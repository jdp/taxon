-----
Taxon
-----

Taxon is a package that provides storage and query capabilities to data organized by tags.
It supports both in-process and Redis-backed storage options out of the box.

Features
--------

- **Fully queryable.** Supports expressions using ``And``, ``Or``, and ``Not`` operations as well as direct tag lookup.
- **Versatile.** Data sets can be kept in-process, or stored in Redis or any other engine through drop-in backends.

Getting Started
---------------

First install the taxon package with pip::
    
    $ pip install -U redis-taxon

Then you can start tagging and querying your data::
    
    import redis
    import taxon

    t = taxon.RedisTaxon()

To tag data, use the ``tag`` method on any ``taxon.Taxon`` object.
The first argument is the tag to use, and the following variable arguments are the items to tag.

::
    
    t.tag('feature', 'issue-312', 'issue-199', 'issue-321')
    t.tag('experimental', 'issue-199')

Querying
--------

Taxon allows the dataset to be queried with arbitrary expressions and supports ``And``, ``Or``, and ``Not`` operations.
The query syntax is a small DSL implemented directly in Python.
Most queries are issued with the ``find`` method, which returns a `set` of items.

::
    
    from taxon import RedisTaxon
    from taxon.query import And, Or, Not

    # get issue tracker items with no action required
    t = RedisTaxon()
    items = t.find(Or('invalid', 'closed', 'wontfix'))

Query expressions can also be arbitrarily complex.
Queries issued through the ``query`` method return both the name of the Redis key and a list of items.

::
    
    # get issue tracker items marked feature or bugfix, but not experimental
    _, items = t.query(And(Or('feature', 'bugfix'), Not('experimental')))

There is an alternate query syntax available using the ``Tag`` member from ``taxon.query`` which uses operators instead of classes.
The operators are ``&`` for ``And``, ``|`` for ``Or``, and ``~`` for ``Not``.
The above query in operator syntax looks like this::
    
    from taxon.query import Tag
    items = t.find((Tag('feature') | Tag('bugfix')) & ~Tag('experimental'))

Backends
--------

By implementing drop-in backends, there is greater flexibility in where data is stored.
Any object that implements the methods of ``taxon.backends.Backend`` is a valid backend.
A backend is used by providing it as the first argument to a ``Taxon`` constructor::

    from taxon import Taxon
    from taxon.backends import MemoryBackend
    t = Taxon(MemoryBackend())

.. _Redis: http://redis.io
.. _redis-py: https://github.com/andymccurdy/redis-py

The ``MemoryBackend`` is the in-process storage option.
When your program ends, the data is lost.
The bundled persistence option is the `Redis`_ backend, which accepts ``Redis`` instances from `redis-py`_::

    from redis import Redis
    from taxon import Taxon
    from taxon.backends import RedisBackend
    t = Taxon(RedisBackend(Redis()), 'blog-posts')

You usually will not need to create Taxon instances like this though. There are convenience classes for using the memory and Redis backends::

    from taxon import MemoryTaxon, RedisTaxon
    mt = MemoryTaxon()
    rt = RedisTaxon('redis://localhost:6379/0', 'blog-posts')

MIT License
-----------

Copyright (c) 2012 Justin Poliey <justin@getglue.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


.. image:: https://d2weczhvl823v0.cloudfront.net/jdp/taxon/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free

