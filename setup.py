#!/usr/bin/env python

import os
from setuptools import setup, find_packages

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

setup(name='redis_reservation',
      version=__version__, description='Resource reservation (locking) libraries using a Redis backend, with customizable timeouts and keep-alive support.',
      long_description=README + '\n\n' + CHANGES,
      author='Clever (https://clever.com)',
      author_email='tech-notify@clever.com',
      url='https://github.com/Clever/python-redis-reservation',
      license='Apache License 2.0',
      packages=find_packages(exclude=['*.tests']),
      setup_requires=[
          'nose>=1.0'
      ],
      install_requires=[
          'redis==2.8.0'
      ],
      test_suite='redis_reservation.tests',
      entry_points={
      },
      )
