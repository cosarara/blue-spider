#!/usr/bin/env python3

try:
    from cx_Freeze import setup, Executable
except:
    print("Warning: cx_Freeze not found. Using distutils")
    from distutils.core import setup
    # lol hack
    class Executable:
        def __init__(self, a, base):
            pass

import sys
import os

try:
    with os.popen("git describe --always | sed 's|-|.|g'") as psfile:
        version = psfile.read().strip("\n")
except:
    version = "git"

base = None
basecli = None
if sys.platform == "win32":
    base = "Win32GUI"
data_files = [
          'data/events/*',
          'data/mov_perms/*',
          'data/icon*',
          'data/*.tbl',
          ]
data_files_cxfreeze = ['bluespider/data/', 'README.txt', 'imageformats']
build_exe_options = {"packages": ["pkg_resources"],
                     "include_files": data_files_cxfreeze,
                     "includes": "PyQt4.QtCore"}

setup(name='BlueSpider',
      version=version,
      description="Blue Spider map editor for the GBA pokémon games",
      author="Jaume (cosarara97) Delclòs",
      author_email="cosarara97@gmail.com",
      url="https://gitorious.org/blue-spider-map-editor",
      packages=['bluespider'],
      package_data={'bluespider': data_files},
      scripts=['bluespider-qt', 'bluespider-cli'],
      requires=['sip', 'PyQt4', 'PIL'],
      options = {"build_exe": build_exe_options},
      executables = [
          Executable("bluespider-qt", base=base),
          Executable("bluespider-cli", base=basecli),
          ],
      )


