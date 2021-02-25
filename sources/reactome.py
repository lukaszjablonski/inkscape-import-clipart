
from .base import RemoteSource

class Reactome(RemoteSource):
    name = 'Reactome (Bio)'
    icon = 'sources/reactome.svg'

    def search(self, query):
        for item in []:
            yield None
