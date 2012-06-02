from redis import Redis
from nose.tools import with_setup, raises, eq_
from .context import taxon
from taxon.query import *

t = None


def setup():
    global t
    db = 9
    t = taxon.Taxon(Redis(db=db))
    if t.dbsize() > 0:
        raise RuntimeError("Redis DB %d is not empty" % db)


def teardown():
    global t
    t.flushdb()


@with_setup(teardown=teardown)
def simple_add_test():
    t.tag('foo', 'a')
    t.tag('bar', ['b', 'c'])
    eq_(t.tags(), set(['foo', 'bar']))
    eq_(t.items(), set(['a', 'b', 'c']))


@with_setup(teardown=teardown)
def tag_query_test():
    t.tag('foo', ['a', 'b', 'c'])
    _, items = t.query(Tag("foo"))
    eq_(items, set(['a', 'b', 'c']))


@with_setup(teardown=teardown)
def and_query_test():
    t.tag('foo', ['a', 'b'])
    t.tag('bar', ['a', 'c'])
    _, items = t.query(And('foo', 'bar'))
    eq_(items, set(['a']))


@with_setup(teardown=teardown)
def or_query_test():
    t.tag('foo', ['a', 'b'])
    t.tag('bar', ['a', 'c'])
    _, items = t.query(Or('foo', 'bar'))
    eq_(items, set(['a', 'b', 'c']))


@with_setup(teardown=teardown)
def not_query_test():
    t.tag('foo', ['a', 'b'])
    t.tag('bar', ['a', 'c'])
    _, items = t.query(Not('foo'))
    eq_(items, set(['c']))


@raises(TypeError)
def invalid_type_in_query_test():
    t.query(Tag("foo") & 5)
