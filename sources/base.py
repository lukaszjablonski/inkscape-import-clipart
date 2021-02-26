#
# Copyright 2021 Martin Owens <doctormo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>
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
    icon = property(lambda self: self.remote.to_local_file(self.info['thumbnail']))
    get_file = lambda self: self.remote.to_local_file(self.info['file'])

    def __init__(self, remote, info):
        for field in ('name', 'thumbnail', 'license', 'file'):
            if field not in info:
                raise ValueError(f"Field {field} not provided in RemoteFile package")
        self.info = info
        self.remote = remote

    @property
    def string(self):
        return self.info['name']


class RemoteSource:
    """A remote source of svg images which can be searched and downloaded"""
    # These are the properties that should be overridden in your class
    name = None
    icon = None
    file_cls = RemoteFile
    is_default = False

    def search(self, query, tags=[]):
        """
        Search for the given query and yield basic informational blocks t hand to file_cls.

        Required fields per yielded object are: name, license, thumbnail and file.
        Optional fields are: id, summary, author, created, popularity
        """
        raise NotImplementedError("You must implement a search function for this remote source!")

    sources = {}
    def __init_subclass__(cls):
        if cls != RemoteSource:
            cls.sources[cls.__name__] = cls

    def __init__(self, cache_dir):
        self.session = requests.session()
        self.cache_dir = cache_dir
        self.session.mount('https://', CacheControlAdapter(
            cache=FileCache(cache_dir),
            heuristic=ExpiresAfter(days=5),
        ))

    def file_search(self, query):
        """Search for extension packages"""
        for info in self.search(query):
            yield self.file_cls(self, info)

    def to_local_file(self, url):
        """Get a remote url and turn it into a local file"""
        filepath = os.path.join(self.cache_dir, url.split('/')[-1])
        remote = self.session.get(url)
        if remote and remote.status_code == 200:
            with open(filepath, 'wb') as fhl:
                fhl.write(remote.content)
            return filepath
        return None
