# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages
from taxon import __version__, __author_name__, __author_email__

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

with open(os.path.join(os.path.dirname(__file__), 'LICENSE')) as f:
    license = f.read()

setupinfo = dict(
    name='redis-taxon',
    version=__version__,
    description='Redis-backed tagged data store',
    long_description=readme,
    author=__author_name__,
    author_email=__author_email__,
    url='https://github.com/jdp/taxon',
    keywords=['redis', 'key-value', 'store', 'tag', 'taxonomy'],
    include_package_data=True,
    packages=find_packages(exclude=('tests', 'docs')),
    license=license,
    requires=['redis']
)

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(**setupinfo)
