from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import *
from os import walk


class ColorThemesMenu(QMenu):
    actionTriggeredSignal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ColorThemesMenu, self).__init__(parent)
        self.setTitle("&Color themes")

        self.darkAction = QAction("&Dark theme", self)
        self.defaultAction = QAction("&Standard theme", self)

        self.addAction(self.defaultAction)
        self.addAction(self.darkAction)

        """
        filenames = next(walk("ColorThemes"), (None, None, []))[2]
        for filename in filenames:
            name = filename.split(".")[0]
            action = QAction(name, self)
            self.addAction(action)
            action.triggered.connect(self.actionTriggeredEvent)
        """

    def actionTriggeredEvent(self):
        self.actionTriggeredSignal.emit("ColorThemes/" + self.sender().text() + ".qss")
