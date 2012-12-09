from functools import partial
from nose.tools import raises, eq_, ok_
from .context import taxon, benchmark
from taxon import MemoryTaxon, RedisTaxon
from taxon.query import *

TestRedisTaxon = partial(RedisTaxon, 'redis://localhost:6379/9', 'test')


class _TestBasics(object):
    def __init__(self, taxon_cls):
        self.taxon_cls = taxon_cls

    def setup(self):
        self.t = self.taxon_cls()

    def teardown(self):
        self.t.empty()

    def test_one_item_tag(self):
        tagged = self.t.tag('foo', 'a')
        eq_(tagged, ['a'])

    def test_many_item_tag(self):
        tagged = self.t.tag('foo', 'a', 'b', 'c')
        eq_(set(tagged), set(['a', 'b', 'c']))

    def test_existing_tag(self):
        tagged = self.t.tag('bar', 'x')
        eq_(tagged, ['x'])
        tagged = self.t.tag('bar', 'x', 'y')
        eq_(tagged, ['y'])
        tagged = self.t.tag('bar', 'x')
        eq_(tagged, [])

    def test_all_tags(self):
        self.t.tag('foo', 'x', 'y')
        self.t.tag('bar', 'y', 'z')
        eq_(set(self.t.tags()), set(['foo', 'bar']))

    def test_all_items(self):
        self.t.tag('foo', 'x', 'y')
        self.t.tag('bar', 'y', 'z')
        eq_(set(self.t.items()), set(['x', 'y', 'z']))

    def test_remove_tag(self):
        self.t.tag('bar', 'x', 'y')
        untagged = self.t.untag('bar', 'x')
        eq_(untagged, ['x'])
        untagged = self.t.untag('bar', 'x')
        eq_(untagged, [])

    def test_remove_item(self):
        self.t.tag('bar', 'x', 'y')
        self.t.tag('foo', 'x', 'z')
        removed = self.t.remove('x')
        eq_(removed, ['x'])
        removed = self.t.remove('y')
        eq_(removed, ['y'])
        removed = self.t.remove('w')
        eq_(removed, [])

    def test_item_tag_sync(self):
        self.t.tag('bar', 'x', 'y')
        self.t.tag('foo', 'x', 'z')
        removed = self.t.remove('x')
        eq_(removed, ['x'])
        removed = self.t.remove('y')
        eq_(removed, ['y'])
        removed = self.t.remove('w')
        eq_(removed, [])
        eq_(self.t.tags(), ['foo'])
        eq_(self.t.items(), ['z'])


class TestMemoryBasics(_TestBasics):
    def __init__(self):
        super(TestMemoryBasics, self).__init__(MemoryTaxon)


class TestRedisBasics(_TestBasics):
    def __init__(self):
        super(TestRedisBasics, self).__init__(TestRedisTaxon)

    def setup(self):
        super(TestRedisBasics, self).setup()
        if self.t.backend.redis.dbsize() > 0:
            raise RuntimeError("Redis database is not empty")

    def teardown(self):
        super(TestRedisBasics, self).teardown()
        self.t.backend.redis.flushdb()
