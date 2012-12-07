from urlparse import urlparse

from .backends import Backend, MemoryBackend, RedisBackend
from .query import Query


class Taxon(object):
    """
    A wrapper for Redis objects that allows data to be organized and queried
    by tag.
    """

    def __init__(self, backend):
        if not isinstance(backend, Backend):
            raise ValueError("%s is not a valid backend" % backend)
        self._backend = backend

    @property
    def backend(self):
        return self._backend

    def tag(self, tag, *items):
        "Add tag to items"
        return self._backend.tag_items(tag, *items)

    def untag(self, tag, *items):
        "Remove tag from items"
        return self._backend.untag_items(tag, *items)

    def remove(self, *items):
        "Remove items"
        return self._backend.remove_items(*items)

    def tags(self):
        "Return the collection of all known tags"
        return self._backend.all_tags()

    def items(self):
        "Return the collection of all known items"
        return self._backend.all_items()

    def query(self, q):
        "Perform a query and return the results and metadata"
        if not isinstance(q, (tuple, Query)):
            raise ValueError("%s is not a valid query" % q)
        return self._backend.query(q)

    def find(self, q):
        _, items = self.query(q)
        return set(items)

    def empty(self):
        return self._backend.empty()


class MemoryTaxon(Taxon):
    def __init__(self):
        super(MemoryTaxon, self).__init__(MemoryBackend())


class RedisTaxon(Taxon):
    def __init__(self, dsn='redis://localhost', name='txn'):
        r = self._redis_from_dsn(dsn)
        super(RedisTaxon, self).__init__(RedisBackend(r, name))

    def _redis_from_dsn(self, dsn):
        import redis
        parts = urlparse(dsn)
        _, _, netloc = parts.netloc.partition('@')
        netloc = netloc.split(':')
        host = netloc[0]
        try:
            port = int(netloc[1])
        except IndexError:
            port = 6379
        try:
            db = int(parts.path.strip('/'))
        except ValueError:
            db = 0
        return redis.Redis(host=host, port=port, db=db)
