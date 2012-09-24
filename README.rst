-----
Taxon
-----

Taxon is a tagged data store with persistence to a Redis backend. It allows you to organize and query Redis data sets with tags, and is implemented as a library instead of a stand-alone server.

Features
--------

- **Fully queryable.** Supports expressions using ``And``, ``Or``, and ``Not`` operations as well as direct tag lookup.
- **Persistent.** Data is stored in Redis.

Getting Started
---------------

First install the taxon package with pip:

::
    
    $ pip install -U redis-taxon

Then you can instantiate Taxon stores in your code that wrap ``Redis`` objects from `redis-py`_.

.. _redis-py: https://github.com/andymccurdy/redis-py

::
    
    import redis
    import taxon

    t = taxon.Taxon(redis.Redis())

To tag data, use the ``tag`` method on a ``taxon.Taxon`` object. The first argument is the tag to use, and the following variable arguments are the items to tag.

::
    
    t.tag('feature', 'issue-312', 'issue-199', 'issue-321')
    t.tag('experimental', 'issue-199')

Querying
--------

Taxon allows the dataset to be queried with arbitrary expressions and supports ``And``, ``Or``, and ``Not`` operations. The query syntax is a small DSL implemented directly in Python. Most queries are issued with the ``find`` method, which returns a `set` of items.

::
    
    from taxon import Taxon
    from taxon.query import And, Or, Not

    # get issue tracker items with no action required
    t = Taxon(my_redis_object)
    items = t.find(Or('invalid', 'closed', 'wontfix'))

Query expressions can also be arbitrarily complex. Queries issued through the ``query`` method return both the name of the Redis key and a list of items.

::
    
    # get issue tracker items marked feature or bugfix, but not experimental
    _, items = t.query(And(Or('feature', 'bugfix'), Not('experimental')))

There is an alternate query syntax available using the ``Tag`` member from ``taxon.query`` which uses operators instead of classes. The operators are ``&`` for ``And``, ``|`` for ``Or``, and ``~`` for ``Not``. The above query in operator syntax looks like this:

::
    
    from taxon.query import Tag
    items = t.find((Tag('feature') | Tag('bugfix')) & ~Tag('experimental'))

Data Encoding
-------------

You can also interface better with Python data types by subclassing ``Taxon`` and providing ``encode`` and ``decode`` methods.

::

    import json
    from redis import Redis
    from taxon import Taxon
    from taxon.query import Tag

    class JsonTaxon(Taxon):
        def encode(self, data): return json.dumps(data)
        def decode(self, data): return json.loads(data)

    t = JsonTaxon(Redis())
    t.tag('foo', {'foo': 'bar'})
    _, items = t.query(Tag('foo'))

MIT License
-----------

Copyright (c) 2012 Justin Poliey <justin@getglue.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
