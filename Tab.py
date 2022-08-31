from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import *
import uuid


class Tab(QWidget):
    def __init__(self, tabType, name, port: str = "ALL", UUID=None, parent=None):
        super().__init__(parent)
        self.tabType = tabType
        self.name = name
        self.port = port
        self.parent = parent
        if UUID is None:
            self.uuid = str(uuid.uuid4())
        else:
            self.uuid = UUID

    def saveSettings(self, settings: QSettings = None):
        pass

    def applySettings(self, settings: QSettings = None):
        pass

    def closeEvent(self, event):
        pass