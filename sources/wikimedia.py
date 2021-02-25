
from .base import RemoteSource

class Wikimedia(RemoteSource):
    name = 'Wikimedia'
    icon = 'sources/wikimedia.svg'

    def search(self, query):
        for item in []:
            yield None
