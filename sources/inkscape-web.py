
from .base import RemoteSource

class InkscapeWebsite(RemoteSource):
    name = 'Inkscape Community'
    icon = 'sources/inkscape-web.svg'

    def search(self, query):
        for item in []:
            yield None
