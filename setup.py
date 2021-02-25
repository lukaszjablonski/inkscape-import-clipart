#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (C) 2018-2019 Martin Owens
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
"""
Setup the inkscape extensions manager (inkman)
"""

from setuptools import setup

from import_clipart import __version__, __pkgname__, __doc__

setup(
    name=__pkgname__,
    version=__version__,
    description=__doc__,
    long_description="See README for full details",
    author='Martin Owens',
    url='https://gitlab.com/inkscape/import-clipart',
    author_email='doctormo@gmail.com',
    platforms='linux',
    license='GPLv3',
    data_files=[
        ('', ['import_clipart.py', 'import_clipart.inx', 'import_clipart.ui', 'import_clipart.svg']),
    ],
    classifiers=[
        'Environment :: Plugins',
        'Topic :: Multimedia :: Graphics :: Editors :: Vector-Based',

        'Intended Audience :: Other Audience',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',

        'Development Status :: 5 - Production/Stable',
    ],
    install_requires=[
        'requests',
        'cachecontrol[filecache]',
        'gtkme>=1.5.2',
    ],
)
