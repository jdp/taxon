from functools import partial
from nose.tools import raises, eq_, ok_
from .context import taxon
from taxon import MemoryTaxon, RedisTaxon
from taxon.query import *

TestRedisTaxon = partial(RedisTaxon, 'redis://localhost:6379/9', 'test')


def setup():
    t = TestRedisTaxon()
    if t.backend.redis.dbsize() > 0:
        raise RuntimeError("Redis DB is not empty")


def teardown():
    t = TestRedisTaxon()
    t.backend.redis.flushdb()


def simple_add_test():
    def func(t):
        t.tag('foo', 'a')
        t.tag('bar', 'b')
        t.tag('bar', 'c')
        eq_(set(t.tags()), set(['foo', 'bar']))
        eq_(set(t.items()), set(['a', 'b', 'c']))
        t.empty()

    for t in [MemoryTaxon, TestRedisTaxon]:
        yield func, t()


def complex_add_test():
    def func(t):
        t.tag('foo', 'a')
        t.tag('bar', 'b', 'c')
        eq_(set(t.tags()), set(['foo', 'bar']))
        eq_(set(t.items()), set(['a', 'b', 'c']))
        t.empty()

    for t in [MemoryTaxon, TestRedisTaxon]:
        yield func, t()


def tag_query_test():
    def func(t):
        t.tag('foo', 'a', 'b', 'c')
        _, items = t.query(Tag("foo"))
        eq_(set(items), set(['a', 'b', 'c']))
        t.empty()

    for t in [MemoryTaxon, TestRedisTaxon]:
        yield func, t()


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

    for t in [MemoryTaxon, TestRedisTaxon]:
        yield func, t()


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

    for t in [MemoryTaxon, TestRedisTaxon]:
        yield func, t()


def find_test():
    def func(t):
        t.tag('foo', 'a', 'b')
        results = t.find(Tag('foo'))
        eq_(results, set(['a', 'b']))
        t.empty()

    for t in [MemoryTaxon, TestRedisTaxon]:
        yield func, t()


def and_query_test():
    def func(t):
        t.tag('foo', 'a', 'b')
        t.tag('bar', 'a', 'c')
        _, items = t.query(And('foo', 'bar'))
        eq_(set(items), set(['a']))
        t.empty()

    for t in [MemoryTaxon, TestRedisTaxon]:
        yield func, t()


def or_query_test():
    def func(t):
        t.tag('foo', 'a', 'b')
        t.tag('bar', 'a', 'c')
        _, items = t.query(Or('foo', 'bar'))
        eq_(set(items), set(['a', 'b', 'c']))
        t.empty()

    for t in [MemoryTaxon, TestRedisTaxon]:
        yield func, t()


def not_query_test():
    def func(t):
        t.tag('foo', 'a', 'b')
        t.tag('bar', 'a', 'c')
        _, items = t.query(Not('foo'))
        eq_(set(items), set(['c']))
        t.empty()

    for t in [MemoryTaxon, TestRedisTaxon]:
        yield func, t()


def invalid_type_in_query_test():
    @raises(TypeError)
    def func(t):
        t.query(Tag("foo") & 5)

    for t in [MemoryTaxon, TestRedisTaxon]:
        yield func, t()

