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
from CalculationWidget import CalculationWidget


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


class CalibrationPortCombobox(QComboBox):
    def __init__(self, connectedPorts: list):
        super().__init__()
        self.connectedPorts = connectedPorts

        for p in self.connectedPorts:
            self.addItem(p.port)
        self.adjustSize()
        self.activated.connect(self.handleActivated)

    def showPopup(self):
        for p in self.connectedPorts:
            if self.findText(p.port) < 0:
                self.addItem(p.port)
        super().showPopup()

    def handleActivated(self, index):
        pass


class VarCalculator(Tab):
    sendSerialWriteSignal = pyqtSignal(str, object)
    startRecordSignal = pyqtSignal(str, str, str)
    stopRecordSignal = pyqtSignal(str)
    renameTabSignal = pyqtSignal()

    def __init__(self, name, connectedPorts: list = None, port: str = "ALL", UUID=None, parent=None):
        super().__init__("VarCalculator", name, port, UUID, parent)

        self.connectedPorts = connectedPorts
        self.port = port

        self.vars = []
        self.varNames = []

        self.calibrations = []
        self.receivedValueData = []

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

        self.addCalculationButton = QPushButton("Add calculation")
        self.addCalculationButton.clicked.connect(self.addCalculationButtonPressed)
        frequencyLabel = QLabel("Calculation frequency:")
        self.timerCombobox = QComboBox()
        self.timerCombobox.addItem("If new data")
        self.timerCombobox.addItem("1 Hz")
        self.timerCombobox.addItem("2 Hz")
        self.timerCombobox.addItem("5 Hz")
        self.timerCombobox.addItem("10 Hz")
        self.timerCombobox.setCurrentText("If new data")
        self.timerCombobox.activated.connect(self.changeTimer)

        self.calculateTimer = QTimer()
        self.calculateTimer.timeout.connect(self.calculateTimerTimeout)

        optionsLayout = QHBoxLayout()
        optionsLayout.addWidget(self.portCombobox)
        optionsLayout.addWidget(self.baudrateCombobox)
        optionsLayout.addStretch()
        optionsLayout.addWidget(self.addCalculationButton)
        optionsLayout.addStretch()
        optionsLayout.addWidget(frequencyLabel)
        optionsLayout.addWidget(self.timerCombobox)

        self.table = QTableWidget(1, 0)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        header = self.table.verticalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)

        self.channelTable = QTableWidget(0, 2)
        self.channelTable.horizontalHeader().hide()
        self.channelTable.verticalHeader().hide()
        self.channelTable.setColumnWidth(0, int(self.channelTable.width() / 2) - 1)
        self.channelTable.setColumnWidth(1, int(self.channelTable.width() / 2) - 1)
        header = self.channelTable.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        splitter1H = QSplitter(Qt.Horizontal)
        splitter1H.addWidget(self.table)
        splitter1H.addWidget(self.channelTable)
        splitter1H.setHandleWidth(10)
        splitter1H.moveSplitter(200, 1)

        splitterLayout = QHBoxLayout()
        splitterLayout.addWidget(splitter1H)

        self.calibrationPortCombobox = CalibrationPortCombobox(self.connectedPorts)
        self.calibrationPortCombobox.activated.connect(self.changeCalibrationPort)
        self.loadCalibrationButton = QPushButton("Import Calibration File", self)
        self.loadCalibrationButton.clicked.connect(self.calibrationButtonPressed)
        self.loadCalibrationText = CalibrationFileLabel("No File loaded", self)
        self.loadCalibrationText.setStyleSheet("color: #808080")

        options2Layout = QHBoxLayout()
        options2Layout.addWidget(self.calibrationPortCombobox)
        options2Layout.addWidget(self.loadCalibrationButton)
        options2Layout.addWidget(self.loadCalibrationText)
        options2Layout.addStretch()

        mainLayout = QGridLayout()
        mainLayout.addLayout(optionsLayout, 0, 0)
        mainLayout.addLayout(splitterLayout, 1, 0)
        mainLayout.addLayout(options2Layout, 2, 0)
        mainLayout.setRowStretch(1, 2)

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

    def changeCalibrationPort(self):
        if self.calibrationPortCombobox.currentText() == "":
            self.loadCalibrationText.setText("No File loaded")

        portFound = False
        for calibration in self.calibrations:
            if calibration.port == self.calibrationPortCombobox.currentText():
                self.loadCalibrationText.setText(calibration.fileName)
                portFound = True

        if not portFound:
            self.loadCalibrationText.setText("No File loaded")

    def changeTimer(self):
        if self.timerCombobox.currentText() == "If new data":
            self.calculateTimer.stop()
        elif self.timerCombobox.currentText() == "1 Hz":
            self.calculateTimer.start(1000)
        elif self.timerCombobox.currentText() == "2 Hz":
            self.calculateTimer.start(500)
        elif self.timerCombobox.currentText() == "5 Hz":
            self.calculateTimer.start(200)
        elif self.timerCombobox.currentText() == "10 Hz":
            self.calculateTimer.start(100)

    def addColumn(self):
        self.table.insertColumn(self.table.columnCount())
        self.table.setCellWidget(0, self.table.columnCount() - 1, CalculationWidget(self.varNames, self.vars, self))

    def addRow(self, varName: str, varValue: float):
        self.channelTable.insertRow(self.channelTable.rowCount())
        self.channelTable.setItem(self.channelTable.rowCount() - 1, 0, QTableWidgetItem(varName))
        self.channelTable.setItem(self.channelTable.rowCount() - 1, 1, QTableWidgetItem("%.2f" % varValue))

    def calibrationButtonPressed(self):
        if self.calibrationPortCombobox.currentText() == "":
            return

        fileName = QFileDialog.getOpenFileName(None, "Open Calibration File", os.getcwd(), "csv(*.csv)\nall(*.*)", "",
                                               QFileDialog.DontUseNativeDialog)

        if fileName[0] == "":
            return None

        portFound = False
        for calibration in self.calibrations:
            if calibration.port == self.calibrationPortCombobox.currentText():
                portFound = True
                if calibration.readCalibrationFile(fileName[0]) is None:
                    print("Error at loading calibration file")
                    return
                self.loadCalibrationText.setText(calibration.fileName)
        if not portFound:
            tempCalibration = CalibrationOfData()
            tempCalibration.port = self.calibrationPortCombobox.currentText()
            if tempCalibration.readCalibrationFile(fileName[0]) is None:
                print("Error at loading calibration file")
                return
            self.calibrations.append(tempCalibration)
            self.loadCalibrationText.setText(tempCalibration.fileName)

    def dragLabelActivated(self):
        for calibration in self.calibrations:
            if calibration.port == self.calibrationPortCombobox.currentText():
                return {"port": calibration.port, "path": calibration.pathName}
        return {"port": None, "path": None}

    def dropLabelActivated(self, obj):
        if obj["path"] is None:
            return
        if obj["port"] is None:
            if self.calibrationPortCombobox.currentText() != "":
                self.loadCalibrationsFromSaveOptions(self.calibrationPortCombobox.currentText(), obj["path"])
        else:
            self.loadCalibrationsFromSaveOptions(obj["port"], obj["path"])

    def addCalculationButtonPressed(self):
        self.addColumn()
        self.table.resizeColumnsToContents()

    def resizeTableColumns(self):
        self.table.resizeColumnsToContents()

    def closeCalculationWidget(self, ID: str):
        index = -1
        for columnCount in range(0, self.table.columnCount()):
            if self.table.cellWidget(0, columnCount).uuid == ID:
                index = columnCount

        if index >= 0:
            self.table.removeColumn(index)

    def receiveData(self, obj: SerialParameters, data):
        if self.portCombobox.currentText() != obj.port and self.portCombobox.currentText() != "COM-ALL":
            return
        if self.baudrateCombobox.currentText() != str(
                obj.baudrate) + " Baud" and self.baudrateCombobox.currentText() != "ALL Baud":
            return

        if obj.readTextIndex == "read_WU_device":
            calibration = None
            for tempCalibration in self.calibrations:
                if tempCalibration.port == obj.port and tempCalibration.configured:
                    calibration = tempCalibration

            if not calibration:
                return

            self.receivedValueData = []
            for numberIndex in range(0, len(data)):
                self.receivedValueData.append(int(data[numberIndex], 16))

            self.receivedCalValueData = calibration.calibrate(self.receivedValueData)

            for calDataCounter in range(0, len(self.receivedCalValueData)):
                tempName = calibration.port + '_CH' + str(calDataCounter) + "_" + calibration.getName(calDataCounter)
                tempValue = self.receivedCalValueData[calDataCounter]
                if tempName not in self.varNames:
                    self.varNames.append(tempName)
                    self.vars.append(tempValue)
                    self.addRow(tempName, tempValue)
                else:
                    tempIndex = self.varNames.index(tempName)
                    self.vars[tempIndex] = tempValue
                    self.channelTable.item(tempIndex, 1).setText("%.2f" % tempValue)

            if self.timerCombobox.currentText() == "If new data":
                for columnCount in range(0, self.table.columnCount()):
                    self.table.cellWidget(0, columnCount).calculate()

            self.channelTable.resizeColumnsToContents()

    def calculateTimerTimeout(self):
        for columnCount in range(0, self.table.columnCount()):
            self.table.cellWidget(0, columnCount).calculate()

    def closeEvent(self, event):
        pass

    def loadCalcWidget(self, options):
        self.table.insertColumn(self.table.columnCount())
        self.table.setCellWidget(0, self.table.columnCount() - 1, CalculationWidget(self.varNames, self.vars, self))
        self.table.cellWidget(0, self.table.columnCount() - 1).calculationTypeCombobox.setCurrentText(options["name"])
        self.table.cellWidget(0, self.table.columnCount() - 1).changeCalculationType()
        self.table.cellWidget(0, self.table.columnCount() - 1).load(options["option"])
        self.resizeTableColumns()

    def applySettings(self, settings: QSettings = None):
        if settings.contains(self.uuid):
            tempSettings = settings.value(self.uuid)
            if self.portCombobox.findText(tempSettings["port"]) == -1:
                self.portCombobox.addItem(tempSettings["port"])
            self.portCombobox.lastText = tempSettings["port"]
            self.portCombobox.setCurrentText(tempSettings["port"])
            self.changeTabName()
            self.baudrateCombobox.setCurrentText(tempSettings["baud"])
            self.timerCombobox.setCurrentText(tempSettings["calcFrequency"])
            for calibrationOption in tempSettings["calibrationOptions"]:
                self.loadCalibrationsFromSaveOptions(calibrationOption[0], calibrationOption[1])
            for option in tempSettings["calcWidgets"]:
                self.loadCalcWidget(option)

    def saveSettings(self, settings: QSettings = None):
        calibrationOptions = []
        for calibration in self.calibrations:
            calibrationOptions.append([calibration.port, calibration.pathName])

        calcWidgets = []
        for columnCount in range(0, self.table.columnCount()):
            option = {"name": self.table.cellWidget(0, columnCount).calculationTypeCombobox.currentText(),
                      "option": self.table.cellWidget(0, columnCount).save()}
            calcWidgets.append(option)

        tempSettings = {"port": self.portCombobox.currentText(),
                        "baud": self.baudrateCombobox.currentText(),
                        "calibrationOptions": calibrationOptions,
                        "calcWidgets": calcWidgets,
                        "calcFrequency": self.timerCombobox.currentText()}
        settings.setValue(self.uuid, tempSettings)

    def loadCalibrationsFromSaveOptions(self, port, path):
        if not os.path.exists(path):
            return
        if path[0] == "":
            return None

        portFound = False
        for calibration in self.calibrations:
            if calibration.port == port:
                portFound = True
                if calibration.readCalibrationFile(path) is None:
                    print("Error at loading calibration file")
                    return
                self.loadCalibrationText.setText(calibration.fileName)
                if self.calibrationPortCombobox.findText(port) < 0:
                    self.calibrationPortCombobox.addItem(port)
                    self.calibrationPortCombobox.setCurrentText(port)
                else:
                    self.calibrationPortCombobox.setCurrentText(port)
        if not portFound:
            tempCalibration = CalibrationOfData()
            tempCalibration.port = port
            if tempCalibration.readCalibrationFile(path) is None:
                print("Error at loading calibration file")
                return
            if self.calibrationPortCombobox.findText(port) < 0:
                self.calibrationPortCombobox.addItem(port)
                self.calibrationPortCombobox.setCurrentText(port)
            else:
                self.calibrationPortCombobox.setCurrentText(port)
            self.calibrations.append(tempCalibration)
            self.loadCalibrationText.setText(tempCalibration.fileName)

    def sendData(self):
        data = "TEST DATA".encode('utf-8')
        if self.portCombobox.currentText() == "COM-ALL":
            self.sendSerialWriteSignal.emit("ALL", data)
        else:
            self.sendSerialWriteSignal.emit(self.portCombobox.currentText(), data)
