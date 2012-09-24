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
    requires=['redis'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration',
    ]
)

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(**setupinfo)
