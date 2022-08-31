from PyQt5.QtWidgets import *


class LayoutMenu(QMenu):
    def __init__(self, parent=None):
        super(LayoutMenu, self).__init__(parent)
        self.setTitle("&Layout")

        self.layout1x1Action = QAction("&1x1 Layout", self)
        self.layout2x1Action = QAction("2x1 Layout", self)
        self.layout1x2Action = QAction("1x2 Layout", self)
        self.layout2u1Action = QAction("2+1 Layout", self)
        self.layout1u2Action = QAction("1+2 Layout", self)
        self.layout2x2Action = QAction("&2x2 Layout", self)
        self.addAction(self.layout1x1Action)
        self.addAction(self.layout2x1Action)
        self.addAction(self.layout1x2Action)
        self.addAction(self.layout2u1Action)
        self.addAction(self.layout1u2Action)
        self.addAction(self.layout2x2Action)
