#!/usr/bin/env python3

import sys
from PyQt4 import Qt, QtCore, QtGui
from window import Ui_MainWindow

MapHeaders      = 0x53324
Maps            = 0x5326C
MapLabels       = 0xFBFE0

get_addr = lambda x : int.from_bytes(x, "little")

def get_rom_addr(x): # Safer and more useful version
    a = int.from_bytes(x, "little")
    if a & 0x8000000 == 0x8000000:
        return a & 0xFFFFFF
    else:
        return -1


class Window(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.treemodel = QtGui.QStandardItemModel()
        self.ui.treeView.setModel(self.treemodel)

        #self.treemodel.setItem(0, QtGui.QStandardItem("first"))
        #self.treemodel.setItem(1, QtGui.QStandardItem("seccond"))
        #self.treemodel.item(1).appendRow(QtGui.QStandardItem("seccond child"))

        QtCore.QObject.connect(self.ui.actionLoad_ROM,
                               QtCore.SIGNAL("triggered()"),
                               self.load_rom)

    def get_rom_addr_at(self, x):
        return get_rom_addr(self.rom_contents[x:x+4])

    
    def load_rom(self):
        fn = QtGui.QFileDialog.getOpenFileName(self, 'Open ROM file', 
                                               QtCore.QDir.homePath(),
                                               "GBA ROM (*.gba);;"
                                               "All files (*)")

        if not fn:
            return
        with open(fn, "rb") as rom_file:
            self.rom_contents = rom_file.read()
        self.load_banks()

        self.rom_file_name = fn

    def load_banks(self):
        i = 0 
        self.banks = []
        while True:
            a = self.get_rom_addr_at(self.get_rom_addr_at(MapHeaders) + i * 4)
            if a == -1:
                break
            self.banks.append(a)
            i += 1
        for i, bank in enumerate(self.banks):
            self.treemodel.appendRow(QtGui.QStandardItem(hex(i) + " - " + hex(bank)))
            self.load_maps(i)
            #self.treemodel.setItem(1, QtGui.QStandardItem("seccond"))
            #self.treemodel.item(1).appendRow(QtGui.QStandardItem("seccond child"))

    def load_maps(self, bank_num):
        n = bank_num
        maps_addr = self.banks[n]
        if n+1 == len(self.banks):
            maps_of_next_bank = self.get_rom_addr_at(MapHeaders)
        else:
            maps_of_next_bank = self.banks[n+1]
        maps = []
        i = 0
        while True:
            a = self.get_rom_addr_at(maps_addr + i * 4)
            if a == -1 or maps_addr + i * 4 == maps_of_next_bank:
                break
            #print(hex(i) + "\t" + hex(a))
            maps.append(a)
            i += 1

        for i, map, in enumerate(maps):
            self.treemodel.item(n).appendRow(QtGui.QStandardItem(hex(i) + " - "
                                                                 + hex(map)))






if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())


