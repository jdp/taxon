from functools import partial
from redis import Redis
from nose.tools import raises, eq_, ok_
from .context import taxon
from taxon.backends import MemoryBackend, RedisBackend
from taxon.query import *

redis_inst = Redis(db=9)
TestRedisBackend = partial(RedisBackend, redis_inst)


def setup():
    global redis_inst
    if redis_inst.dbsize() > 0:
        raise RuntimeError("Redis DB is not empty")


def teardown():
    global redis_inst
    redis_inst.flushdb()


def simple_add_test():
    def func(t):
        t.tag('foo', 'a')
        t.tag('bar', 'b')
        t.tag('bar', 'c')
        eq_(set(t.tags()), set(['foo', 'bar']))
        eq_(set(t.items()), set(['a', 'b', 'c']))
        t.empty()

    for backend in [MemoryBackend, TestRedisBackend]:
        yield func, taxon.Taxon(backend())


def complex_add_test():
    def func(t):
        t.tag('foo', 'a')
        t.tag('bar', 'b', 'c')
        eq_(set(t.tags()), set(['foo', 'bar']))
        eq_(set(t.items()), set(['a', 'b', 'c']))
        t.empty()

    for backend in [MemoryBackend, TestRedisBackend]:
        yield func, taxon.Taxon(backend())


def tag_query_test():
    def func(t):
        t.tag('foo', 'a', 'b', 'c')
        _, items = t.query(Tag("foo"))
        eq_(set(items), set(['a', 'b', 'c']))
        t.empty()

    for backend in [MemoryBackend, TestRedisBackend]:
        yield func, taxon.Taxon(backend())


def simple_remove_test():
    def func(t):
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
        t.empty()

    for backend in [MemoryBackend, TestRedisBackend]:
        yield func, taxon.Taxon(backend())


def remove_item_test():
    def func(t):
        t.tag('foo', 'a')
        t.tag('bar', 'a')
        t.tag('baz', 'a')
        eq_(len(t.tags()), 3)
        eq_(len(t.items()), 1)
        eq_(set(t.remove('a')), set(['a']))
        eq_(len(t.tags()), 0)
        eq_(len(t.items()), 0)
        t.empty()

    for backend in [MemoryBackend, TestRedisBackend]:
        yield func, taxon.Taxon(backend())


def find_test():
    def func(t):
        t.tag('foo', 'a', 'b')
        results = t.find(Tag('foo'))
        eq_(results, set(['a', 'b']))
        t.empty()

    for backend in [MemoryBackend, TestRedisBackend]:
        yield func, taxon.Taxon(backend())


def and_query_test():
    def func(t):
        t.tag('foo', 'a', 'b')
        t.tag('bar', 'a', 'c')
        _, items = t.query(And('foo', 'bar'))
        eq_(set(items), set(['a']))
        t.empty()

    for backend in [MemoryBackend, TestRedisBackend]:
        yield func, taxon.Taxon(backend())


def or_query_test():
    def func(t):
        t.tag('foo', 'a', 'b')
        t.tag('bar', 'a', 'c')
        _, items = t.query(Or('foo', 'bar'))
        eq_(set(items), set(['a', 'b', 'c']))
        t.empty()

    for backend in [MemoryBackend, TestRedisBackend]:
        yield func, taxon.Taxon(backend())


def not_query_test():
    def func(t):
        t.tag('foo', 'a', 'b')
        t.tag('bar', 'a', 'c')
        _, items = t.query(Not('foo'))
        eq_(set(items), set(['c']))
        t.empty()

    for backend in [MemoryBackend, TestRedisBackend]:
        yield func, taxon.Taxon(backend())


def invalid_type_in_query_test():
    @raises(TypeError)
    def func(t):
        t.query(Tag("foo") & 5)

    for backend in [MemoryBackend, TestRedisBackend]:
        yield func, taxon.Taxon(backend())


def encoding_test():
    import json

    class JsonRedisBackend(RedisBackend):
        def encode(self, data):
            return json.dumps(data)

        def decode(self, data):
            return json.loads(data)

    t = taxon.Taxon(JsonRedisBackend(redis_inst, 'jtxn'))
    t.tag('foo', {'foo': 'bar'})
    _, items = t.query(Tag('foo'))
    eq_(len(items), 1)
    ok_(isinstance(items[0], dict))
    t.empty()
