.. redis-taxon documentation master file, created by
   sphinx-quickstart on Wed May  2 00:02:52 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Taxon
=====

Taxon is a tagged data store with persistence to a Redis backend. It allows you to organize and query Redis data sets with tags.

In a simple issue tracking app, issues that are tagged as a ``feature`` or ``bugfix`` but not ``experimental`` could be queried for like this:

::

    from redis import Redis
    from taxon import Taxon
    from taxon.query import Tag

    t = Taxon(Redis())
    t.tag('feature', ['issue-312', 'issue-199', 'issue-321'])
    t.tag('experimental', ['issue-199'])
    _, items = t.query((Tag('feature') | Tag('bugfix')) & ~Tag('experimental'))

.. automodule:: taxon

.. autoclass:: Taxon

The Taxon class is the interface through which tags are added and removed, and queries are performed. It wraps a ``Redis`` object, and any method calls on a Taxon object that are not Taxon methods are proxied to the underlying ``Redis`` instance.

.. automodule:: taxon.query

The `taxon.query` module contains the query DSL for querying the Taxon store.

.. autoclass:: And

.. autoclass:: Or

.. autoclass:: Not

.. autoclass:: Tag

Contents:

.. toctree::
   :maxdepth: 2

   intro
   quickstart
   querying
   internals



Modules and Indices
===================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

