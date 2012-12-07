from urlparse import urlparse

from .backends import Backend, MemoryBackend, RedisBackend
from .query import Query


class Taxon(object):
    """A Taxon instance provides methods to organize and query data by tag.
    """

    def __init__(self, backend):
        """Create a new instance to access the data stored in the backend.

        >>> Taxon(MemoryBackend())
        """
        if not isinstance(backend, Backend):
            raise ValueError("%r is not a valid backend" % backend)
        self._backend = backend

    @property
    def backend(self):
        """Return the the instance of the backend being used."""
        return self._backend

    def tag(self, tag, *items):
        """Add tag ``tag`` to each element in ``items``.

        >>> t = Taxon(MemoryBackend())
        >>> t.tag('closed', 'issue-91', 'issue-105', 'issue-4')
        """
        return self.backend.tag_items(tag, *items)

    def untag(self, tag, *items):
        """Remove tag ``tag`` from each element in ``items``.

        >>> t = Taxon(MemoryBackend())
        >>> t.untag('closed', 'issue-91')
        """
        return self.backend.untag_items(tag, *items)

    def remove(self, *items):
        """Remove each element in ``items`` from the store.

        >>> t = Taxon(MemoryBackend())
        >>> t.tag('functional', 'Haskell', 'Pure', 'ML', 'C')
        >>> t.remove('C')
        """
        return self.backend.remove_items(*items)

    def tags(self):
        """Return a list of all the tags known to the store.

        >>> t = Taxon(MemoryBackend())
        >>> t.tag('water', 'Squirtle')
        >>> t.tag('fire', 'Charmander')
        >>> t.tag('grass', 'Bulbasaur')
        >>> t.tags()
        ['water', 'fire', 'grass']
        """
        return self.backend.all_tags()

    def items(self):
        """Return a list of all the items in the store.

        >>> t = Taxon(MemoryBackend())
        >>> t.tag('water', 'Squirtle')
        >>> t.tag('fire', 'Charmander')
        >>> t.tag('grass', 'Bulbasaur')
        >>> t.items()
        ['Squirtle', 'Charmander', 'Bulbasaur']
        """
        return self.backend.all_items()

    def query(self, q):
        """Perform a query and return the results and metadata.

        The first element of the tuple contains the metadata, which can be any
        value and is specific to the backend being used. The second element is
        a list of the items matching the query.

        >>> t = Taxon(MemoryBackend())
        >>> t.tag('ice', 'Dewgong', 'Articuno')
        >>> t.tag('flying', 'Articuno', 'Pidgeotto')
        >>> t.query(Tag('ice') & Tag('flying'))
        (None, ['Articuno'])
        """
        if not isinstance(q, (tuple, Query)):
            raise ValueError("%r is not a valid query" % q)
        return self.backend.query(q)

    def find(self, q):
        """Return a set of the items matching the query, ignoring metadata.

        >>> t = Taxon(MemoryBackend())
        >>> t.tag('ice', 'Dewgong', 'Articuno')
        >>> t.tag('flying', 'Articuno', 'Pidgeotto')
        >>> t.find(Tag('ice') & Tag('flying'))
        ['Articuno']
        """
        _, items = self.query(q)
        return set(items)

    def empty(self):
        """Remove all tags and items from the store.

        >>> t = Taxon(MemoryBackend())
        >>> t.tag('foo', 'bar')
        >>> t.empty()
        >>> t.tags()
        []
        >>> t.items()
        []
        """
        return self.backend.empty()

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"%s(%r)" % (self.__class__.__name__, self.backend)


class MemoryTaxon(Taxon):
    """A utility class to quickly create a memory-backed Taxon instance."""

    def __init__(self):
        """Create a new Taxon instance with a memory backend."""
        super(MemoryTaxon, self).__init__(MemoryBackend())

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"%s()" % (self.__class__.__name__)


class RedisTaxon(Taxon):
    """A utility class to quickly create a Redis-backed Taxon instance."""

    def __init__(self, dsn='redis://localhost', name='txn'):
        """Create a new Taxon instance with a Redis backend.

        A DSN is used to specify the Redis server to connect to. The path part
        of the DSN can be used to specify which database to select.

        >>> t = RedisTaxon('redis://localhost:6379/10')

        The name of the instance is used as a namespacing mechanism, so that
        multiple Taxon instances can use the same Redis database without
        clobbering each others' data.

        >>> t = RedisTaxon(name='my-other-blog')
        """
        self._dsn = dsn
        r = self._redis_from_dsn(self._dsn)
        super(RedisTaxon, self).__init__(RedisBackend(r, name))

    def _redis_from_dsn(self, dsn):
        """Return a Redis instance from a string DSN."""
        import redis
        parts = urlparse(dsn)
        _, _, netloc = parts.netloc.partition('@')
        netloc = netloc.rsplit(':')
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

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"%s(%r, %r)" % (self.__class__.__name__, self._dsn, self.backend.name)
