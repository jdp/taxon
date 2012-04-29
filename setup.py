# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from taxon import __version__


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setupinfo = dict(
    name='redis-taxon',
    version=__version__,
    description='Redis-backed tagged data store',
    long_description=readme,
    author='Justin Poliey',
    author_email='justin@getglue.com',
    url='https://github.com/jdp/taxon',
    keywords=['redis', 'key-value', 'store', 'tag', 'taxonomy'],
    packages=find_packages(exclude=('tests', 'docs')),
    license=license,
    requires=['redis']
)

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(**setupinfo)
