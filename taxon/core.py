import hashlib
from functools import partial
from .query import Query, sexpr


class Taxon(object):
    """
    A wrapper for Redis objects that allows data to be organized and queried
    by tag.
    """

    def __init__(self, r, key_prefix='txn', encode=str, decode=str):
        self.r = r
        make_key = partial(lambda *parts: ':'.join(parts), key_prefix)
        self.tag_key = partial(make_key, 'tag')
        self.result_key = partial(make_key, 'result')
        self.items_key = make_key('items')
        self.tags_key = make_key('tags')
        self.cache_key = make_key('cache')
        self._encode = encode
        self._decode = decode

    def tag(self, tag, items):
        "Store ``items`` in Redis tagged with ``tag``"
        try:
            _ = iter(items)
        except TypeError:
            items = [items]
        with self.r.pipeline() as pipe:
            pipe.sadd(self.tags_key, tag)
            pipe.sadd(self.items_key, *map(self._encode, items))
            pipe.sadd(self.tag_key(tag), *map(self._encode, items))
            pipe.execute()
        cached_keys = self.r.smembers(self.cache_key)
        if len(cached_keys) > 0:
            self.r.delete(*cached_keys)
        return True

    def _raw_query(self, fn, args):
        "Perform a raw query on the Taxon instance"
        h = hashlib.sha1(sexpr({fn: args[:]}))
        keyname = self.result_key(h.hexdigest())
        if self.r.exists(keyname):
            return (keyname, map(self._decode, self.r.smembers(keyname)))

        if fn == 'tag':
            if len(args) == 1:
                key = self.tag_key(args[0])
                return (key, map(self._decode, self.r.smembers(key)))
            else:
                keys = [self.tag_key(k) for k in args]
                self.r.sunionstore(keyname, *keys)
                self.r.sadd(self.cache_key, keyname)
                return (keyname, map(self._decode, self.r.smembers(keyname)))
        elif fn == 'and':
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            self.r.sinterstore(keyname, *interkeys)
            self.r.sadd(self.cache_key, keyname)
            return (keyname, map(self._decode, self.r.smembers(keyname)))
        elif fn == 'or':
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            self.r.sunionstore(keyname, *interkeys)
            self.r.sadd(self.cache_key, keyname)
            return (keyname, map(self._decode, self.r.smembers(keyname)))
        elif fn == 'not':
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            self.r.sdiffstore(keyname, self.items_key, *interkeys)
            self.r.sadd(self.cache_key, keyname)
            return (keyname, map(self._decode, self.r.smembers(keyname)))
        else:
            raise SyntaxError("Unkown Taxon operator '%s'" % fn)

    def query(self, q):
        "Perform a query on the Taxon instance"
        if isinstance(q, Query):
            return self._raw_query(*q.freeze().items()[0])
        elif isinstance(q, dict):
            return self._raw_query(*q.items()[0])
        else:
            raise TypeError("%s is not a recognized Taxon query" % q)

    def tags(self):
        "Return the set of all tags known to the instance"
        return list(self.r.smembers(self.tags_key))

    def items(self):
        "Return the set of all tagged items known to the instance"
        return map(self._decode, self.r.smembers(self.items_key))

    def __getattr__(self, name):
        return getattr(self.r, name)
