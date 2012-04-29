-----
Taxon
-----

Taxon is a tagged data store with persistence to a Redis backend. It allows you to organize and query Redis data sets with tags.

Features
--------

- Fully queryable. Supports expressions using ``And``, ``Or``, and ``Not`` operations as well as direct tag lookup.
- Persistent. Data is stored in Redis.
- Integrated. Taxon wraps ``Redis`` objects, and proxies Redis commands to Taxon through it.

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

To tag data, use the ``tag`` method on a ``taxon.Taxon`` object.

::
    
    t.tag('feature', ['issue-312', 'issue-199', 'issue-321'])
    t.tag('experimental', ['issue-199'])

To get the items associated with the tag, you can provide the ``Store.query`` method with the name of the tag. The return value is a tuple of the key in which the result is stored, and the set of items in the result.

::
    
    key, items = t.query('feature')

Querying
--------

Taxon allows the dataset to be queried with arbitrary expressions and supports ``And``, ``Or``, and ``Not`` operations. The query syntax is a small DSL implemented directly in Python.

::
    
    from taxon import Taxon
    from taxon.query import And, Or, Not

    # get issue tracker items with no action required
    t = Taxon(my_redis_object)
    _, items = t.query(Or('invalid', 'closed', 'wontfix'))

Query expressions can also be arbitrarily complex.

::
    
    # get issue tracker items marked feature or bugfix, but not experimental
    _, items = t.query(And(Or('feature', 'bugfix'), Not('experimental')))

There is an alternate query syntax available using the ``Tag`` member from ``taxon.query`` which uses operators instead of classes. The operators are ``&`` for ``And``, ``|`` for ``Or``, and ``~`` for ``Not``. The above query in operator syntax looks like this:

::
    
    from taxon.query import Tag
    _, items = t.query((Tag('feature') | Tag('bugfix')) & ~Tag('experimental'))

MIT License
-----------

Copyright (c) 2012 Justin Poliey <justin@getglue.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.