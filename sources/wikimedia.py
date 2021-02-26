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

import hashlib
from import_sources import RemoteSource

def get_thumbnail(image, width=200):
    """Generate a wikimedia thumbnail url"""
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/"
    # image = e.g. from Wikidata, width in pixels
    image = image.replace(' ', '_') # need to replace spaces with underline 
    my_hash = hashlib.md5()
    my_hash.update(image.encode('utf-8'))
    digest = my_hash.hexdigest()
    raster = image + '.png' if image.endswith('.svg') else image
    url += "{}/{}/{}/{}px-{}".format(digest[0], digest[0:2], image, width, raster)
    return url

class Wikimedia(RemoteSource):
    name = 'Wikimedia'
    icon = 'sources/wikimedia.svg'
    base_url = "https://en.wikipedia.org/w/api.php"

    def search(self, query):
        params = {
            "action": "query",
            "format": "json",
            "generator": "images",
            "prop": "imageinfo",
            "gimlimit": 100,
            "redirects": 1,
            "titles": query,
            "iiprop": "user|timestamp|url|thumbmime|mime|mediatype",
        }
        response = self.session.get(self.base_url, params=params).json()
        if 'error' in response:
            raise IOError(response['error']['info'])
        for item in response['query']['pages'].values():
            img = item['imageinfo'][0]
            yield {
                'id': item.get('pageid', None),
                'name': item['title'].split(':', 1)[-1],
                'author': img['user'],
                'license': 'Unknown', # XXX
                'summary': 'None',
                'thumbnail': get_thumbnail(img['url'].rsplit('/', 1)[-1]),
                'created': img['timestamp'],
                'popularity': 0, # No data
                'file': img['url'],
            }

