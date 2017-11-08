#!/usr/bin/env python

import os
from setuptools import setup, find_packages
from pip.req import parse_requirements

import pkg_resources

__version__ = '0.2.1'

here = os.path.abspath(os.path.dirname(__file__))

try:
    with open(os.path.join(here, '../README.md')) as f:
        README = f.read()
    with open(os.path.join(here, '../CHANGES.md')) as f:
        CHANGES = f.read()
except:
    README = ''
    CHANGES = ''

pr_kwargs = {}
if pkg_resources.get_distribution("pip").version >= '6.0':
  pr_kwargs = {"session": False}

install_reqs = parse_requirements(
    os.path.join(
        here,
        './requirements.txt'
    ), **pr_kwargs)
  

setup(name='redis_reservation',
      version=__version__, description='Resource reservation (locking) libraries using a Redis backend, with customizable timeouts and keep-alive support.',
      long_description=README + '\n\n' + CHANGES,
      author='Clever (https://clever.com)',
      author_email='tech-notify@clever.com',
      url='https://github.com/Clever/python-redis-reservation',
      license='Apache License 2.0',
      packages=find_packages(exclude=['*.tests']),
      install_requires=[str(ir.req) for ir in install_reqs],
      setup_requires=['nose>=1.0'],
      test_suite='redis_reservation.tests',
      entry_points={
      },
      )
