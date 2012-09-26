import hashlib
import operator
from collections import Counter
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

    def empty(self):
        raise NotImplementedError


class MemoryBackend(Backend):
    def __init__(self):
        self.empty()

    def tag_items(self, tag, *items):
        if tag not in self.tags:
            self.tags[tag] = 0
            self.tagged[tag] = set()
        new_items = set(items) - self.tagged[tag]
        if len(new_items) == 0:
            raise RuntimeError
        self.tags[tag] += len(new_items)
        self.tagged[tag].update(set(new_items))
        self.items += Counter(new_items)
        return new_items

    def untag_items(self, tag, *items):
        old_items = set(items) & self.tagged[tag]
        if len(old_items) == 0:
            raise RuntimeError
        self.tags[tag] -= len(old_items)
        self.tagged[tag] -= set(old_items)
        self.items -= Counter(old_items)
        return old_items

    def remove_items(self, *items):
        removed = []
        for item in set(items):
            if item not in self.items:
                continue
            for tag in self.all_tags():
                if item not in self.tagged[tag]:
                    continue
                self.tagged[tag] -= set([item])
                self.tags[tag] -= 1
                self.items[item] -= 1
            removed.append(item)
        return removed

    def all_tags(self):
        return [tag[0] for tag in self.tags.items() if tag[1] > 0]

    def all_items(self):
        return [item[0] for item in self.items.items() if item[1] > 0]

    def query(self, q):
        if isinstance(q, Query):
            return self._raw_query(*q.freeze().items()[0])
        elif isinstance(q, dict):
            return self._raw_query(*q.items()[0])
        else:
            raise RuntimeError

    def _raw_query(self, fn, args):
        if fn == 'tag':
            if len(args) == 1:
                return None, self.tagged.get(args[0], [])
            else:
                groups = [self.tagged.get(tag, []) for tag in args]
                return None, reduce(operator.add, groups)
        elif fn == 'and':
            results = [set(items) for _, items in [self._raw_query(*a.items()[0]) for a in args]]
            return None, reduce(operator.__and__, results)
        elif fn == 'or':
            results = [set(items) for _, items in [self._raw_query(*a.items()[0]) for a in args]]
            return None, reduce(operator.__or__, results)
        elif fn == 'not':
            results = [set(items) for _, items in [self._raw_query(*a.items()[0]) for a in args]]
            results.insert(0, set(self.all_items()))
            return None, reduce(operator.sub, results)
        else:
            raise ValueError

    def empty(self):
        self.tagged = dict()
        self.items = Counter()
        self.tags = Counter()


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
        removed = []
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

    def empty(self):
        self._r.flushdb()
