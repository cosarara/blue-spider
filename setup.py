#!/usr/bin/env python3

from distutils.core import setup
import os

try:
    with os.popen("git describe --always | sed 's|-|.|g'") as psfile:
        version = psfile.read().strip("\n")
except:
    version = "git"

setup(name='BlueSpider',
      version=version,
      description="Blue Spider map editor for the GBA pokémon games",
      author="Jaume (cosarara97) Delclòs",
      author_email="cosarara97@gmail.com",
      url="https://gitorious.org/blue-spider-map-editor",
      packages=['bluespider'],
      package_data={'bluespider': [
          'data/events/*',
          'data/mov_perms/*',
          'data/icon*',
          'data/*.tbl',
          ]
          },
      scripts=['bluespider-qt', 'bluespider-cli'],
      requires=['sip', 'PyQt4', 'PIL'],
      )


