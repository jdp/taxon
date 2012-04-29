import hashlib
from functools import partial
from .query import Query, sexpr


class Taxon(object):
    """
    A wrapper for Redis objects that allows data to be organized and queried
    by tag.
    """

    def __init__(self, r, key_prefix='txn'):
        self.r = r
        self.key_prefix = key_prefix
        self.tag_key = partial(self._make_key, 'tag')
        self.result_key = partial(self._make_key, 'result')
        self.items_key = self._make_key('items')
        self.tags_key = self._make_key('tags')
        self.cache_key = self._make_key('cache')

    def _make_key(self, *args):
        return ':'.join([self.key_prefix] + list(args))

    def tag(self, tag, items):
        "Store ``items`` in Redis tagged with ``tag``"
        try:
            _ = iter(items)
        except TypeError:
            items = [items]
        pipe = self.r.pipeline()
        pipe.sadd(self.tags_key, tag)
        pipe.sadd(self.items_key, *items)
        pipe.sadd(self.tag_key(tag), *items)
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
            return (keyname, self.r.smembers(keyname))

        if fn == 'tag':
            if len(args) == 1:
                key = self.tag_key(args[0])
                return (key, self.r.smembers(key))
            else:
                keys = [self.tag_key(k) for k in args]
                self.r.sunionstore(keyname, *keys)
                self.r.sadd(self.cache_key, keyname)
                return (keyname, self.r.smembers(keyname))
        elif fn == 'and':
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            self.r.sinterstore(keyname, *interkeys)
            self.r.sadd(self.cache_key, keyname)
            return (keyname, self.r.smembers(keyname))
        elif fn == 'or':
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            self.r.sunionstore(keyname, *interkeys)
            self.r.sadd(self.cache_key, keyname)
            return (keyname, self.r.smembers(keyname))
        elif fn == 'not':
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            self.r.sdiffstore(keyname, self.items_key, *interkeys)
            self.r.sadd(self.cache_key, keyname)
            return (keyname, self.r.smembers(keyname))
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
        return self.r.smembers(self.tags_key)

    def items(self):
        "Return the set of all tagged items known to the instance"
        return self.r.smembers(self.items_key)

    def __getattr__(self, name):
        return getattr(self.r, name)
