import binascii
import math
import os

import spectra

from CalibrationFileLabel import CalibrationFileLabel
from CalibrationFilePushButton import CalibrationFilePushButton
from CalibrationOfData import *
from datetime import datetime
import time
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from UsefulFunctions import resource_path

from Tab import Tab
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


class Measurement(Tab):
    sendSerialWriteSignal = pyqtSignal(str, object)
    startRecordSignal = pyqtSignal(str, str, str)
    stopRecordSignal = pyqtSignal(str)
    pauseRecordSignal = pyqtSignal(str)
    resumeRecordSignal = pyqtSignal(str)
    writeToFileSignal = pyqtSignal(str, str, str, str)
    renameTabSignal = pyqtSignal()

    def __init__(self, name, connectedPorts: list = None, port: str = "ALL", UUID=None, parent=None):
        super().__init__("Measurement", name, port, UUID, parent)
        self.connectedPorts = connectedPorts
        self.port = port

        self.htsStatus = "Not running"
        self.volt_byte = "23"
        self.htsCounter = 0
        self.htsTimer = QTimer()
        self.htsTimer.setSingleShot(True)

        self.portCombobox = PortCombobox(self.connectedPorts)
        self.portCombobox.activated.connect(self.changeBaudrate)
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

        heatingVoltageLabel = QLabel("Heating voltage")
        self.heatingVoltageCombobox = QComboBox()
        self.heatingVoltageCombobox.addItem("11")
        self.heatingVoltageCombobox.addItem("8,1")
        self.heatingVoltageCombobox.addItem("6,7")
        heatingVoltageLayout = QHBoxLayout()
        heatingVoltageLayout.addWidget(heatingVoltageLabel)
        heatingVoltageLayout.addWidget(self.heatingVoltageCombobox)
        heatingVoltageLayout.addStretch()

        # __________ Send Byte Group Box __________
        sendByteLabel = QPushButton("Send byte")
        sendByteLabel.pressed.connect(self.sendSingleByte)
        self.sendByteLineEdit = QLineEdit("24")
        self.sendByteLineEdit.setFixedWidth(40)
        self.sendByteLineEdit.setInputMask("HH")

        sendByteLayout = QHBoxLayout()
        sendByteLayout.addStretch()
        sendByteLayout.addWidget(sendByteLabel)
        sendByteLayout.addWidget(self.sendByteLineEdit)

        # __________ Transmitted Text Group Box __________
        self.normalHTSRB = QRadioButton("normal HTS")
        self.oneshotHTSRB = QRadioButton("oneshot HTS")
        self.calibHTSRB = QRadioButton("calib HTS")
        self.shortHTSRB = QRadioButton("short HTS")
        htsModeGroup = QButtonGroup()
        htsModeGroup.addButton(self.normalHTSRB)
        htsModeGroup.addButton(self.oneshotHTSRB)
        htsModeGroup.addButton(self.calibHTSRB)
        htsModeGroup.addButton(self.shortHTSRB)
        self.normalHTSRB.setChecked(True)

        htsModeLayout = QVBoxLayout()
        htsModeLayout.addWidget(self.normalHTSRB)
        htsModeLayout.addWidget(self.oneshotHTSRB)
        htsModeLayout.addWidget(self.calibHTSRB)
        htsModeLayout.addWidget(self.shortHTSRB)

        oneShotNumberLabel = QLabel("Oneshot number")
        self.oneShotNumberSB = QSpinBox()
        self.oneShotNumberSB.setValue(3)
        oneShotNumberLayout = QHBoxLayout()
        oneShotNumberLayout.addWidget(oneShotNumberLabel)
        oneShotNumberLayout.addWidget(self.oneShotNumberSB)
        oneShotNumberLayout.addStretch()

        heatingTimeLabel = QLabel("Heating time")
        self.heatingTimeSB = QSpinBox()
        self.heatingTimeSB.setRange(0, 100000)
        self.heatingTimeSB.setValue(180)
        heatingTimeUnitLabel = QLabel("s")
        heatingTimeLayout = QHBoxLayout()
        heatingTimeLayout.addWidget(heatingTimeLabel)
        heatingTimeLayout.addWidget(self.heatingTimeSB)
        heatingTimeLayout.addWidget(heatingTimeUnitLabel)
        heatingTimeLayout.addStretch()

        waitingTimeLabel = QLabel("Waiting time")
        self.waitingTimeSB = QSpinBox()
        self.waitingTimeSB.setRange(0, 100000)
        self.waitingTimeSB.setValue(180)
        waitingTimeUnitLabel = QLabel("s")
        waitingTimeLayout = QHBoxLayout()
        waitingTimeLayout.addWidget(waitingTimeLabel)
        waitingTimeLayout.addWidget(self.waitingTimeSB)
        waitingTimeLayout.addWidget(waitingTimeUnitLabel)
        waitingTimeLayout.addStretch()

        self.htsStatusLabel = QLabel("Not running")

        self.htsStartbutton = QPushButton("Test Button")
        self.htsStartbutton.clicked.connect(self.start_HTS_Mode)

        self.loggingFilePath = os.getcwd()
        self.filePathLineEdit = QLineEdit()
        self.filePathLineEdit.setReadOnly(True)
        self.filePathLineEdit.setPlaceholderText(self.loggingFilePath)
        self.fileNameLineEdit = QLineEdit()
        self.fileNameLineEdit.setPlaceholderText("filename")
        self.openFilePathDialogButton = QPushButton()
        self.openFilePathDialogButton.setIcon(QIcon(resource_path("res/Icon/folder.ico")))
        self.openFilePathDialogButton.clicked.connect(self.getNewFilePath)
        self.fileAutoTimeCB = QCheckBox("add date/time")
        self.fileAutoTimeCB.setChecked(True)

        fileSaveLayout = QGridLayout()
        fileSaveLayout.addWidget(self.filePathLineEdit, 0, 2)
        fileSaveLayout.addWidget(self.openFilePathDialogButton, 0, 1)
        fileSaveLayout.addWidget(self.fileNameLineEdit, 1, 2)
        fileSaveLayout.addWidget(self.fileAutoTimeCB, 1, 0, 1, 2)

        optionsLayout = QHBoxLayout()
        optionsLayout.addWidget(self.portCombobox)
        optionsLayout.addWidget(self.baudrateCombobox)
        optionsLayout.addStretch()

        self.startLoggingButton = QPushButton("Start HTS")
        self.startLoggingButton.pressed.connect(self.start_HTS_Mode)
        self.stopLoggingButton = QPushButton("Stop HTS")
        self.stopLoggingButton.pressed.connect(self.stopHTSMode)
        options2Layout = QHBoxLayout()
        options2Layout.addStretch()
        options2Layout.addLayout(fileSaveLayout)
        options2Layout.addSpacing(10)
        recordHTSLayout = QVBoxLayout()
        recordHTSLayout.addWidget(self.startLoggingButton)
        recordHTSLayout.addWidget(self.stopLoggingButton)
        options2Layout.addLayout(recordHTSLayout)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(optionsLayout)
        mainLayout.addStretch()
        mainLayout.addLayout(sendByteLayout)
        mainLayout.addLayout(htsModeLayout)
        mainLayout.addSpacing(10)
        mainLayout.addLayout(heatingVoltageLayout)
        mainLayout.addLayout(heatingTimeLayout)
        mainLayout.addLayout(waitingTimeLayout)
        mainLayout.addLayout(oneShotNumberLayout)
        mainLayout.addStretch()
        mainLayout.addLayout(options2Layout)

        self.setLayout(mainLayout)

        self.initUI()

    def initUI(self):
        if self.port == "COM-ALL":
            return
        if self.portCombobox.findText(self.port) != -1:
            self.portCombobox.setCurrentText(self.port)
            self.portCombobox.lastText = self.port
            self.changeBaudrate()

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

    def getNewFilePath(self):
        filePath = QFileDialog.getExistingDirectory(None, "Select Folder", "",
                                                    QFileDialog.DontUseNativeDialog | QFileDialog.ShowDirsOnly)
        if filePath:
            self.loggingFilePath = filePath
            self.filePathLineEdit.setText(filePath)

    def nextHTSStatus(self, time_s: float = 0, newStatus: str = "", statusLabelText: str = ""):
        self.htsStatus = newStatus
        if statusLabelText != "":
            self.htsStatusLabel.setText(statusLabelText)
        if time_s == 0:
            self.start_HTS_Mode()
        else:
            self.htsTimer.singleShot(int(time_s * 1000), self.start_HTS_Mode)

    def start_HTS_Mode(self):
        if self.htsStatus == "Not running":
            self.htsStartbutton.setDisabled(True)
            self.volt_byte = '23'
            if self.heatingVoltageCombobox.currentText() == '11':
                self.volt_byte = '20'
            elif self.heatingVoltageCombobox.currentText() == '8,1':
                self.volt_byte = '21'
            elif self.heatingVoltageCombobox.currentText() == '6,7':
                self.volt_byte = '22'
            else:
                print('Fehler bei der Voltauswahl')

            if self.oneshotHTSRB.isChecked():
                self.nextHTSStatus(0, "oneshot begin", "measurement started")
            elif self.shortHTSRB.isChecked():
                self.nextHTSStatus(0, "short begin", "measurement started")
            elif self.normalHTSRB.isChecked():
                self.nextHTSStatus(0, "normal begin", "measurement started")
            elif self.calibHTSRB.isChecked():
                self.nextHTSStatus(0, "calib begin", "measurement started")

        elif self.htsStatus == "oneshot begin":
            self.sendDataInBytes('23')
            self.startRecording()
            self.nextHTSStatus(0.25, "oneshot begin 2")
        elif self.htsStatus == "oneshot begin 2":
            self.sendDataInBytes('25')
            self.htsCounter = 0
            self.nextHTSStatus(0, "oneshot loop")
        elif self.htsStatus == "oneshot loop":
            if self.htsCounter < self.oneShotNumberSB.value():
                self.sendDataInBytes('23')
                self.nextHTSStatus(self.waitingTimeSB.value(), "oneshot loop 2", "measurement started: " + str(self.htsCounter))
            else:
                self.nextHTSStatus(0, "stopping hts 1")
        elif self.htsStatus == "oneshot loop 2":
            self.sendDataInBytes(str(self.volt_byte))
            self.nextHTSStatus(self.heatingTimeSB.value(), "oneshot loop 3", "heating: " + str(self.htsCounter))
        elif self.htsStatus == "oneshot loop 3":
            self.htsCounter += 1
            self.nextHTSStatus(0, "oneshot loop")

        elif self.htsStatus == "short begin":
            self.sendDataInBytes('24')
            self.nextHTSStatus(2, "short begin 2")
        elif self.htsStatus == "short begin 2":
            self.sendDataInBytes(str(self.volt_byte))
            self.nextHTSStatus(2, "short begin 3")
        elif self.htsStatus == "short begin 3":
            self.sendDataInBytes('24')
            self.nextHTSStatus(0, "short loop")
        elif self.htsStatus == "short loop":
            self.sendDataInBytes('24')
            self.nextHTSStatus(self.waitingTimeSB.value(), "short loop 2", "measurement started")
        elif self.htsStatus == "short loop 2":
            self.sendDataInBytes('25')
            self.nextHTSStatus(self.heatingTimeSB.value(), "short loop", "heating")

        elif self.htsStatus == "normal begin":
            self.sendDataInBytes('24')
            self.nextHTSStatus(0.25, "normal begin 2", "measurement started")
        elif self.htsStatus == "normal begin 2":
            self.sendDataInBytes(str(self.volt_byte))
            self.nextHTSStatus(0.25, "normal loop")
        elif self.htsStatus == "normal loop":
            self.sendDataInBytes('24')
            self.nextHTSStatus(self.waitingTimeSB.value(), "normal loop 2", "measurement started")
        elif self.htsStatus == "normal loop 2":
            self.sendDataInBytes('25')
            self.nextHTSStatus(0.25, "normal loop 3")
        elif self.htsStatus == "normal loop 3":
            self.sendDataInBytes('23')
            self.nextHTSStatus(self.waitingTimeSB.value(), "normal loop 4")
        elif self.htsStatus == "normal loop 4":
            self.sendDataInBytes(str(self.volt_byte))
            self.nextHTSStatus(self.heatingTimeSB.value(), "normal loop", "heating")

        elif self.htsStatus == "calib begin":
            self.startRecording()
            self.pauseRecording()
            self.nextHTSStatus(1800, "calib begin 2", "wait 30 min")
        elif self.htsStatus == "calib begin 2":
            self.sendDataInBytes('23')
            self.nextHTSStatus(1, "calib begin 3", "measurement started")
        elif self.htsStatus == "calib begin 3":
            self.writeToFile("-----Start 8,1V Messung------\n")
            self.sendDataInBytes('25')
            self.resumeRecording()
            self.htsCounter = 0
            self.nextHTSStatus(1, "calib loop 1")
        elif self.htsStatus == "calib loop 1":
            if self.htsCounter < 3:
                self.sendDataInBytes('23')
                self.nextHTSStatus(180, "calib loop 2", "measurement started")
            else:
                self.nextHTSStatus(0, "calib middle")
        elif self.htsStatus == "calib loop 2":
            self.sendDataInBytes('21')
            self.htsCounter += 1
            self.nextHTSStatus(180, "calib loop 1", "heating at 8,1 V")
        elif self.htsStatus == "calib middle":
            self.pauseRecording()
            self.sendDataInBytes('23')
            self.writeToFile("-----Start 11V Messung------\n")
            self.resumeRecording()
            self.sendDataInBytes('25')
            self.htsCounter = 0
            self.nextHTSStatus(180, "calib loop 3")
        elif self.htsStatus == "calib loop 3":
            if self.htsCounter < 3:
                self.sendDataInBytes('23')
                self.nextHTSStatus(240, "calib loop 4", "measurement started")
            else:
                self.nextHTSStatus(0, "stopping hts 1")
        elif self.htsStatus == "calib loop 4":
            self.sendDataInBytes('20')
            self.htsCounter += 1
            self.nextHTSStatus(240, "calib loop 3", "heating at 11 V")

        elif self.htsStatus == "stopping hts 1":
            self.stopRecording()
            self.sendDataInBytes('23')
            self.nextHTSStatus(2, "stopping hts 2")
        elif self.htsStatus == "stopping hts 2":
            self.sendDataInBytes('24')
            self.htsStatusLabel.setText("measurement ended")
            self.htsStatus = "Not running"
            self.htsStartbutton.setEnabled(True)

    def stopHTSMode(self):
        self.htsTimer.stop()
        self.htsStatus = "stopping hts 1"
        self.start_HTS_Mode()

    def startRecording(self):
        if self.fileAutoTimeCB.isChecked() or self.fileNameLineEdit.text() == "":
            fileName = self.fileNameLineEdit.text() + datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + ".txt"
        else:
            fileName = self.fileNameLineEdit.text() + ".txt"
        if self.portCombobox.currentText() == "COM-ALL":
            self.startRecordSignal.emit("ALL", self.loggingFilePath, fileName)
        else:
            self.startRecordSignal.emit(self.portCombobox.currentText(), self.loggingFilePath, fileName)

    def stopRecording(self):
        if self.portCombobox.currentText() == "COM-ALL":
            self.stopRecordSignal.emit("ALL")
        else:
            self.stopRecordSignal.emit(self.portCombobox.currentText())

    def pauseRecording(self):
        if self.portCombobox.currentText() == "COM-ALL":
            self.pauseRecordSignal.emit("ALL")
        else:
            self.pauseRecordSignal.emit(self.portCombobox.currentText())

    def resumeRecording(self):
        if self.portCombobox.currentText() == "COM-ALL":
            self.resumeRecordSignal.emit("ALL")
        else:
            self.resumeRecordSignal.emit(self.portCombobox.currentText())

    def writeToFile(self, text):
        if self.portCombobox.currentText() == "COM-ALL":
            self.writeToFileSignal.emit(text, "ALL", "", "")
        else:
            self.writeToFileSignal.emit(text, self.portCombobox.currentText(), "", "")

    def receiveData(self, obj: SerialParameters, data):
        pass

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
            if os.path.isdir(tempSettings["loggingFilePath"]):
                self.filePathLineEdit.setText(tempSettings["loggingFilePath"])
                self.loggingFilePath = tempSettings["loggingFilePath"]
            self.fileNameLineEdit.setText(tempSettings["loggingFileName"])
            self.fileAutoTimeCB.setChecked(tempSettings["autoTimeChecked"])
            self.heatingVoltageCombobox.setCurrentText(tempSettings["heatingVoltage"])
            self.normalHTSRB.setChecked(tempSettings["normalHTS"])
            self.oneshotHTSRB.setChecked(tempSettings["oneshotHTS"])
            self.calibHTSRB.setChecked(tempSettings["calibHTS"])
            self.shortHTSRB.setChecked(tempSettings["shortHTS"])
            self.oneShotNumberSB.setValue(tempSettings["oneShotNumber"])
            self.heatingTimeSB.setValue(tempSettings["heatingTime"])
            self.waitingTimeSB.setValue(tempSettings["waitingTime"])

    def saveSettings(self, settings: QSettings = None):
        tempSettings = {"port": self.portCombobox.currentText(),
                        "baud": self.baudrateCombobox.currentText(),
                        "loggingFilePath": self.filePathLineEdit.text(),
                        "loggingFileName": self.fileNameLineEdit.text(),
                        "autoTimeChecked": self.fileAutoTimeCB.isChecked(),
                        "heatingVoltage": self.heatingVoltageCombobox.currentText(),
                        "normalHTS": self.normalHTSRB.isChecked(),
                        "oneshotHTS": self.oneshotHTSRB.isChecked(),
                        "calibHTS": self.calibHTSRB.isChecked(),
                        "shortHTS": self.shortHTSRB.isChecked(),
                        "oneShotNumber": self.oneShotNumberSB.value(),
                        "heatingTime": self.heatingTimeSB.value(),
                        "waitingTime": self.waitingTimeSB.value()
                        }
        settings.setValue(self.uuid, tempSettings)

    def sendData(self, data):
        if self.portCombobox.currentText() == "COM-ALL":
            self.sendSerialWriteSignal.emit("ALL", data)
        else:
            self.sendSerialWriteSignal.emit(self.portCombobox.currentText(), data)

    def sendDataInBytes(self, data):
        self.sendData(binascii.unhexlify(data))

    def sendSingleByte(self):
        if len(self.sendByteLineEdit.text()) == 0:
            self.sendByteLineEdit.setText("00")
        elif len(self.sendByteLineEdit.text()) == 1:
            self.sendByteLineEdit.setText("0" + self.sendByteLineEdit.text())
        self.sendData(binascii.unhexlify(self.sendByteLineEdit.text()))
