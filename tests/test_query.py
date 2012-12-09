from functools import partial
from os.path import dirname
from nose.tools import raises, eq_, ok_
from .context import taxon, benchmark
from taxon import MemoryTaxon, RedisTaxon
from taxon.query import *

TestRedisTaxon = partial(RedisTaxon, 'redis://localhost:6379/9', 'test')


class _TestBackend(object):
    def __init__(self, taxon_cls):
        self.taxon_cls = taxon_cls

    def setup(self):
        self.t = self.taxon_cls()
        for line in open(dirname(__file__) + '/fixtures/pokemon_types.csv'):
            line = line.strip()
            if not line:
                continue
            tokens = line.split()
            pokemon, types = tokens[0], tokens[1:]
            for t in types:
                self.t.tag(t, pokemon)

    def teardown(self):
        self.t.empty()

    def test_all_tags(self):
        tags = self.t.tags()
        ok_(len(tags) > 0)
        eq_(len(tags), 17)

    def test_all_items(self):
        items = self.t.items()
        ok_(len(items) > 0)
        eq_(len(items), 649)

    def test_find_tag(self):
        # Find all water-type pokemon
        water = self.t.find(Tag('water'))
        ok_(len(water) > 0)
        eq_(len(water), 111)

    def test_find_and(self):
        # Find all grass/poison dual types
        results = self.t.find(And('grass', 'poison'))
        ok_(len(results) > 0)
        eq_(len(results), 14)

    def test_find_or(self):
        # Find all that are either grass or poison (or both)
        results = self.t.find(Or('grass', 'poison'))
        ok_(len(results) > 0)
        eq_(len(results), 119)

    def test_find_not(self):
        # Find all that are not fire-type
        results = self.t.find(Not('fire'))
        ok_(len(results) > 0)
        eq_(len(results), 599)

    def test_find_complex(self):
        # Find all that are flying that are also fire or water type
        results = self.t.find(And('flying', Or('fire', 'water')))
        ok_(len(results) > 0)
        eq_(len(results), 11)

    def test_find_all(self):
        tags = self.t.tags()
        # Find all items by providing every tag
        results = self.t.find(Or(*tags))
        eq_(len(results), len(self.t.items()))
        eq_(set(results), set(self.t.items()))
        # Find all items through union of all tags
        results = self.t.find(reduce(Or, tags))
        eq_(len(results), len(self.t.items()))
        eq_(set(results), set(self.t.items()))

    @raises(TypeError)
    def test_find_invalid(self):
        self.t.find(Tag('water') & 5)


class TestMemoryBackend(_TestBackend):
    def __init__(self):
        super(TestMemoryBackend, self).__init__(MemoryTaxon)


class TestRedisBackend(_TestBackend):
    def __init__(self):
        super(TestRedisBackend, self).__init__(TestRedisTaxon)

    def setup(self):
        t = self.taxon_cls()
        if t.backend.redis.dbsize() > 0:
            raise RuntimeError("Redis database is not empty")
        super(TestRedisBackend, self).setup()

    def teardown(self):
        super(TestRedisBackend, self).teardown()
        self.t.backend.redis.flushdb()
