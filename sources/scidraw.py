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

import re
import logging

from import_sources import RemoteSource, RemoteFile
from urllib.parse import urljoin

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


def fix_doi_url(href):
    """
    Fix malformed DOI URLs

    Handles these cases:
      - None or empty                     -> None
      - "https://doi.org/10.5281/..."     -> unchanged (already correct)
      - "https://10.5281/..."             -> "https://doi.org/10.5281/..."
      - "http://10.5281/..."              -> "https://doi.org/10.5281/..."
      - "10.5281/..."                     -> "https://doi.org/10.5281/..."
      - "doi:10.5281/..."                 -> "https://doi.org/10.5281/..."
    """
    if not href:
        return None

    href = href.strip()

    # Already a correct DOI URL
    if re.match(r'https?://doi\.org/', href):
        return href

    # Malformed: https://10. or http://10. (missing doi.org/)
    if re.match(r'https?://10\.', href):
        doi_part = re.sub(r'^https?://', '', href)
        return f"https://doi.org/{doi_part}"

    # Plain DOI: 10.5281/...
    if re.match(r'^10\.', href):
        return f"https://doi.org/{href}"

    # doi:10.5281/... format
    if re.match(r'^doi:', href, re.IGNORECASE):
        doi_part = re.sub(r'^doi:', '', href, flags=re.IGNORECASE)
        return f"https://doi.org/{doi_part.strip()}"

    # Unknown format - return as-is with a warning
    logging.warning("Scidraw: unrecognised DOI format: %s", href)
    return href


class ScidrawFile(RemoteFile):
    """Custom RemoteFile that exposes DOI, title and, author as properties"""

    @property
    def doi(self):
        return self.info.get("doi")

    @property
    def title(self):
        return self.info.get("name", "")

    @property
    def author(self):
        return self.info.get("author", "")


class Scidraw(RemoteSource):
    name = "SciDraw"
    icon = "sources/scidraw.svg"
    base_url = "https://scidraw.io/"
    is_enabled = BeautifulSoup is not None
    file_cls = ScidrawFile

    def html_search(self, response):
        """Extract search results from html"""
        soup = BeautifulSoup(response.text, features="lxml")
        for div in soup.find_all("div", {"class": "modified-card"}):
            if div.figure and div.figure.a and div.figure.a.img:
                img = urljoin(self.base_url, div.figure.a.img.get("src"))

                # Extract name
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

                # Extract author - handle mixed content (text + <b> tags)
                try:
                    author_tag = (
                        div
                        .find("div", {"class": "card-content"})
                        .find("p", {"class": "authorname"})
                    )
                    if author_tag:
                        # get_text() strips all tags (including <b>)
                        # split() + join() collapses all whitespace/newlines
                        author = " ".join(author_tag.get_text().split())
                    else:
                        author = ""
                except AttributeError:
                    author = ""

                # Extract and fix DOI link
                doi_url = None
                try:
                    doi_container = div.find("div", {"class": "doi-container"})
                    if doi_container:
                        doi_anchor = doi_container.find("a")
                        if doi_anchor:
                            doi_url = fix_doi_url(doi_anchor.get("href"))
                except AttributeError:
                    pass

                if doi_url:
                    logging.debug(
                        "Scidraw: found DOI %s for '%s'", doi_url, name
                    )

                yield {
                    "file":      img,
                    "name":      name,
                    "thumbnail": img,
                    "author":    author,
                    "license":   "cc-0",
                    "doi":       doi_url,
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