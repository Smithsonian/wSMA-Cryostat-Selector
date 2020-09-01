#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as fh:
        return fh.read()


setup(
    name='wsma-cryostat-selector',
    version='0.0.0',
    license='MIT',
    description='Package for controlling the wSMA Cryostat Selector Wheel',
    author='Paul Grimes',
    author_email='pgrimes@cfa.harvard.edu',
    url='https://github.com/Smithsonian/wSMA-Cryostat-Selector',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Utilities',
        'Private :: Do Not Upload',
    ],
    project_urls={
        'Issue Tracker': 'https://github.com/Smithsonian/wSMA-Cryostat-Selector/issues',
    },
    keywords=[
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    python_requires='>=3.6',
    install_requires=[
        'pymodbus',
        'argparse'
    ],
    extras_require={
    },
    entry_points={
        'console_scripts': [
            'selector = wsma_cryostat_selector.cli:main',
        ]
    },
)
