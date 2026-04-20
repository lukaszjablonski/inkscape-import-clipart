#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Martin Owens <doctormo@gmail.com>
# Copyright 2022 Simon Duerr <dev@simonduerr.eu>
# Copyright 2026 Lukasz Jablonski <lukasz.jablonski@wp.eu>
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
Import images from the internet, inkscape extension (GUI)
"""

__version__ = "1.0"
__pkgname__ = "inkscape-import-web-image"

import os
import sys
import logging
import warnings

warnings.filterwarnings("ignore")

from collections import defaultdict
from base64 import encodebytes
from appdirs import user_cache_dir

import inkex
from inkex import Style
from inkex.gui import GtkApp, Window, IconView, asyncme
from inkex.gui.pixmap import PixmapManager, SizeFilter, PadFilter, OverlayFilter
from inkex.elements import (
    load_svg,
    Image,
    Defs,
    NamedView,
    Metadata,
    SvgDocumentElement,
    StyleElement,
    TextElement,
)
from gi.repository import Gtk

from import_sources import RemoteSource, RemoteFile, RemotePage

SOURCES = os.path.join(os.path.dirname(__file__), "sources")
LICENSES = os.path.join(os.path.dirname(__file__), "licenses")
CACHE_DIR = user_cache_dir("inkscape-import-web-image", "Inkscape")


class LicenseOverlay(OverlayFilter):
    pixmaps = PixmapManager(LICENSES)

    def get_overlay(self, item=None, manager=None):
        if item is None:
            return None
        return self.pixmaps.get(item.get_overlay())


class ResultsIconView(IconView):
    """The search results shown as icons"""

    def get_markup(self, item):
        return item.string

    def get_icon(self, item):
        return item.icon

    def setup(self):
        self._list.set_markup_column(1)
        self._list.set_pixbuf_column(2)
        crt, crp = self._list.get_cells()
        self.crt_notify = crt.connect("notify", self.keep_size)
        super().setup()

    def keep_size(self, crt, *args):
        """Hack Gtk to keep cells smaller"""
        crt.handler_block(self.crt_notify)
        crt.set_property("width", 150)
        crt.handler_unblock(self.crt_notify)


class ImporterWindow(Window):
    """The window that is in the glade file"""

    name = "import_web_image"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.widget("dl-searching").hide()

        self.source = self.widget("service_list")
        self.source_model = self.source.get_model()
        self.source_model.clear()

        RemoteSource.load(SOURCES)
        pix = PixmapManager(SOURCES, size=150)
        for x, (key, source) in enumerate(RemoteSource.sources.items()):
            if not source.is_enabled:
                continue
            self.source_model.append([pix.get(source.icon), source.name, key])
            if source.is_default:
                self.source.set_active(x)

        pixmaps = PixmapManager(
            CACHE_DIR,
            filters=[
                SizeFilter(size=150),
                PadFilter(size=(0, 150)),
                LicenseOverlay(position=(0.5, 1)),
            ],
        )
        self.select_func = self.gapp.kwargs["select"]
        self.results = ResultsIconView(self.widget("results"), pixmaps)
        self.pool = ResultsIconView(self.widget("pool"), pixmaps)
        self.multiple = False

        self.widget("perm-nocopyright").set_message_type(Gtk.MessageType.WARNING)

    def select_image(self, widget):
        """Callback when clicking on an image in the result list"""
        for item_path in self.widget("results").get_selected_items():
            item_iter = self.results._model.get_iter(item_path)
            item = self.results._model[item_iter][0]
            self.show_license(item)
        self.update_btn_import()

    def show_license(self, item):
        """Display the current item's license information"""
        self.widget("perms").foreach(lambda w: w.hide())
        info = item.license_info
        for mod in info["modules"]:
            self.widget("perm-" + mod).show()

    def get_selected_source(self):
        """Return the selected source class"""
        _iter = self.source.get_active_iter()
        key = self.source_model[_iter][2]
        return RemoteSource.sources[key](CACHE_DIR)

    def img_multiple(self, widget):
        """Enable multi-selection"""
        widget.hide()
        self.widget("btn-single").show()
        self.widget("multiple-box").show()
        self.widget("multiple-buttons").show()
        self.multiple = True
        self.update_btn_import()

    def img_single(self, widget):
        """Enable single-selection"""
        widget.hide()
        self.widget("btn-multiple").show()
        self.widget("multiple-box").hide()
        self.widget("multiple-buttons").hide()
        self.pool.clear()
        self.multiple = False
        self.update_btn_import()

    def img_add(self, widget=None):
        """Add an item from the search to the multi-pool"""
        self.pool.add(self.results.get_selected_items())
        self.update_btn_import()

    def img_remove(self, widget=None):
        """Remove any selected items from the multi-pool"""
        for item in self.pool.get_selected_items():
            self.pool.remove_item(item)
        self.update_btn_import()

    def update_btn_import(self):
        """Set the import button to enabled or disabled"""
        enabled = False
        if self.multiple:
            enabled = bool(list(self.pool))
        else:
            enabled = bool(list(self.results.get_selected_items()))
        self.widget("btn-import").set_sensitive(enabled)

    def result_activate(self, widget=None):
        """Search results double click"""
        if self.multiple:
            self.img_add()
        else:
            self.img_import()

    def img_import(self, widget=None):
        """Apply the selected image and quit"""
        items = []
        if not self.multiple:
            items.extend(self.results.get_selected_items())
        else:
            items.extend([item for item, *_ in self.pool])

        to_exit = True
        for item in items:
            self.select_func(item.file, item=item)
        if to_exit:
            self.exit()

    def search(self, widget):
        """Remote search activation"""
        query = widget.get_text()
        if len(query) > 2:
            self.search_clear()
            self.search_started()
            self.async_search(query)

    @asyncme.run_or_none
    def async_search(self, query):
        """Asyncronous searching"""
        for resource in self.get_selected_source().file_search(query):
            self.add_search_result(resource)
        self.search_finished()

    @asyncme.mainloop_only
    def add_search_result(self, resource):
        """Adding things to Gtk must be done in mainloop"""
        if isinstance(resource, RemotePage):
            return self.set_next_page(resource)
        self.results.add_item(resource)

    def search_clear(self, widget=None):
        """Remove previous search"""
        self.results.clear()
        self.update_btn_import()
        self.next_page_item = None
        self.widget("btn-next-page").hide()

    def search_started(self):
        """Set widgets to stun"""
        self.widget("dl-search").set_sensitive(False)
        self.widget("dl-searching").start()
        self.widget("dl-searching").show()

    @asyncme.mainloop_only
    def search_finished(self):
        """After everything, finish the search"""
        self.widget("dl-search").set_sensitive(True)
        self.widget("dl-searching").hide()
        self.widget("dl-searching").stop()

    def set_next_page(self, item):
        self.next_page_item = item
        self.widget("btn-next-page").show()

    def show_next_page(self, widget=None):
        item = self.next_page_item
        if item:
            self.search_clear()
            self.search_started()
            self.async_next_page(item)

    @asyncme.run_or_none
    def async_next_page(self, item):
        for resource in item.get_next_page():
            self.add_search_result(resource)
        self.search_finished()


