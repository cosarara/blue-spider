
# python speedtest.py ~/RH/tmp/FR.gba 0x82d4bb4 0x82d4c44

from PyQt4 import QtGui
from bluespider import mapped, mapped_gui
import sys
import time
print("imported things")

app = QtGui.QApplication(sys.argv)
print("created stupid app")
window = mapped_gui.Window()
print("created stupid window")
window.load_rom(sys.argv[1])
print("loaded stupid rom")
print(window.game)
t1_header = mapped.parse_tileset_header(
        window.rom_contents,
        int(sys.argv[2], 16),
        window.game
        )
t2_header = mapped.parse_tileset_header(
        window.rom_contents,
        int(sys.argv[3], 16),
        window.game
        )
print("parsed stupid headers")
print("running real test now")
x = time.time()
#window.load_tilesets(t1_header, t1_header, t1_imgs=None)
window.get_tilesets(t1_header, t2_header, t1_imgs=None)
print(time.time() - x)
print("done")


