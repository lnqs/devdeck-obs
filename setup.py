#!/usr/bin/env python

from distutils.core import setup

requirements = open('requirements.txt', 'rt').readlines()
requirements = [x.strip() for x in requirements if x]

setup(name='devdeck-obs',
      version='0.1',
      description='OBS control support for devdeck',
      keywords=['devdeck', 'obs', 'obs-studio'],
      author='Simon Hayessen',
      author_email='simon@lnqs.io',
      url='https://github.com/lnqs/devdeck-obs',
      packages=['devdeckobs'],
      install_requires=requirements,
      )
