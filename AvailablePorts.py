import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class AvailablePorts(QMenu):
    actionTriggeredSignal = pyqtSignal(str)

    def __init__(self, connectedPorts: list, title: str, parent=None):
        super(AvailablePorts, self).__init__(parent)
        self.connectedPorts = connectedPorts
        self.setTitle(title)

    def showEvent(self, QEvent):
        act = QAction("Verfügbare Ports", self)
        act.setEnabled(False)
        font1 = QFont()
        font1.setUnderline(True)
        act.setFont(font1)

        self.clear()
        self.addAction(act)
        action = QAction("&ALL", self)
        self.addAction(action)
        action.triggered.connect(self.actionTriggeredEvent)

        for port in self.connectedPorts:
            action = QAction(port.port, self)
            self.addAction(action)
            action.triggered.connect(self.actionTriggeredEvent)

    def actionTriggeredEvent(self):
        self.actionTriggeredSignal.emit(self.sender().text())


