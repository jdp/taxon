import hashlib
from functools import partial
import redis
import query


class Store(object):
    items_key = "items"
    tags_key = "tags"
    cache_key = "cache"

    def __init__(self, r, key_prefix="txn"):
        self.r = r
        self.key_prefix = key_prefix
        self._tag_key = partial(self._make_key, "tag")
        self._result_key = partial(self._make_key, "result")

    def _make_key(self, *args):
        return ':'.join([self.key_prefix] + list(args))

    def put(self, tag, items):
        "Store `items` in Taxon tagged with with `tag`."

        try:
            _ = iter(items)
        except TypeError:
            items = [items]
        pipe = self.r.pipeline()
        pipe.sadd(self._make_key(self.tags_key), tag)
        pipe.sadd(self._make_key(self.items_key), *items)
        pipe.sadd(self._tag_key(tag), *items)
        pipe.execute()
        cached_keys = self.r.smembers(self._make_key(self.cache_key))
        if len(cached_keys) > 0:
            self.r.delete(*cached_keys)
        return True

    def _raw_query(self, fn, args):
        "Perform a raw query on the Taxon store."

        h = hashlib.sha1(query.sexpr({fn: args[:]}))
        keyname = self._result_key(h.hexdigest())
        if self.r.exists(keyname):
            return (keyname, self.r.smembers(keyname))

        if fn == "tag":
            if len(args) == 1:
                key = self._tag_key(args[0])
                return (key, self.r.smembers(key))
            else:
                keys = [self._tag_key(k) for k in args]
                self.r.sunionstore(keyname, *keys)
                self.r.sadd(self._make_key(self.cache_key), keyname)
                return (keyname, self.r.smembers(keyname))
        elif fn == "and":
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            self.r.sinterstore(keyname, *interkeys)
            self.r.sadd(self._make_key(self.cache_key), keyname)
            return  (keyname, self.r.smembers(keyname))
        elif fn == "or":
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            self.r.sunionstore(keyname, *interkeys)
            self.r.sadd(self._make_key(self.cache_key), keyname)
            return (keyname, self.r.smembers(keyname))
        elif fn == "not":
            interkeys = [key for key, _ in [self._raw_query(*a.items()[0]) for a in args]]
            self.r.sdiffstore(keyname, self._make_key(self.items_key), *interkeys)
            self.r.sadd(self._make_key(self.cache_key), keyname)
            return (keyname, self.r.smembers(keyname))
        else:
            raise SyntaxError("Unkown Taxon fn `%s'" % fn)

    def query(self, q):
        "Perform a query on the Taxon store."

        if isinstance(q, query.Query):
            return self._raw_query(*q.freeze().items()[0])
        elif isinstance(q, dict):
            return self._raw_query(*q.items()[0])
        else:
            raise TypeError("%s is not a recognized Taxon query" % q)

if __name__ == '__main__':
    from query import *

    r = redis.Redis(db=9)
    s = Store(r)
    s.put('foo', ['a', 'b'])
    s.put('bar', ['c', 'a'])
    s.put('baz', 'a')

    _, items = s.query(Tag("foo") & ~Tag("baz"))
    print items
    _, items = s.query(And(Not("baz"), "foo"))
    print items
    _, items = s.query({'and': [{'tag': ['foo']}, {'or': [{'tag': ['fuck']}, {'not': [{'tag': ['baz']}]}]}]})
    print items
