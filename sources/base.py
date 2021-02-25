#
# Copyright (C) 2021 Martin Owens
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
Base module for all search source modules.
"""

import re
import os
import json
import logging
import requests

from zipfile import ZipFile

from cachecontrol import CacheControl, CacheControlAdapter
from cachecontrol.caches.file_cache import FileCache
from cachecontrol.heuristics import ExpiresAfter

from inkex.command import CommandNotFound, ProgramRunError, call
from inkex.inkscape_env import get_bin
from collections import defaultdict

class RemoteFile:
    """Lazy access to remote files"""
    def __init__(self, session, cache_dir, info):
        self.session = session
        self.cache_dir = cache_dir
        for field in ('name', 'thumbnail', 'license', 'file'):
            if field not in info:
                raise ValueError(f"Field {field} not provided in RemoteFile package")
        self.info = info

    def __str__(self):
        return self.info['name']

    def get(self):
        return self.session.get(self.info['file'])

    def filename(self):
        return self.info['file'].split('/')[-1]

    def filepath(self):
        return os.path.join(self.cache_dir, self.filename())

    def as_local_file(self):
        remote = self.get()
        if remote and remote.status_code == 200:
            with open(self.filepath(), 'wb') as fhl:
                fhl.write(remote.content)
            return self.filepath()
        return None

class RemoteSource:
    """A remote source of svg images which can be searched and downloaded"""
    # These are the properties that should be overridden in your class
    name = None
    icon = None
    file_cls = RemoteFile

    def search(self, query, tags=[]):
        """Search for the given query and yield each item, will raise if any other response"""
        raise NotImplementedError("You must implement a search function for this remote source!")

    sources = {}
    def __init_subclass__(cls):
        if cls != RemoteSource:
            cls.sources[cls.__name__] = cls

    def __init__(self, cache_dir):
        self.version = version
        self.session = requests.session()
        self.cache_dir = cache_dir
        self.session.mount('https://', CacheControlAdapter(
            cache=FileCache(cache_dir),
            heuristic=ExpiresAfter(days=5),
        ))

    def file_search(self, query):
        """Search for extension packages"""
        for info in self.search(query):
            yield self.file_cls(self.session, self.cache_dir, info)

