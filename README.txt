Copyright Jaume Delclòs Coll (aka cosarara97) 2012 
appdirs.py has its copyright notice (by ActiveState Software Inc.)
and license (MIT) in the file itself.
The rest of the code is mine and under the GPLv3 or later (read LICENSE).

Blue Spider Map editor
======================

Blue Spider is a map editor for the GBA pokémon games.
It supports only the USA versions of Ruby and Fire Red,
although Emerald support is about to get working.

Version:
	git

Dependencies (only when running from source):
	python3
	PyQt4
	PIL (or pillow)

Also, to get the "Open in emulator" button working you'll need
the executable of [VBA-M-Scripted](https://gitorious.org/vba-m-scripted)
as well as the "cfg" file which comes with it in the same directory as
Blue Spider.

Thanks to the devs of EliteMap and NLZ Advance for making the source code
of their tools available.
(If you want nightmares, read EliteMap's source code, lol)

Building:
If creating a package on linux, you'll probably not want
to use cx_freeze. If you have it installed you'll have to
pass the option --no-freeze to setup.py.
On windows you'll probably want to, so just "setup.py build".

