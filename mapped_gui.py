#!/usr/bin/env python3

import sys
from PyQt4 import Qt, QtCore, QtGui
from window import Ui_MainWindow

import mapped

#MapHeaders      = 0x53324
#Maps            = 0x5326C
#MapLabels       = 0xFBFE0

#get_addr = lambda x : int.from_bytes(x, "little")
#
#def get_rom_addr(x): # Safer and more useful version
#    a = int.from_bytes(x, "little")
#    if a & 0x8000000 == 0x8000000:
#        return a & 0xFFFFFF
#    else:
#        return -1


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
        self.ui.treeView.clicked.connect(self.load_map)
        # self.ui.pushButton_NeuesMoebel.clicked.connect(self.add_item)

    #def get_rom_addr_at(self, x):
    #    return get_rom_addr(self.rom_contents[x:x+4])

    
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
        self.banks = mapped.get_banks(self.rom_contents)
        for i, bank in enumerate(self.banks):
            self.treemodel.appendRow(QtGui.QStandardItem(hex(i) + " - " + hex(bank)))
            self.load_maps(i)
            #self.treemodel.setItem(1, QtGui.QStandardItem("seccond"))
            #self.treemodel.item(1).appendRow(QtGui.QStandardItem("seccond child"))

    def load_maps(self, bank_num):
        maps = mapped.get_map_headers(self.rom_contents, bank_num, self.banks)

        for i, map, in enumerate(maps):
            self.treemodel.item(bank_num).appendRow(
                    QtGui.QStandardItem(hex(i) + " - " + hex(map))
                    )
        print(self.treemodel.item(0).child(9).text())

    def load_map(self, qindex):
        bank_n = qindex.parent().row()
        if bank_n == -1:
            return
        map_n = qindex.row()
        print(bank_n, map_n)
        maps = mapped.get_map_headers(self.rom_contents, bank_n, self.banks)
        map_h_ptr = maps[map_n]
        map_header = mapped.parse_map_header(self.rom_contents, map_h_ptr)
        #print(map_header)
        map_data_header = mapped.parse_map_data(
                self.rom_contents, map_header['map_data_ptr']
                )
        print(map_data_header)






if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())


