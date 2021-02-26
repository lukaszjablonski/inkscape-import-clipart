"""
Testing tool for running queries.
"""

import sys
import json

from import_sources.base import RemoteSource

def run():
    source = RemoteSource.sources[sys.argv[1]]('/tmp')

    for item in source.search(sys.argv[2]):
        print(json.dumps(item, indent=2))

if __name__ == '__main__':
    run()
