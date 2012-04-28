from redis import Redis
from nose.tools import with_setup, eq_
from .context import taxon
from taxon.query import *

t = None


def setup():
    global t
    t = taxon.Store(Redis(db=9))


def teardown():
    global t
    t.r.flushdb()


@with_setup(teardown=teardown)
def simple_add_test():
    t.put('foo', 'a')
    t.put('bar', ['b', 'c'])
    eq_(t.tags(), set(['foo', 'bar']))
    eq_(t.items(), set(['a', 'b', 'c']))


@with_setup(teardown=teardown)
def tag_query_test():
    t.put('foo', ['a', 'b', 'c'])
    _, items = t.query(Tag("foo"))
    eq_(items, set(['a', 'b', 'c']))


@with_setup(teardown=teardown)
def and_query_test():
    t.put('foo', ['a', 'b'])
    t.put('bar', ['a', 'c'])
    _, items = t.query(And('foo', 'bar'))
    eq_(items, set(['a']))


@with_setup(teardown=teardown)
def or_query_test():
    t.put('foo', ['a', 'b'])
    t.put('bar', ['a', 'c'])
    _, items = t.query(Or('foo', 'bar'))
    eq_(items, set(['a', 'b', 'c']))


@with_setup(teardown=teardown)
def not_query_test():
    t.put('foo', ['a', 'b'])
    t.put('bar', ['a', 'c'])
    _, items = t.query(Not('foo'))
    eq_(items, set(['c']))