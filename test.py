
""" Here'll be all the unit tests.
    For now all it does is loading the ROM at argv[1] and two maps """

from bluespider import mapped_gui
from PyQt4 import QtGui
import sys

def run_tests(w):
    print("loading ROM")
    w.load_rom(sys.argv[1])
    print("loading map 0 0")
    w.load_map(w.tree_model.item(0).child(0))
    print("loading map 0 1 with the warp function")
    w.go_to_warp(None, 0, 1)

def main():
    app = QtGui.QApplication([])
    win = mapped_gui.Window()
    win.show()
    run_tests(win)
    app.exec_()
    app.deleteLater()
    win.close()

if __name__ == "__main__":
    main()

