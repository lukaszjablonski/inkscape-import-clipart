#
# Copyright 2025 Lukasz Jablonski <lukasz.jablonski@wp.eu>
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

import logging

from import_sources import RemoteSource, RemoteFile
from urllib.parse import urljoin

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class Scidraw(RemoteSource):
    name = "SciDraw"
    icon = "sources/scidraw.svg"
    base_url = "https://scidraw.io/"
    is_enabled = BeautifulSoup is not None
    # No custom file_cls needed: base RemoteFile.get_file()
    # handles direct URL downloads correctly
    file_cls = RemoteFile

    def html_search(self, response):
        """Extract search results from html"""
        soup = BeautifulSoup(response.text, features="lxml")
        for div in soup.find_all("div", {"class": "modified-card"}):
            if div.figure and div.figure.a and div.figure.a.img:
                img = urljoin(self.base_url, div.figure.a.img.get("src"))
                try:
                    name = (
                        div
                        .find("div", {"class": "card-content"})
                        .find("div", {"class": "media-content"})
                        .find("p", {"class": "title"})
                        .get_text(strip=True)
                    )
                except AttributeError:
                    name = ""

                # Capitalise first letter only
                name = name[:1].upper() + name[1:] if name else ""

                yield {
                    "file": img, # direct SVG URL
                    "name": name,
                    "thumbnail": img, # no separate thumbnail available
                    "author": "",
                    "license": "cc-by-4.0", # one license for all images (https://scidraw.io/terms/)
                }

    def search(self, query):
        """HTML searching"""
        return self._search(q=query)

    def _search(self, **params):
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
        except Exception as err:
            logging.error("Scidraw: search request failed: %s", err)
            return []

        items = []
        for item in self.html_search(response):
            items.append(item)
        return items