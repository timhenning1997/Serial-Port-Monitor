import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from SerialParameters import SerialParameters
from UsefulFunctions import isInt, returnInt, returnFloat, isFloat


class SerialConnectWindow(QWidget):
    def __init__(self, portName: str = "none"):
        super().__init__()

        self.setWindowTitle("Port connection")

        # __________ Port Configuration Group Box __________
        portLabel = QLabel("Port")
        baudrateLabel = QLabel("Baud rate")
        dataBitsLabel = QLabel("Data bits")
        stopBitsLabel = QLabel("Stop bits")
        parityLabel = QLabel("Parity")
        flowControlLabel = QLabel("Flow control")

        self.portCombobox = QComboBox()
        self.portCombobox.setEditable(True)
        self.portCombobox.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        for port in serial.tools.list_ports.comports():
            self.portCombobox.addItem(port.name)
        self.portCombobox.setCurrentText(portName)

        self.baudrateCombobox = QComboBox()
        self.baudrateCombobox.setEditable(True)
        self.baudrateCombobox.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        self.baudrateCombobox.addItem("300")
        self.baudrateCombobox.addItem("1200")
        self.baudrateCombobox.addItem("2400")
        self.baudrateCombobox.addItem("4800")
        self.baudrateCombobox.addItem("9600")
        self.baudrateCombobox.addItem("19200")
        self.baudrateCombobox.addItem("38400")
        self.baudrateCombobox.addItem("57600")
        self.baudrateCombobox.addItem("74880")
        self.baudrateCombobox.addItem("115200")
        self.baudrateCombobox.addItem("230400")
        self.baudrateCombobox.addItem("250000")
        self.baudrateCombobox.addItem("500000")
        self.baudrateCombobox.addItem("1000000")
        self.baudrateCombobox.addItem("2000000")
        self.baudrateCombobox.setCurrentText("115200")

        self.dataBitsCombobox = QComboBox()
        self.dataBitsCombobox.addItem("5")
        self.dataBitsCombobox.addItem("6")
        self.dataBitsCombobox.addItem("7")
        self.dataBitsCombobox.addItem("8")
        self.dataBitsCombobox.setCurrentText("8")

        self.stopBitsCombobox = QComboBox()
        self.stopBitsCombobox.addItem("1")
        self.stopBitsCombobox.addItem("1.5")
        self.stopBitsCombobox.addItem("2")
        self.stopBitsCombobox.setCurrentText("1")

        self.parityCombobox = QComboBox()
        self.parityCombobox.addItem("none")
        self.parityCombobox.addItem("even")
        self.parityCombobox.addItem("odd")
        self.parityCombobox.addItem("mark")
        self.parityCombobox.addItem("space")
        self.parityCombobox.setCurrentText("none")

        self.flowControlCombobox = QComboBox()
        self.flowControlCombobox.addItem("none")
        self.flowControlCombobox.addItem("xonxoff")
        self.flowControlCombobox.addItem("rtscts")
        self.flowControlCombobox.addItem("dsrdtr")
        self.flowControlCombobox.setCurrentText("none")

        portConfigLayout = QFormLayout()
        portConfigLayout.addRow(portLabel, self.portCombobox)
        portConfigLayout.addRow(baudrateLabel, self.baudrateCombobox)
        portConfigLayout.addRow(dataBitsLabel, self.dataBitsCombobox)
        portConfigLayout.addRow(stopBitsLabel, self.stopBitsCombobox)
        portConfigLayout.addRow(parityLabel, self.parityCombobox)
        portConfigLayout.addRow(flowControlLabel, self.flowControlCombobox)

        portConfigGroupbox = QGroupBox("Port configuration")
        portConfigGroupbox.setLayout(portConfigLayout)

        # __________ Transmitted Text Group Box __________
        self.appendNothingRB = QRadioButton("Append nothing")
        self.appendCRRB = QRadioButton("Append CR")
        self.appendLFRB = QRadioButton("Append LF")
        self.appendCRLFRB = QRadioButton("Append CR-LF")

        appendButtonGroup = QButtonGroup()
        appendButtonGroup.addButton(self.appendNothingRB)
        appendButtonGroup.addButton(self.appendCRRB)
        appendButtonGroup.addButton(self.appendLFRB)
        appendButtonGroup.addButton(self.appendCRLFRB)

        self.appendNothingRB.setChecked(True)

        self.localEchoCB = QCheckBox("Local echo")

        transmittedTextVLayout = QVBoxLayout()
        transmittedTextVLayout.addWidget(self.appendNothingRB)
        transmittedTextVLayout.addWidget(self.appendCRRB)
        transmittedTextVLayout.addWidget(self.appendLFRB)
        transmittedTextVLayout.addWidget(self.appendCRLFRB)
        transmittedTextVLayout.addWidget(self.localEchoCB)

        transmittedTextGroupbox = QGroupBox("Transmitted text")
        transmittedTextGroupbox.setLayout(transmittedTextVLayout)

        # __________ Received Text Group Box __________
        timeoutLabel = QLabel("Timeout [s]")

        self.timeoutCombobox = QComboBox()
        self.timeoutCombobox.setEditable(True)
        self.timeoutCombobox.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        self.timeoutCombobox.addItem("none")
        self.timeoutCombobox.addItem("0")
        self.timeoutCombobox.addItem("0.1")
        self.timeoutCombobox.addItem("0.2")
        self.timeoutCombobox.addItem("0.3")
        self.timeoutCombobox.addItem("0.4")
        self.timeoutCombobox.addItem("0.5")
        self.timeoutCombobox.addItem("1")
        self.timeoutCombobox.addItem("1.5")
        self.timeoutCombobox.addItem("2")
        self.timeoutCombobox.addItem("3")
        self.timeoutCombobox.addItem("4")
        self.timeoutCombobox.addItem("5")
        self.timeoutCombobox.addItem("10")
        self.timeoutCombobox.setCurrentText("0.3")

        self.readLinesRB = QRadioButton("Read line")
        self.readBytesRB = QRadioButton("Read bytes")
        self.readUntilRB = QRadioButton("Read until")
        self.readWUDRB = QRadioButton('Read WU_Device')
        self.readLoggingRawRB = QRadioButton('Log Raw')
        self.readLinesRB.setChecked(True)
        self.readLinesRB.toggled.connect(self.changeReadTextAvailable)
        self.readWUDRB.toggled.connect(self.changeReadTextAvailable)
        self.readLoggingRawRB.toggled.connect(self.changeReadTextAvailable)
        self.readBytesRB.toggled.connect(self.changeReadTextAvailable)
        self.readUntilRB.toggled.connect(self.changeReadTextAvailable)

        self.readBytesSpinBox = QSpinBox()
        self.readBytesSpinBox.setRange(1, 1000)
        self.readUntilLineEdit = QLineEdit("?")
        self.readUntilLineEdit.setMaxLength(1)
        self.readUntilLineEdit.setFixedWidth(20)
        self.readBytesSpinBox.setEnabled(False)
        self.readUntilLineEdit.setEnabled(False)

        appendButtonGroup = QButtonGroup()
        appendButtonGroup.addButton(self.readLinesRB)
        appendButtonGroup.addButton(self.readWUDRB)
        appendButtonGroup.addButton(self.readLoggingRawRB)
        appendButtonGroup.addButton(self.readBytesRB)
        appendButtonGroup.addButton(self.readUntilRB)

        receivedTextLayout = QGridLayout()
        receivedTextLayout.addWidget(timeoutLabel, 0, 0, 1, 1)
        receivedTextLayout.addWidget(self.timeoutCombobox, 0, 1, 1, 1)
        receivedTextLayout.addWidget(self.readLinesRB, 1, 0, 1, 1)
        receivedTextLayout.addWidget(self.readWUDRB, 2, 0, 1, 1)
        receivedTextLayout.addWidget(self.readLoggingRawRB, 3, 0, 1, 1)
        receivedTextLayout.addWidget(self.readBytesRB, 4, 0, 1, 1)
        receivedTextLayout.addWidget(self.readBytesSpinBox, 4, 1, 1, 1)
        receivedTextLayout.addWidget(self.readUntilRB, 5, 0, 1, 1)
        receivedTextLayout.addWidget(self.readUntilLineEdit, 5, 1, 1, 1)

        receivedTextGroupbox = QGroupBox("Received text")
        receivedTextGroupbox.setLayout(receivedTextLayout)

        # __________ Options Group Box __________
        maxSignalRateLabel = QLabel("Max signal rate [Hz]")

        self.maxSignalRateSpinBox = QSpinBox()
        self.maxSignalRateSpinBox.setRange(1, 30)
        self.maxSignalRateSpinBox.setValue(5)

        optionsLayout = QFormLayout()
        optionsLayout.addRow(maxSignalRateLabel, self.maxSignalRateSpinBox)
        # optionsLayout.addWidget(-------------, 0, 0, 1, 1)

        optionsGroupbox = QGroupBox("Options")
        optionsGroupbox.setLayout(optionsLayout)

        horizontalLine = QFrame()
        horizontalLine.setFrameShape(QFrame.Shape.HLine)
        horizontalLine.setFrameShadow(QFrame.Shadow.Sunken)

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
        gridLayout.addWidget(portConfigGroupbox, 0, 0, 2, 1)
        gridLayout.addWidget(transmittedTextGroupbox, 0, 1, 1, 1)
        gridLayout.addWidget(receivedTextGroupbox, 1, 1, 1, 1)
        gridLayout.addWidget(optionsGroupbox, 0, 2, 2, 1)
        gridLayout.addWidget(horizontalLine, 3, 0, 1, 3)
        gridLayout.addLayout(submitButtonLayout, 4, 2, 1, 1)

        self.setLayout(gridLayout)

        # __________ QPushButton Function __________
        self.cancelButton.clicked.connect(self.close)

    def changeReadTextAvailable(self, checked: bool):
        if not checked:
            return
        if self.sender().text() == "Read line":
            self.readBytesSpinBox.setEnabled(False)
            self.readUntilLineEdit.setEnabled(False)
        elif self.sender().text() == 'Read WU_Device':
            self.readBytesSpinBox.setEnabled(False)
            self.readUntilLineEdit.setEnabled(False)
        elif self.sender().text() == "Read bytes":
            self.readBytesSpinBox.setEnabled(True)
            self.readUntilLineEdit.setEnabled(False)
        elif self.sender().text() == "Read until":
            self.readBytesSpinBox.setEnabled(False)
            self.readUntilLineEdit.setEnabled(True)

    def getSerialParameter(self):
        serialParam = SerialParameters()
        if self.portCombobox.currentText().strip() != "":
            serialParam.port = self.portCombobox.currentText()
        if isInt(self.baudrateCombobox.currentText()):
            serialParam.baudrate = returnInt(self.baudrateCombobox.currentText())
        if {"5": serial.FIVEBITS, "6": serial.SIXBITS, "7": serial.SEVENBITS, "8": serial.EIGHTBITS}.get(self.dataBitsCombobox.currentText()):
            serialParam.bytesize = {"5": serial.FIVEBITS, "6": serial.SIXBITS, "7": serial.SEVENBITS, "8": serial.EIGHTBITS}.get(self.dataBitsCombobox.currentText())
        if {"1": serial.STOPBITS_ONE, "1.5": serial.STOPBITS_ONE_POINT_FIVE, "2": serial.STOPBITS_TWO}.get(self.stopBitsCombobox.currentText()):
            serialParam.stopbits = {"1": serial.STOPBITS_ONE, "1.5": serial.STOPBITS_ONE_POINT_FIVE, "2": serial.STOPBITS_TWO}.get(self.stopBitsCombobox.currentText())
        if {"none": serial.PARITY_NONE, "even": serial.PARITY_EVEN, "odd": serial.PARITY_ODD, "mark": serial.PARITY_MARK, "space": serial.PARITY_SPACE}.get(self.parityCombobox.currentText()):
            serialParam.parity = {"none": serial.PARITY_NONE, "even": serial.PARITY_EVEN, "odd": serial.PARITY_ODD, "mark": serial.PARITY_MARK, "space": serial.PARITY_SPACE}.get(self.parityCombobox.currentText())
        if self.flowControlCombobox.currentText() == "xonxoff":
            serialParam.xonxoff = True
        if self.flowControlCombobox.currentText() == "rtscts":
            serialParam.rtscts = True
        if self.flowControlCombobox.currentText() == "dsrdtr":
            serialParam.dsrdtr = True
        if self.appendCRRB.isChecked():
            serialParam.appendCR = True
        if self.appendLFRB.isChecked():
            serialParam.appendLF = True
        if self.appendCRLFRB.isChecked():
            serialParam.appendCR = True
            serialParam.appendLF = True
        if self.localEchoCB.isChecked():
            serialParam.local_echo = True
        if isFloat(self.timeoutCombobox.currentText()):
            serialParam.timeout = returnFloat(self.timeoutCombobox.currentText())
        if self.readLinesRB.isChecked():
            serialParam.readTextIndex = "read_lines"
        if self.readWUDRB.isChecked():
            serialParam.readTextIndex = "read_WU_device"
        if self.readLoggingRawRB.isChecked():
            serialParam.readTextIndex = "logging_raw"
        if self.readBytesRB.isChecked():
            serialParam.readTextIndex = "read_bytes"
            serialParam.readBytes = self.readBytesSpinBox.value()
        if self.readUntilRB.isChecked():
            serialParam.readTextIndex = "read_until"
            serialParam.readUntil = self.readUntilLineEdit.text()[0]
        serialParam.maxSignalRate = self.maxSignalRateSpinBox.value()

        return serialParam
