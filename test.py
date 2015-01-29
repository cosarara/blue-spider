
""" Here'll be all the unit tests.
    For now all it does is loading the ROM at argv[1] and two maps """

from bluespider import mapped_gui
from bluespider import mapped
from PyQt4 import QtGui
import sys
import unittest

fn = "/home/jaume/RH/pkmnruby-mgr.gba"

class MapsTest(unittest.TestCase):
    def setUp(self):
        self.app = QtGui.QApplication([])
        self.win = mapped_gui.Window()
        self.win.show()
        self.win.load_rom(fn)

    def tearDown(self):
        #app.exec_()
        self.win.close()
        self.app.deleteLater()

    def test(self):
        load_all_maps(self.win)

def load_all_maps(w):
    rom, rom_data = w.rom_contents, w.rom_data
    banks = mapped.get_banks(rom, rom_data)
    for bank_n in range(len(banks)):
        maps = mapped.get_map_headers(rom, bank_n, banks)
        for map_n in range(len(maps)):
            print(bank_n, map_n)
            w.load_map(bank_n, map_n)

def t_rom_data(w, fn):
    w.load_rom(fn)
    rom = w.rom_contents
    rom_code = mapped.get_rom_code(rom)
    rom_data, game = mapped.get_rom_data(rom_code)
    if "RUBY" in fn.upper():
        assert w.rom_code == rom_code == b"AXVE"
    if "FR" in fn.upper():
        assert w.rom_code == rom_code == b"BPRE"

def run_tests(w):
    print("loading ROM")
    fn = sys.argv[1]
    t_rom_data(w, fn)
    w.load_rom(fn)

    try:
        t_rom_data(w, fn)
        print("passed rom data")
    except Exception as e:
        print(e)
        print("failed rom data")
    try:
        load_all_maps(w)
    except Exception as e:
        print(e)
        print("failed load_maps")
    #print("loading map 0 0")
    #w.load_map(0, 0)

    #print("loading map 0 1 with the warp function")
    #w.go_to_warp(None, 0, 1)

def main():
    app = QtGui.QApplication([])
    win = mapped_gui.Window()
    win.show()
    run_tests(win)
    win.close()
    #app.exec_()
    app.deleteLater()

if __name__ == "__main__":
    #main()
    unittest.main()


