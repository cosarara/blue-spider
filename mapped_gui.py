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

from PIL import Image, ImageQt


class Window(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.treemodel = QtGui.QStandardItemModel()
        self.ui.treeView.setModel(self.treemodel)

        self.map_scene = QtGui.QGraphicsScene()
        self.ui.map.setScene(self.map_scene)
        #self.map_pixmap = QtGui.QPixmap()
        #self.
        self.palette_scene = QtGui.QGraphicsScene()
        self.ui.palette.setScene(self.palette_scene)
        self.map_scene = QtGui.QGraphicsScene()
        self.ui.map.setScene(self.map_scene)

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
        #print(self.treemodel.item(0).child(9).text())

    def load_tileset(self, tileset_header, previous_img=None):
        print(tileset_header)
        t_img_ptr = tileset_header['tileset_image_ptr']
        tileset_img = mapped.get_tileset_img(self.rom_contents, t_img_ptr)
        if previous_img:
            w = previous_img.size[0]
            h = previous_img.size[1] + tileset_img.size[1]
            print("big_img_size", w, h)
            big_img = Image.new("RGB", (w, h))
            pos = (0, 0, previous_img.size[0], previous_img.size[1])
            big_img.paste(previous_img, pos)
            x = 0
            y = previous_img.size[1]
            x2 = x + tileset_img.size[0]
            y2 = y + tileset_img.size[1]
            pos = (x, y, x2, y2)
            big_img.paste(tileset_img, pos)
            tileset_img = big_img
        block_data_mem = mapped.parse_block_data(self.rom_contents, tileset_header)
        blocks_imgs = mapped.build_block_imgs(block_data_mem, tileset_img)
        #dummy_img = Image.new("RGB", (16, 16))
        #blocks_imgs += [dummy_img] * 512
        self.blocks_imgs += blocks_imgs
        return tileset_img

    def draw_palette(self):
        # The tile palette, not the color one
        blocks_imgs = self.blocks_imgs
        print("len", len(blocks_imgs))
        #blocks_img_w = (len(blocks_imgs) // 8) * 16
        blocks_img_w = 16 * 8 # 8 tiles per row
        print("w", blocks_img_w)
        blocks_img_h = (len(blocks_imgs) * 16) // 8
        print("h", blocks_img_h)
        blocks_img = Image.new("RGB", (blocks_img_w, blocks_img_h))
        i = 0
        for row in range(blocks_img_h // 16):
            for col in range(blocks_img_w // 16):
                x = col*16
                y = row*16
                x2 = x+16
                y2 = y+16
                pos = (x, y, x2, y2)
                block_img = blocks_imgs[i]
                blocks_img.paste(block_img, pos)
                i += 1

        #self.t1_img_qt = ImageQt.ImageQt(tileset1_img)
        #self.t1_img_qt = ImageQt.ImageQt(blocks_imgs[map_n])
        blocks_img.save("tpalette.png", "PNG")
        self.t1_img_qt = ImageQt.ImageQt(blocks_img)

        self.tilesetPixMap = QtGui.QPixmap.fromImage(self.t1_img_qt)
        self.palette_scene.clear()
        self.palette_scene.addPixmap(self.tilesetPixMap)
        self.palette_scene.update()
        #self.ui.palette.fitInView(self.palette_scene.sceneRect(), mode=QtCore.Qt.KeepAspectRatio)

    def draw_map(self, map_mem, w, h):
        i = 0
        map_img = Image.new("RGB", (w*16, h*16))
        for row in range(h):
            for tile in range(w):
                # Each tile is 16 bit, 9 bits for tile num. and 7 for attributes
                tbytes = map_mem[i*2:i*2+2]
                #char = tbytes[0] + tbytes[1]
                tile_num = tbytes[0] | (tbytes[1] & 0b11) << 8
                behavior = (tbytes[1] & 0b11111100) >> 2

                x = tile*16
                y = row*16
                x2 = x+16
                y2 = y+16
                pos = (x, y, x2, y2)

                #print(tile_num, len(self.blocks_imgs))
                map_img.paste(self.blocks_imgs[tile_num], pos)
                i += 1

        self.map_img_qt = ImageQt.ImageQt(map_img)
        self.mapPixMap = QtGui.QPixmap.fromImage(self.map_img_qt)
        self.map_scene.clear()
        self.map_scene.addPixmap(self.mapPixMap)
        self.map_scene.update()



    def load_map(self, qindex):
        bank_n = qindex.parent().row()
        if bank_n == -1:
            return
        map_n = qindex.row()
        print(bank_n, map_n)
        maps = mapped.get_map_headers(self.rom_contents, bank_n, self.banks)
        map_h_ptr = maps[map_n]
        map_header = mapped.parse_map_header(self.rom_contents, map_h_ptr)
        map_data_header = mapped.parse_map_data(
                self.rom_contents, map_header['map_data_ptr']
                )

        self.blocks_imgs = []

        tileset_header = mapped.parse_tileset_header(
                self.rom_contents,
                map_data_header['global_tileset_ptr']
                )
        tileset2_header = mapped.parse_tileset_header(
                self.rom_contents,
                map_data_header['local_tileset_ptr']
                )
        t1_img = self.load_tileset(tileset_header)
        self.load_tileset(tileset2_header, t1_img)

        map_size = map_data_header['w'] * map_data_header['h'] * 2 # Every tile is 2 bytes
        tilemap_ptr = map_data_header['tilemap_ptr']
        map_mem = self.rom_contents[tilemap_ptr:tilemap_ptr+map_size]
        self.draw_map(map_mem, map_data_header['w'], map_data_header['h'])
        self.draw_palette()






if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())


