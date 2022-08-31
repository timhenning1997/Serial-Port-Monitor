import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class PortMenu(QMenu):
    connectActionTriggeredSignal = pyqtSignal(str)
    disconnectActionTriggeredSignal = pyqtSignal(str)

    def __init__(self, connectedPorts: list, parent=None):
        super(PortMenu, self).__init__(parent)
        self.connectedPorts = connectedPorts
        self.setTitle("&Ports")

    def showEvent(self, QEvent):
        act = QAction("Serielle Ports", self)
        act.setEnabled(False)
        font1 = QFont()
        font1.setUnderline(True)
        act.setFont(font1)

        self.clear()
        self.addAction(act)

        for port in serial.tools.list_ports.comports():
            action = QAction(port.name + " - " + port.description, self)
            action.setCheckable(True)
            if any(x.port == port.name for x in self.connectedPorts):
                action.setChecked(True)
            self.addAction(action)
            action.triggered.connect(self.actionTriggeredEvent)

    def actionTriggeredEvent(self):
        if self.sender().isChecked():
            self.connectActionTriggeredSignal.emit(self.sender().text().split(" -")[0])
        else:
            self.disconnectActionTriggeredSignal.emit(self.sender().text().split(" -")[0])


