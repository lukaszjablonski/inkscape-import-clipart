#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
Import clipart extension (GUI)
"""

__version__ = '0.5'
__pkgname__ = 'inkscape-clipart-importer'

import os
import sys
import logging

import inkex
from inkex import inkscape_env

from appdirs import user_cache_dir
from gtkme import GtkApp, Window, PixmapManager, asyncme

# This just makes damn sure we're looking at the right path
from sources.base import RemoteSource

CACHE_DIR = user_cache_dir('inkscape-import-clipart', 'Inkscape')

class ImporterWindow(Window):
    name = 'import_clipart'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pixmaps = PixmapManager('pixmaps',
            pixmap_dir=CACHE_DIR, size=150, load_size=(300,300))

        self.searching = self.widget('dl-searching')
        self.searchbox = self.searching.get_parent()
        self.searchbox.remove(self.searching)

        self.source = self.widget('service_list')
        self.source_model = self.source.get_model()
        self.source_model.clear()
        for key, source in RemoteSource.sources.items():
            self.source_model.append([self.pixmaps.get(source.icon), source.name, key])
        self.source.set_active(0)

        self.select_func = self.gapp.opt.select

    def apply_image(self, widget):
        """Apply the selected image and quit"""
        # XXX Download svg file here to cache dir and return filename
        self.select_func(None)
        self.exit()

    def remote_search(self, widget):
        """Remote search activation"""
        query = widget.get_text()
        if len(query) > 2:
            self._remote_search(query)

    def _remote_search(self, query):
        filtered = self.widget('remote_target').get_active()
        self.remote.clear()
        self.widget('remote_install').set_sensitive(False)
        self.widget('remote_info').set_sensitive(False)
        self.widget('dl-search').set_sensitive(False)
        self.searchbox.add(self.searching)
        self.widget('dl-searching').start()
        self.async_search(query, filtered)

    @asyncme.run_or_none
    def async_search(self, query, filtered):
        """Asyncronous searching in PyPI"""
        for package in self.target.search(query, filtered):
            self.add_search_result(package)
        self.search_finished()

    @asyncme.mainloop_only
    def add_search_result(self, package):
        """Adding things to Gtk must be done in mainloop"""
        self.remote.add_item([package])

    @asyncme.mainloop_only
    def search_finished(self):
        """After everything, finish the search"""
        self.searchbox.remove(self.searching)
        self.widget('dl-search').set_sensitive(True)
        self.replace(self.searching, self.remote)

    def dialog(self, msg):
        self.widget('dialog_msg').set_label(msg)
        self.widget('dialog').set_transient_for(self.window)
        self.widget('dialog').show_all()

    def close_dialog(self, widget):
        self.widget('dialog_msg').set_label('')
        self.widget('dialog').hide()

class App(GtkApp):
    """Load the inkscape extensions glade file and attach to window"""
    glade_dir = os.path.join(os.path.dirname(__file__))
    app_name = 'inkscape-import-clipart'
    windows = [ImporterWindow]

class ImportClipart(inkex.GenerateExtension):
    """Import an svg from the internet"""
    selected_filename = None

    def add_arguments(self, pars):
        pass

    def generate(self):
        def select_func(filename):
            if os.path.isfile(filename):
                self.selected_filename = filename

        App(start_loop=True, select=select_func)

        if self.selected_filename:
            return self.import_from_file(self.selected_filename)
        return None

if __name__ == '__main__':
    ImportClipart().run()
