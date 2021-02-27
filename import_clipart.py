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

__version__ = '0.6'
__pkgname__ = 'inkscape-clipart-importer'

import os
import sys
import logging

from base64 import encodebytes

import inkex
from inkex import inkscape_env
from inkex.elements import load_svg, Image, Defs, NamedView, Metadata, SvgDocumentElement

from appdirs import user_cache_dir
from gtkme import GtkApp, Window, PixmapManager, IconView, asyncme

# This just makes damn sure we're looking at the right path
from import_sources import RemoteSource

CACHE_DIR = user_cache_dir('inkscape-import-clipart', 'Inkscape')

class ResultsIconView(IconView):
    """The search results shown as icons"""
    def get_markup(self, item):
        return item.string

    def get_icon(self, item):
        return item.icon

    def setup(self, svlist):
        svlist.set_markup_column(1)
        svlist.set_pixbuf_column(2)
        crt, crp = svlist.get_cells()
        self.crt_notify = crt.connect('notify', self.keep_size)

    def keep_size(self, crt, *args):
        """Hack Gtk to keep cells smaller"""
        crt.handler_block(self.crt_notify)
        crt.set_property('width', 150)
        crt.handler_unblock(self.crt_notify)


class ImporterWindow(Window):
    """The window that is in the glade file"""
    name = 'import_clipart'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.selected = []
        self.pixmaps = PixmapManager('pixmaps',
            pixmap_dir=CACHE_DIR, size=150, load_size=(300,300))

        self.searching = self.widget('dl-searching')
        self.searchbox = self.searching.get_parent()
        self.searchbox.remove(self.searching)

        # Add each of the source services from their plug-in modules
        self.source = self.widget('service_list')
        self.source_model = self.source.get_model()
        self.source_model.clear()

        RemoteSource.load(os.path.join(os.path.dirname(__file__), 'sources'))
        for x, (key, source) in enumerate(RemoteSource.sources.items()):
            # We add them in GdkPixbuf, string, string format (see glade file)
            self.source_model.append([self.pixmaps.get(source.icon), source.name, key])
            if source.is_default:
                self.source.set_active(x)

        self.select_func = self.gapp.opt.select
        self.results = ResultsIconView(self.widget('results'))
        self.results.pixmaps = self.pixmaps

    def select_image(self, widget):
        self.selected = []
        for item_path in widget.get_selected_items():
            item_iter = self.results._model.get_iter(item_path)
            item = self.results._model[item_iter][0]
            self.selected.append(item)

    def get_selected_source(self):
        """Return the selected source class"""
        _iter = self.source.get_active_iter()
        key = self.source_model[_iter][2]
        return RemoteSource.sources[key](CACHE_DIR)

    def apply_image(self, widget):
        """Apply the selected image and quit"""
        if not self.selected:
            return
        for item in self.selected:
            self.select_func(item.get_file())
        self.exit()

    def search(self, widget):
        """Remote search activation"""
        query = widget.get_text()
        if len(query) > 2:
            self.results.clear()
            self.widget('apply-image').set_sensitive(False)
            self.widget('dl-search').set_sensitive(False)
            self.widget('dl-searching').start()
            self.searchbox.add(self.searching)
            self.async_search(query)

    @asyncme.run_or_none
    def async_search(self, query):
        """Asyncronous searching in PyPI"""
        for package in self.get_selected_source().file_search(query):
            self.add_search_result(package)
        self.search_finished()

    @asyncme.mainloop_only
    def add_search_result(self, package):
        """Adding things to Gtk must be done in mainloop"""
        self.results.add_item(package)

    @asyncme.mainloop_only
    def search_finished(self):
        """After everything, finish the search"""
        self.searchbox.remove(self.searching)
        self.widget('dl-search').set_sensitive(True)
        self.widget('apply-image').set_sensitive(True)
        self.replace(self.searching, self.results)

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

class ImportClipart(inkex.EffectExtension):
    """Import an svg from the internet"""
    selected_filename = None

    def merge_defs(self, defs):
        """Add all the items in defs to the self.svg.defs"""
        target = self.svg.defs
        for child in defs:
            target.append(child)

    def import_svg(self, new_svg):
        """Import an svg file into the current document"""
        for child in new_svg.getroot():
            if isinstance(child, SvgDocumentElement):
                yield from self.import_svg(child)
            elif isinstance(child, Defs):
                self.merge_defs(child)
            elif isinstance(child, (NamedView, Metadata)):
                pass
            else:
                yield child

    def import_from_file(self, filename):
        with open(filename, 'rb') as fhl:
            head = fhl.read(100)
            container = inkex.Layer.new(os.path.basename(filename))
            if b'<?xml' in head or b'<svg' in head:
                objs = self.import_svg(load_svg(head + fhl.read()))
            else:
                objs = self.import_raster(filename, fhl)

            for child in objs:
                container.append(child)
            self.svg.get_current_layer().append(container)

    def effect(self):
        def select_func(filename):
            self.import_from_file(filename)

        App(start_loop=True, select=select_func)

    def import_raster(self, filename, handle):
        """Import a raster image"""
        # Don't read the whole file to check the header
        handle.seek(0)
        file_type = self.get_type(filename, handle.read(10))
        handle.seek(0)

        if file_type:
            # Future: Change encodestring to encodebytes when python3 only
            node = Image()
            node.label = os.path.basename(filename)
            node.set('xlink:href', 'data:{};base64,{}'.format(
                file_type, encodebytes(handle.read()).decode('ascii')))
            yield node

    @staticmethod
    def get_type(path, header):
        """Basic magic header checker, returns mime type"""
        # Taken from embedimage.py
        for head, mime in (
                (b'\x89PNG', 'image/png'),
                (b'\xff\xd8', 'image/jpeg'),
                (b'BM', 'image/bmp'),
                (b'GIF87a', 'image/gif'),
                (b'GIF89a', 'image/gif'),
                (b'MM\x00\x2a', 'image/tiff'),
                (b'II\x2a\x00', 'image/tiff'),
            ):
            if header.startswith(head):
                return mime
        return None


if __name__ == '__main__':
    ImportClipart().run()
