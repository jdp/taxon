import hashlib
try:
    import cPickle as pickle
except:
    import pickle

from functools import partial
from itertools import imap

from .backend import Backend
from ..query import Query


class RedisBackend(Backend):
    def __init__(self, redis, name):
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
        return pickle.dumps(data)

    def decode(self, data):
        return pickle.loads(data)

    def tag_items(self, tag, *items):
        items = list(set(self.encode(item) for item in items) - self._r.smembers(self.tag_key(tag)))
        if len(items) == 0:
            return []
        with self._r.pipeline() as pipe:
            pipe.zincrby(self.tags_key, tag, len(items))
            pipe.sadd(self.tag_key(tag), *items)
            for item in items:
                pipe.zincrby(self.items_key, item, 1)
            pipe.execute()
        return map(self.decode, items)

    def untag_items(self, tag, *items):
        items = list(set(self.encode(item) for item in items) & self._r.smembers(self.tag_key(tag)))
        if len(items) == 0:
            return []
        with self._r.pipeline() as pipe:
            pipe.zincrby(self.tags_key, tag, -len(items))
            pipe.srem(self.tag_key(tag), *items)
            for item in items:
                pipe.zincrby(self.items_key, item, -1)
            pipe.execute()
        self._clear_cache()
        return map(self.decode, items)

    def remove_items(self, *items):
        removed = []
        if not len(items):
            return removed
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
            removed.append(self.decode(item))
        self._clear_cache()
        return removed

    def all_tags(self):
        return list(self._r.zrangebyscore(self.tags_key, 1, '+inf'))

    def all_items(self):
        return map(self.decode, self._r.zrangebyscore(self.items_key, 1, '+inf'))

    def query(self, q):
        if isinstance(q, Query):
            fn, args = q.freeze()
            return self._raw_query(fn, args)
        elif isinstance(q, tuple):
            fn, args = q
            return self._raw_query(fn, args)
        else:
            raise TypeError("%s is not a recognized Taxon query" % q)

    def _raw_query(self, fn, args):
        "Perform a raw query on the Taxon instance"
        h = hashlib.sha1(pickle.dumps((fn, args)))
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
            interkeys = [key for key, _ in [self._raw_query(*a) for a in args]]
            self._r.sinterstore(keyname, *interkeys)
            self._r.sadd(self.cache_key, keyname)
            return (keyname, map(self.decode, self._r.smembers(keyname)))
        elif fn == 'or':
            interkeys = [key for key, _ in [self._raw_query(*a) for a in args]]
            self._r.sunionstore(keyname, *interkeys)
            self._r.sadd(self.cache_key, keyname)
            return (keyname, map(self.decode, self._r.smembers(keyname)))
        elif fn == 'not':
            interkeys = [key for key, _ in [self._raw_query(*a) for a in args]]
            tags = self.all_tags()
            scratchpad_key = self.result_key('_')
            self._r.sunionstore(scratchpad_key, *map(self.tag_key, tags))
            self._r.sdiffstore(keyname, scratchpad_key, *interkeys)
            self._r.sadd(self.cache_key, keyname)
            return (keyname, map(self.decode, self._r.smembers(keyname)))
        else:
            raise ValueError("Unkown Taxon operator '%s'" % fn)

    def _clear_cache(self):
        cached_keys = self._r.smembers(self.cache_key)
        if len(cached_keys) > 0:
            self._r.delete(*cached_keys)
        return True

    def empty(self):
        self._r.flushdb()

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"%s(%r, %r)" % (self.__class__.__name__, self.redis, self.name)