class App(GtkApp):
    """Load the inkscape extensions glade file and attach to window"""

    glade_dir = os.path.join(os.path.dirname(__file__))
    app_name = "inkscape-import-web-image"
    windows = [ImporterWindow]


class ImportWebImage(inkex.EffectExtension):
    """Import an svg from the internet"""

    selected_filename = None

    def merge_defs(self, defs):
        """Add all the items in defs to the self.svg.defs"""
        target = self.svg.defs
        for child in defs:
            if isinstance(child, StyleElement):
                continue
            target.append(child)

    def merge_stylesheets(self, svg):
        """Scrub conflicting style-sheets (classes, ids, etc)"""
        elems = defaultdict(list)
        for sheet in svg.getroot().stylesheets:
            for style in sheet:
                xpath = style.to_xpath()
                for elem in svg.xpath(xpath):
                    elems[elem].append(style)
                    if "@id" in xpath:
                        elem.set_random_id()
                    if "@class" in xpath:
                        elem.set("class", None)
        for elem, styles in elems.items():
            output = Style()
            for style in styles:
                output += style
            elem.style = output + elem.style

    def import_svg(self, new_svg):
        """Import an svg file into the current document"""
        self.merge_stylesheets(new_svg)
        for child in new_svg.getroot():
            if isinstance(child, SvgDocumentElement):
                yield from self.import_svg(child)
            elif isinstance(child, StyleElement):
                continue
            elif isinstance(child, Defs):
                self.merge_defs(child)
            elif isinstance(child, (NamedView, Metadata)):
                pass
            else:
                yield child

    def get_viewport_center(self):
        """
        Return the (x, y) center of the currently visible viewport
        in document coordinates.
        Uses the namedview to find current zoom/pan position.
        """
        try:
            namedview = self.svg.namedview
            cx   = namedview.get("inkscape:cx")
            cy   = namedview.get("inkscape:cy")
            zoom = namedview.get("inkscape:zoom")

            if cx is not None and cy is not None and zoom is not None:
                cx   = float(cx)
                cy   = float(cy)
                zoom = float(zoom)

                # inkscape:cx/cy are the document coordinates of the
                # viewport center - use them directly
                return cx, cy

        except Exception as e:
            logging.warning(f"get_viewport_center failed: {e}")

        # Fallback: use document center
        try:
            width  = self.svg.unittouu(self.svg.get("width",  "744"))
            height = self.svg.unittouu(self.svg.get("height", "1052"))
            return width / 2, height / 2
        except Exception:
            return 0.0, 0.0

    def center_group_on_viewport(self, group):
        """
        Move the group so its center aligns with the viewport center.
        """
        try:
            bbox = group.bounding_box()
            if bbox is None:
                logging.warning("center_group_on_viewport: bbox is None")
                return

            # Current center of the group
            group_cx = bbox.left + bbox.width  / 2
            group_cy = bbox.top  + bbox.height / 2

            # Target center (viewport center)
            target_cx, target_cy = self.get_viewport_center()

            # Calculate translation needed
            dx = target_cx - group_cx
            dy = target_cy - group_cy

            # Apply translation
            group.transform.add_translate(dx, dy)

        except Exception as e:
            logging.warning(f"center_group_on_viewport failed: {e}")

    def make_annotation(self, item, container, scale):
        """
        Create a text annotation group below the imported SVG containing:
        - Figure title  (bold, larger)
        - Author        (normal)
        - DOI link      (normal)

        Uses container bounding box for accurate positioning.
        Returns an inkex.Group or None if no metadata available.
        """
        # Settings - adjust to your preference
        font_size_title = 10    # px
        font_size_sub   = 8     # px
        line_gap        = 4     # px gap between lines
        margin_top      = 6     # px gap between image bottom and first line
        font_family     = "sans-serif"

        # Build lines: (text, font_size, is_bold)
        lines = []
        if hasattr(item, "title") and item.title:
            lines.append((item.title, font_size_title, True))
        if hasattr(item, "author") and item.author:
            lines.append((item.author, font_size_sub, False))
        if hasattr(item, "doi") and item.doi:
            lines.append((item.doi, font_size_sub, False))

        if not lines:
            return None

        # Get bounding box of the imported container.
        # NOTE: container must already be in the document tree.
        try:
            bbox   = container.bounding_box()
            x_pos  = bbox.left
            y_base = bbox.bottom
        except Exception as e:
            logging.warning(f"make_annotation: bbox failed: {e}")
            x_pos  = 0.0
            y_base = 100.0 * scale

        annotation_group = inkex.Group()
        annotation_group.label = "annotation"

        y = y_base + margin_top

        for text, size, bold in lines:
            text_elem = TextElement()
            text_elem.text = text
            text_elem.style = inkex.Style({
                "font-size":   f"{size}px",
                "font-family": font_family,
                "font-weight": "bold" if bold else "normal",
                "fill":        "#000000",
            })
            text_elem.set("x", str(x_pos))
            text_elem.set("y", str(y))
            annotation_group.append(text_elem)
            y += size + line_gap

        return annotation_group

    def import_from_file(self, filename, item=None):
        """
        Import an SVG or raster file into the document.
        If item has DOI/title/author metadata,
        a text annotation is added below the image.
        The whole group is then centered on the current viewport.
        """
        if not filename or not os.path.isfile(filename):
            return

        with open(filename, "rb") as fhl:
            head = fhl.read(100)

            if b"<?xml" in head or b"<svg" in head:
                new_svg = load_svg(head + fhl.read())
                objs = list(self.import_svg(new_svg))

                if len(objs) == 1 and isinstance(objs[0], inkex.Group):
                    container = objs[0]
                else:
                    container = inkex.Group()
                    for child in objs:
                        container.append(child)

                container.label = os.path.basename(filename)
                scale = (
                    self.svg.unittouu(1.0) / new_svg.getroot().unittouu(1.0)
                )
                container.transform.add_scale(scale)

            else:
                container = self.import_raster(filename, fhl)
                scale     = 1.0

            # Wrap image + annotation in an outer group
            outer_group = inkex.Group()
            outer_group.label = os.path.basename(filename)
            outer_group.append(container)

            # Append to document BEFORE bounding_box() calls
            self.svg.get_current_layer().append(outer_group)

            # Add annotation if item has metadata
            if item is not None and any(
                hasattr(item, attr) for attr in ("doi", "title")
            ):
                annotation = self.make_annotation(item, container, scale)
                if annotation is not None:
                    outer_group.append(annotation)

            # Center the whole group (image + annotation) on the viewport
            self.center_group_on_viewport(outer_group)

            # Make sure none of the new content is a layer
            for child in outer_group.descendants():
                if isinstance(child, inkex.Group):
                    child.set("inkscape:groupmode", None)

    def effect(self):
        def select_func(filename, item=None):
            self.import_from_file(filename, item=item)

        App(start_loop=True, select=select_func)

    def import_raster(self, filename, handle):
        """Import a raster image"""
        handle.seek(0)
        file_type = self.get_type(filename, handle.read(10))
        handle.seek(0)

        if file_type:
            node = Image()
            node.label = os.path.basename(filename)
            node.set(
                "xlink:href",
                "data:{};base64,{}".format(
                    file_type, encodebytes(handle.read()).decode("ascii")
                ),
            )
            return node

    @staticmethod
    def get_type(path, header):
        """Basic magic header checker, returns mime type"""
        for head, mime in (
            (b"\x89PNG", "image/png"),
            (b"\xff\xd8", "image/jpeg"),
            (b"BM",       "image/bmp"),
            (b"GIF87a",   "image/gif"),
            (b"GIF89a",   "image/gif"),
            (b"MM\x00\x2a", "image/tiff"),
            (b"II\x2a\x00", "image/tiff"),
        ):
            if header.startswith(head):
                return mime
        return None


if __name__ == "__main__":
    ImportWebImage().run()