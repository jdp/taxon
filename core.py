import hashlib
from collections import namedtuple
import redis
import query


def _tag_keys(tags):
    return [("txn:tag:%s" % tag) for tag in tags]


QueryResult = namedtuple('QueryResult', ('key', 'items'))


class Store(object):
    items_key = "txn:items"
    tags_key = "txn:tags"

    def __init__(self, r):
        self.r = r

    def put(self, tag, items):
        "Store `items` in Taxon tagged with with `tag`."
        try:
            it = iter(items)
        except TypeError:
            items = [items]
        pipe = self.r.pipeline()
        pipe.sadd(self.tags_key, tag)
        pipe.sadd(self.items_key, *items)
        pipe.sadd(_tag_keys([tag])[0], *items)
        pipe.execute()

    def raw_query(self, fn, args):
        "Perform a raw query on the Taxon store."

        h = hashlib.sha1(fn)
        for arg in args:
            h.update(str(arg))
        keyname = "txn:result:%s" % h.hexdigest()

        if fn == "tag":
            if len(args) == 1:
                key = _tag_keys(args)[0]
                items = self.r.smembers(key)
                return QueryResult(key, items)
            else:
                keys = _tag_keys(args)
                self.r.sunionstore(keyname, *keys)
                return QueryResult(keyname, self.r.smembers(keyname))
        elif fn == "and":
            items = [qr.key for qr in [self.raw_query(*a.popitem()) for a in args]]
            self.r.sinterstore(keyname, *items)
            return  QueryResult(keyname, self.r.smembers(keyname))
        elif fn == "or":
            items = [qr.key for qr in [self.raw_query(*a.popitem()) for a in args]]
            self.r.sunionstore(keyname, *items)
            return QueryResult(keyname, self.r.smembers(keyname))
        elif fn == "not":
            items = [qr.key for qr in [self.raw_query(*a.popitem()) for a in args]]
            self.r.sdiffstore(keyname, self.items_key, *items)
            return QueryResult(keyname, self.r.smembers(keyname))
        else:
            raise SyntaxError("Unkown Taxon fn `%s'" % fn)

    def query(self, q):
        "Perform a query on the Taxon store."
        if isinstance(q, query.Query):
            return self.raw_query(*q.freeze().popitem())
        elif isinstance(q, dict):
            return self.raw_query(*q.popitem())
        else:
            raise TypeError("%s is not a recognized Taxon query" % q)

if __name__ == '__main__':
    from query import *
    r = redis.Redis(db=9)
    s = Store(r)
    s.put('foo', ['a', 'b'])
    s.put('bar', ['c', 'a'])
    s.put('baz', 'a')
    print s.query(Tag("foo") & ~Tag("baz")).items
    print s.query(Or("foo", "bar")).items
    print s.query({'or': [{'tag': ['foo']}, {'tag': ['bar']}]}).items
