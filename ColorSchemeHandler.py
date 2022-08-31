from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class ColorSchemeHandler(QObject):
    colorChangeSignal = pyqtSignal()

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.setToDarkScheme()

    def setToStyleSheet(self, styleSheetName):
        sshFile = styleSheetName
        with open(sshFile, "r") as fh:
            self.app.setStyleSheet(fh.read())

    def setToDarkScheme(self):


        # 'Breeze', 'Oxygen', 'QtCurve', 'Windows', 'Fusion'
        QApplication.setStyle("Fusion")
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(35, 35, 35))

        dark_palette.setColor(QPalette.Active, QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray)
        dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, Qt.darkGray)
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray)
        dark_palette.setColor(QPalette.Disabled, QPalette.Light, QColor(53, 53, 53))
        QApplication.setPalette(dark_palette)

        self.colorChangeSignal.emit()

    def setToDefaultColor(self):
        QApplication.setStyle("windowsvista")
        default_palette = QPalette()
        default_palette.setColor(QPalette.Window, QColor(240, 240, 240))
        default_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        default_palette.setColor(QPalette.Base, QColor(255, 255, 255))
        default_palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        default_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        default_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        default_palette.setColor(QPalette.Text, QColor(0, 0, 0))
        default_palette.setColor(QPalette.Button, QColor(240, 240, 240))
        default_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        default_palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        default_palette.setColor(QPalette.Link, QColor(0, 0, 255))
        default_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        default_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        default_palette.setColor(QPalette.Active, QPalette.Button, QColor(53, 53, 53))
        default_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(120, 120, 120))
        default_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(120, 120, 120))
        default_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(120, 120, 120))
        default_palette.setColor(QPalette.Disabled, QPalette.Light, QColor(240, 240, 240))
        QApplication.setPalette(default_palette)

        self.colorChangeSignal.emit()
