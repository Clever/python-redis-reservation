#!/usr/bin/env python

from builtins import str
import os
from setuptools import setup, find_packages
try:  # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError:  # for pip <= 9.0.3
    from pip.req import parse_requirements

import pkg_resources

__version__ = '1.0.0'

here = os.path.abspath(os.path.dirname(__file__))

try:
    with open(os.path.join(here, '../README.md')) as f:
        README = f.read()
    with open(os.path.join(here, '../CHANGES.md')) as f:
        CHANGES = f.read()
except:
    README = ''
    CHANGES = ''


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
      install_requires=[str(ir.requirement) for ir in install_reqs],
      setup_requires=['nose>=1.0'],
      test_suite='redis_reservation.tests',
      entry_points={
      },
      )
