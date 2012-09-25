from redis import Redis
from nose.tools import with_setup, raises, eq_, ok_
from .context import taxon
from taxon.backends import RedisBackend
from taxon.query import *

t = None
db = 9


def setup():
    global t, db
    t = taxon.Taxon(RedisBackend(Redis(db=db)))
    if t._backend.redis.dbsize() > 0:
        raise RuntimeError("Redis DB %d is not empty" % db)


def teardown():
    global t
    t._backend.redis.flushdb()


@with_setup(teardown=teardown)
def simple_add_test():
    t.tag('foo', 'a')
    t.tag('bar', 'b')
    t.tag('bar', 'c')
    eq_(set(t.tags()), set(['foo', 'bar']))
    eq_(set(t.items()), set(['a', 'b', 'c']))


@with_setup(teardown=teardown)
def complex_add_test():
    t.tag('foo', 'a')
    t.tag('bar', 'b', 'c')
    eq_(set(t.tags()), set(['foo', 'bar']))
    eq_(set(t.items()), set(['a', 'b', 'c']))


@with_setup(teardown=teardown)
def tag_query_test():
    t.tag('foo', 'a', 'b', 'c')
    _, items = t.query(Tag("foo"))
    eq_(set(items), set(['a', 'b', 'c']))


@with_setup(teardown=teardown)
def simple_remove_test():
    t.tag('foo', 'a')
    t.tag('bar', 'b', 'c')
    eq_(set(t.tags()), set(['foo', 'bar']))
    eq_(set(t.items()), set(['a', 'b', 'c']))
    t.untag('bar', 'b')
    eq_(set(t.tags()), set(['foo', 'bar']))
    _, items = t.query(Tag('bar'))
    eq_(set(items), set(['c']))
    t.untag('bar', 'c')
    eq_(set(t.tags()), set(['foo']))
    _, items = t.query(Tag('bar'))
    eq_(set(items), set([]))


@with_setup(teardown=teardown)
def remove_item_test():
    t.tag('foo', 'a')
    t.tag('bar', 'a')
    t.tag('baz', 'a')
    eq_(len(t.tags()), 3)
    eq_(len(t.items()), 1)
    eq_(t.remove('a'), 1)
    eq_(len(t.tags()), 0)
    eq_(len(t.items()), 0)


@with_setup(teardown=teardown)
def find_test():
    t.tag('foo', 'a', 'b')
    results = t.find(Tag('foo'))
    eq_(results, set(['a', 'b']))


@with_setup(teardown=teardown)
def and_query_test():
    t.tag('foo', 'a', 'b')
    t.tag('bar', 'a', 'c')
    _, items = t.query(And('foo', 'bar'))
    eq_(set(items), set(['a']))


@with_setup(teardown=teardown)
def or_query_test():
    t.tag('foo', 'a', 'b')
    t.tag('bar', 'a', 'c')
    _, items = t.query(Or('foo', 'bar'))
    eq_(set(items), set(['a', 'b', 'c']))


@with_setup(teardown=teardown)
def not_query_test():
    t.tag('foo', 'a', 'b')
    t.tag('bar', 'a', 'c')
    _, items = t.query(Not('foo'))
    eq_(set(items), set(['c']))


@raises(TypeError)
def invalid_type_in_query_test():
    t.query(Tag("foo") & 5)


@with_setup(teardown=teardown)
def encoding_test():
    import json

    class JsonRedisBackend(RedisBackend):
        def encode(self, data):
            return json.dumps(data)

        def decode(self, data):
            return json.loads(data)

    t = taxon.Taxon(JsonRedisBackend(Redis(db=db), 'jtxn'))
    t.tag('foo', {'foo': 'bar'})
    _, items = t.query(Tag('foo'))
    eq_(len(items), 1)
    ok_(isinstance(items[0], dict))
