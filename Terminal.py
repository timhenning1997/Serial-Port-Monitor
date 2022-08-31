import time

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from Tab import Tab
from datetime import datetime
import serial
import serial.tools.list_ports
from SerialParameters import SerialParameters


class PortCombobox(QComboBox):
    def __init__(self, connectedPorts: list):
        super().__init__()
        self.connectedPorts = connectedPorts
        self.lastText = "COM-ALL"

        self.addItem("COM-ALL")
        for p in self.connectedPorts:
            self.addItem(p.port)
        self.setCurrentText(self.lastText)
        self.adjustSize()
        self.activated.connect(self.handleActivated)

    def showPopup(self):
        self.clear()
        self.addItem("COM-ALL")
        for p in self.connectedPorts:
            self.addItem(p.port)
        self.setCurrentText(self.lastText)
        super().showPopup()

    def handleActivated(self, index):
        self.lastText = self.itemText(index)


class Terminal(Tab):
    sendSerialWriteSignal = pyqtSignal(str, object)
    renameTabSignal = pyqtSignal()

    def __init__(self, name, connectedPorts: list = None, port: str = "ALL", UUID=None, parent=None):
        super().__init__("Terminal", name, port, UUID, parent)

        self.loggingFileName = "test2.txt"

        self.connectedPorts = connectedPorts
        self.port = port

        self.portCombobox = PortCombobox(self.connectedPorts)
        self.portCombobox.activated.connect(self.changeBaudrate)
        self.portCombobox.activated.connect(self.changeNewline)
        self.portCombobox.activated.connect(self.changeTabName)

        self.baudrateCombobox = QComboBox()
        self.baudrateCombobox.addItem("ALL Baud")
        self.baudrateCombobox.addItem("300 Baud")
        self.baudrateCombobox.addItem("1200 Baud")
        self.baudrateCombobox.addItem("2400 Baud")
        self.baudrateCombobox.addItem("4800 Baud")
        self.baudrateCombobox.addItem("9600 Baud")
        self.baudrateCombobox.addItem("19200 Baud")
        self.baudrateCombobox.addItem("38400 Baud")
        self.baudrateCombobox.addItem("57600 Baud")
        self.baudrateCombobox.addItem("74880 Baud")
        self.baudrateCombobox.addItem("115200 Baud")
        self.baudrateCombobox.addItem("230400 Baud")
        self.baudrateCombobox.addItem("250000 Baud")
        self.baudrateCombobox.addItem("500000 Baud")
        self.baudrateCombobox.addItem("1000000 Baud")
        self.baudrateCombobox.addItem("2000000 Baud")
        self.baudrateCombobox.setCurrentText("ALL Baud")

        self.clearTextButton = QPushButton("Clear output")
        self.clearTextButton.clicked.connect(self.clearText)

        optionsLayout = QHBoxLayout()
        optionsLayout.addWidget(self.portCombobox)
        optionsLayout.addWidget(self.baudrateCombobox)
        optionsLayout.addStretch()
        optionsLayout.addWidget(self.clearTextButton)

        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)

        self.autoscrollCheckbox = QCheckBox("Autoscroll")
        self.autoscrollCheckbox.setChecked(True)
        self.autoscrollCheckbox.adjustSize()

        self.timestampCheckbox = QCheckBox("Zeitstempel anzeigen")
        self.timestampCheckbox.adjustSize()

        self.portstampCheckbox = QCheckBox("Port anzeigen")
        self.portstampCheckbox.adjustSize()

        self.loggingCheckbox = QCheckBox("Logging")
        self.loggingCheckbox.adjustSize()
        self.loggingCheckbox.stateChanged.connect(self.btnstate)

        self.maxLinesCheckbox = QCheckBox("Clamp lines")
        self.maxLinesCheckbox.setChecked(True)
        self.maxLinesCheckbox.adjustSize()

        options2Layout = QHBoxLayout()
        options2Layout.addWidget(self.autoscrollCheckbox)
        options2Layout.addWidget(self.timestampCheckbox)
        options2Layout.addWidget(self.portstampCheckbox)
        options2Layout.addWidget(self.loggingCheckbox)
        options2Layout.addWidget(self.maxLinesCheckbox)
        options2Layout.addStretch()

        self.lineEdit = QLineEdit()
        self.lineEdit.returnPressed.connect(self.sendData)
        self.sendButton = QPushButton("Senden")
        self.sendButton.clicked.connect(self.sendData)
        self.newLineCharCombobox = QComboBox()
        self.newLineCharCombobox.setFixedWidth(65)
        self.newLineCharCombobox.addItem("None      |Kein Zeilenende")
        self.newLineCharCombobox.addItem("NL           |Neue Zeile")
        self.newLineCharCombobox.addItem("CR           |Zeilenumbruch")
        self.newLineCharCombobox.addItem("NL&CR   |Sowhol CR als auch NL")

        sendLayout = QHBoxLayout()
        sendLayout.addWidget(self.lineEdit)
        sendLayout.addWidget(self.newLineCharCombobox)
        sendLayout.addWidget(self.sendButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(optionsLayout)
        mainLayout.addWidget(self.textEdit)
        mainLayout.addLayout(options2Layout)
        mainLayout.addLayout(sendLayout)

        self.setLayout(mainLayout)

        self.initUI()

    def initUI(self):
        if self.port == "COM-ALL":
            return
        if self.portCombobox.findText(self.port) != -1:
            self.portCombobox.setCurrentText(self.port)
            self.portCombobox.lastText = self.port
            self.changeBaudrate()
            self.changeNewline()

    def changeTabName(self):
        if self.portCombobox.currentText() == "COM-ALL":
            self.name = self.name[0: self.name.find(":") + 2] + "ALL"
        else:
            self.name = self.name[0: self.name.find(":") + 2] + self.portCombobox.currentText()

        self.renameTabSignal.emit()

    def changeBaudrate(self):
        if self.portCombobox.currentText() == "COM-ALL":
            self.baudrateCombobox.setCurrentText("ALL Baud")
        else:
            for p in self.connectedPorts:
                if p.port == self.portCombobox.currentText():
                    baud = str(p.baudrate) + " Baud"
                    if self.baudrateCombobox.findText(baud) != -1:
                        self.baudrateCombobox.setCurrentText(baud)
                    else:
                        self.baudrateCombobox.addItem(baud)
                        self.baudrateCombobox.setCurrentText(baud)

    def changeNewline(self):
        if self.portCombobox.currentText() == "COM-ALL":
            return
        for p in self.connectedPorts:
            if p.port == self.portCombobox.currentText():
                if p.appendCR and p.appendLF:
                    self.newLineCharCombobox.setCurrentText("Sowhol CR als auch NL")
                elif p.appendCR:
                    self.newLineCharCombobox.setCurrentText("Zeilenumbruch (CR)")
                elif p.appendLF:
                    self.newLineCharCombobox.setCurrentText("Neue Zeile (NL)")
                else:
                    self.newLineCharCombobox.setCurrentText("Kein Zeilenende")

    def receiveData(self, obj: SerialParameters, data):
        if self.portCombobox.currentText() != obj.port and self.portCombobox.currentText() != "COM-ALL":
            return
        if self.baudrateCombobox.currentText() != str(obj.baudrate) + " Baud" and self.baudrateCombobox.currentText() != "ALL Baud":
            return

        line = ""
        if self.timestampCheckbox.isChecked() or self.portstampCheckbox.isChecked():
            line += "|"
        if self.timestampCheckbox.isChecked():
            line += datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        if self.portstampCheckbox.isChecked():
            line += " " + obj.port
        if line != "":
            line += " ->| "
        try:
            rawData = data.decode('utf-8')
            line += rawData
        except:
            line += str(data) + "\n"

        self.textEdit.append(line.strip('\n\r'))
        if self.loggingCheckbox.isChecked():
            with open(self.loggingFileName, 'a') as file:
                file.write(line.rstrip('\n'))
        if self.maxLinesCheckbox.isChecked():
            plainText = self.textEdit.toPlainText()
            if len(plainText) > 15000:
                self.textEdit.setPlainText(plainText[-14000:])
        if self.autoscrollCheckbox.isChecked():
            self.textEdit.moveCursor(QTextCursor.End)

    def btnstate(self, state):
        if state == Qt.Checked:
            date_time = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
            self.loggingFileName = "logging Terminal " + date_time + ".txt"

    def closeEvent(self, event):
        pass

    def applySettings(self, settings: QSettings = None):
        if settings.contains(self.uuid):
            tempSettings = settings.value(self.uuid)
            if self.portCombobox.findText(tempSettings["port"]) == -1:
                self.portCombobox.addItem(tempSettings["port"])
            self.portCombobox.lastText = tempSettings["port"]
            self.portCombobox.setCurrentText(tempSettings["port"])
            self.changeTabName()
            self.baudrateCombobox.setCurrentText(tempSettings["baud"])
            self.lineEdit.setText(tempSettings["lineEditText"])
            self.autoscrollCheckbox.setChecked(tempSettings["autoscroll"])
            self.timestampCheckbox.setChecked(tempSettings["timestamp"])
            self.portstampCheckbox.setChecked(tempSettings["portstamp"])
            self.loggingCheckbox.setChecked(tempSettings["logging"])
            self.maxLinesCheckbox.setChecked(tempSettings["maxlines"])
            self.newLineCharCombobox.setCurrentText(tempSettings["newlinechar"])

    def saveSettings(self, settings: QSettings = None):
        tempSettings = {"port": self.portCombobox.currentText(),
                        "baud": self.baudrateCombobox.currentText(),
                        "lineEditText": self.lineEdit.text(),
                        "autoscroll": self.autoscrollCheckbox.isChecked(),
                        "timestamp": self.timestampCheckbox.isChecked(),
                        "portstamp": self.portstampCheckbox.isChecked(),
                        "logging": self.loggingCheckbox.isChecked(),
                        "maxlines": self.maxLinesCheckbox.isChecked(),
                        "newlinechar": self.newLineCharCombobox.currentText()}
        settings.setValue(self.uuid, tempSettings)

    def sendData(self):
        data = self.lineEdit.text().encode('utf-8')
        self.lineEdit.setText("")
        if self.newLineCharCombobox.currentText() == "Neue Zeile (NL)":
            data += b'\n'
        if self.newLineCharCombobox.currentText() == "Zeilenumbruch (CR)":
            data += b'\r'
        if self.newLineCharCombobox.currentText() == "Sowhol CR als auch NL":
            data += b'\r\n'
        if self.portCombobox.currentText() == "COM-ALL":
            self.sendSerialWriteSignal.emit("ALL", data)
        else:
            self.sendSerialWriteSignal.emit(self.portCombobox.currentText(), data)

    def clearText(self):
        self.textEdit.clear()
