-----
Taxon
-----

Taxon is a tagged data store with persistence to a Redis backend. It allows you to organize and query Redis data sets with tags.

Features
--------

- Fully queryable. Supports expressions using ``And``, ``Or``, and ``Not`` operations as well as direct tag lookup.
- Persistent. Data is stored in Redis.
- Integrated. Operations happen in application code, and query results surface information to smooth direct Redis access.

Getting Started
---------------

First install the taxon package with pip:

    $ pip install -U taxon

Then you can instantiate Taxon stores in your code that wrap ``Redis`` objects from [redis-py](https://github.com/andymccurdy/redis-py).

    import redis
    import taxon

    store = taxon.Store(redis.Redis())

Querying
--------

TODO

MIT License
-----------

Copyright (c) 2012 Justin Poliey <justin@getglue.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.