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
Base module for all import clipart search source modules.
"""

import re
import os
import sys
import logging
import requests
import importlib

from cachecontrol import CacheControl, CacheControlAdapter
from cachecontrol.caches.file_cache import FileCache
from cachecontrol.heuristics import ExpiresAfter

from inkex.command import CommandNotFound, ProgramRunError, call
from inkex.inkscape_env import get_bin
from collections import defaultdict

class RemotePage:
    """Lazy access to paging systems"""
    icon = "sources/next_page.svg"
    string = property(lambda self: "Next Page")

    def __init__(self, remote, func):
        self.func = func
        self.remote = remote

    def get_next_page(self):
        for info in self.func():
            yield self.remote.result_to_cls(info)

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
    page_cls = RemotePage
    is_default = False
    is_enabled = True

    @classmethod
    def load(cls, name):
        """Load the file or directory of remote sources"""
        if os.path.isfile(name):
            sys.path, sys_path = [os.path.dirname(name)] + sys.path, sys.path
            try:
                importlib.import_module(os.path.basename(name).rsplit('.', 1)[0])
            except ImportError:
                logging.error(f"Failed to load module: {name}")
            sys.path = sys_path
        elif os.path.isdir(name):
            for child in os.listdir(name):
                if not child.startswith('_') and child.endswith('.py'):
                    cls.load(os.path.join(name, child))

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

    def __del__(self):
        self.session.close()

    def file_search(self, query):
        """Search for extension packages"""
        for info in self.search(query):
            yield self.result_to_cls(info)

    def result_to_cls(self, info):
        if callable(info):
            return self.page_cls(self, info)
        return self.file_cls(self, info)

    def to_local_file(self, url):
        """Get a remote url and turn it into a local file"""
        filepath = os.path.join(self.cache_dir, url.split('/')[-1])
        remote = self.session.get(url)
        if remote and remote.status_code == 200:
            with open(filepath, 'wb') as fhl:
                fhl.write(remote.content)
            return filepath
        return None
