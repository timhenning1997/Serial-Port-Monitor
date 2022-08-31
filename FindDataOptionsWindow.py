import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from SerialParameters import SerialParameters
from UsefulFunctions import isInt, returnInt, returnFloat, isFloat


class FindDataOptionsWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Data Options")

        # __________ Graph Option Group Box __________
        dataFindMethodLabel = QLabel("Find data")

        self.dataFindMethodCombobox = QComboBox()
        self.dataFindMethodCombobox.addItem("Automatic")
        self.dataFindMethodCombobox.addItem("Every byte")
        self.dataFindMethodCombobox.addItem("Every 2 bytes")
        self.dataFindMethodCombobox.addItem("Every 3 bytes")
        self.dataFindMethodCombobox.addItem("Every 4 bytes")
        self.dataFindMethodCombobox.addItem("Every 5 bytes")
        self.dataFindMethodCombobox.addItem("Every 6 bytes")
        self.dataFindMethodCombobox.addItem("Every 7 bytes")
        self.dataFindMethodCombobox.addItem("Every 8 bytes")
        self.dataFindMethodCombobox.addItem("Every 9 bytes")
        self.dataFindMethodCombobox.addItem("Every 10 bytes")

        dataOptionsLayout = QFormLayout()
        dataOptionsLayout.addRow(dataFindMethodLabel, self.dataFindMethodCombobox)

        dataOptionsGroupbox = QGroupBox("Data options")
        dataOptionsGroupbox.setLayout(dataOptionsLayout)

        # __________ Submit Button Layout __________
        self.cancelButton = QPushButton("Cancel")
        self.okButton = QPushButton("OK")
        self.okButton.setAutoDefault(True)
        QTimer.singleShot(0, self.okButton.setFocus)

        submitButtonLayout = QHBoxLayout()
        submitButtonLayout.addWidget(self.okButton)
        submitButtonLayout.addWidget(self.cancelButton)


        # __________ Main Grid Layout __________
        gridLayout = QGridLayout()
        gridLayout.addWidget(dataOptionsGroupbox, 0, 0, 1, 1)
        gridLayout.addLayout(submitButtonLayout, 1, 0, 1, 1)

        self.setLayout(gridLayout)

        # __________ QPushButton Function __________
        self.cancelButton.clicked.connect(self.close)
