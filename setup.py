#! /usr/bin/env python

import os
import sys

import frame_poster

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

packages = [
    'frame_poster',
]

requires = [
    open('requirements.txt').read()
]

if sys.version_info < (2, 7):
    requires += ['argparse']

setup(
    name='frame-poster',
    version=frame_poster.__version__,
    description='',
    long_description=open('README.rst').read(),
    author='Matt Black',
    author_email='dev@mafro.net',
    url='http://github.com/mafrosis/frame-poster',
    packages=packages,
    package_data={'': ['LICENSE']},
    package_dir={'': '.'},
    include_package_data=True,
    install_requires=requires,
    scripts=['scripts/frame-poster'],
    license=open('LICENSE').read(),
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ),
)
