import hashlib
from functools import partial
from itertools import imap
from .query import Query, sexpr


class Backend(object):
    def __init__(self):
        pass

    def tag_items(self, tag, *items):
        raise NotImplementedError

    def untag_items(self, tag, *items):
        raise NotImplementedError

    def remove_items(self, *items):
        raise NotImplementedError

    def all_tags(self):
        raise NotImplementedError

    def all_items(self):
        raise NotImplementedError

    def query(self, q):
        raise NotImplementedError


class RedisBackend(Backend):
    def __init__(self, redis, name='txn'):
        self._r = redis
        self._name = name
        make_key = partial(lambda *parts: ':'.join(parts), self._name)
        self.tag_key = partial(make_key, 'tag')
        self.result_key = partial(make_key, 'result')
        self.items_key = make_key('items')
        self.tags_key = make_key('tags')
        self.cache_key = make_key('cache')

    @property
    def redis(self):
        return self._r

    @property
    def name(self):
        return self._name

    def encode(self, data):
        return str(data)

    def decode(self, data):
        return str(data)

    def tag_items(self, tag, *items):
        items = list(set(self.encode(item) for item in items) - self._r.smembers(self.tag_key(tag)))
        if len(items) == 0:
            raise ValueError("either no items provided or all exist in tag")
        with self._r.pipeline() as pipe:
            pipe.zincrby(self.tags_key, tag, len(items))
            pipe.sadd(self.tag_key(tag), *items)
            for item in items:
                pipe.zincrby(self.items_key, item, 1)
            pipe.execute()
        return items

    def untag_items(self, tag, *items):
        items = list(set(self.encode(item) for item in items) & self._r.smembers(self.tag_key(tag)))
        if len(items) == 0:
            raise ValueError("either no items provided or none exist in tag")
        with self._r.pipeline() as pipe:
            pipe.zincrby(self.tags_key, tag, -len(items))
            pipe.srem(self.tag_key(tag), *items)
            for item in items:
                pipe.zincrby(self.items_key, item, -1)
            pipe.execute()
        self._clear_cache()
        return items

    def remove_items(self, *items):
        if not len(items):
            return ValueError("must remove at least 1 item")
        removed = 0
        for item in imap(self.encode, items):
            score = self._r.zscore(self.items_key, item)
            if not score:
                continue
            for tag in self.all_tags():
                srem_ok = self._r.srem(self.tag_key(tag), item)
                if not srem_ok:
                    continue
                with self._r.pipeline() as pipe:
                    pipe.zincrby(self.tags_key, tag, -1)
                    pipe.zincrby(self.items_key, item, -1)
                    pipe.execute()
            removed += 1
        self._clear_cache()
        return removed

    def all_tags(self):
        return list(self._r.zrangebyscore(self.tags_key, 1, '+inf'))

    def all_items(self):
        return map(self.decode, self._r.zrangebyscore(self.items_key, 1, '+inf'))

    def query(self, q):
        if isinstance(q, Query):
            return self._raw_query(*q.freeze().items()[0])
        elif isinstance(q, dict):
            return self._raw_query(*q.items()[0])
        else:
            raise TypeError("%s is not a recognized Taxon query" % q)

    def _raw_query(self, fn, args):
        "Perform a raw query on the Taxon instance"
        h = hashlib.sha1(sexpr({fn: args[:]}))
        keyname = self.result_key(h.hexdigest())
        if self._r.exists(keyname):
            return (keyname, map(self.decode, self._r.smembers(keyname)))

        if fn == 'tag':
            if len(args) == 1:
                key = self.tag_key(args[0])
                return (key, map(self.decode, self._r.smembers(key)))
            else:
                keys = [self.tag_key(k) for k in args]
                self._r.sunionstore(keyname, *keys)
                self._r.sadd(self.cache_key, keyname)
                return (keyname, map(self.decode, self._r.smembers(keyname)))
        elif fn == 'and':
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            self._r.sinterstore(keyname, *interkeys)
            self._r.sadd(self.cache_key, keyname)
            return (keyname, map(self.decode, self._r.smembers(keyname)))
        elif fn == 'or':
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            self._r.sunionstore(keyname, *interkeys)
            self._r.sadd(self.cache_key, keyname)
            return (keyname, map(self.decode, self._r.smembers(keyname)))
        elif fn == 'not':
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            tags = self.all_tags()
            scratchpad_key = self.result_key('_')
            self._r.sunionstore(scratchpad_key, *map(self.tag_key, tags))
            self._r.sdiffstore(keyname, scratchpad_key, *interkeys)
            self._r.sadd(self.cache_key, keyname)
            return (keyname, map(self.decode, self._r.smembers(keyname)))
        else:
            raise SyntaxError("Unkown Taxon operator '%s'" % fn)

    def _clear_cache(self):
        cached_keys = self._r.smembers(self.cache_key)
        if len(cached_keys) > 0:
            self._r.delete(*cached_keys)
        return True
