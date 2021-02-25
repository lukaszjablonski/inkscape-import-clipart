
from .base import RemoteSource

class OpenClipart(RemoteSource):
    name = 'Open Clipart Library'
    icon = 'sources/ocal.svg'

    def search(self, query):
        for item in []:
            yield None
