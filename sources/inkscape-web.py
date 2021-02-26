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

from .base import RemoteSource

class InkscapeWebsite(RemoteSource):
    name = 'Inkscape Community'
    icon = 'sources/inkscape-web.svg'
    is_default = True

    base_url = "https://inkscape.org/gallery/=artwork/json/"

    def search(self, query):
        """Ask the inkscape website for some artwork"""
        response = self.session.get(self.base_url, params={'q': query})
        for item in response.json()['items']:
            if 'svg' not in item['type']:
                continue
            yield {
                'id': item['id'],
                'name': item['name'],
                'author': item['author'],
                'license': item['license'],
                'summary': item['summary'],
                'thumbnail': item['icon'] or item['links']['file'],
                'created': item['dates']['created'],
                'popularity': item['stats']['liked'],
                'file': item['links']['file'],
            }
