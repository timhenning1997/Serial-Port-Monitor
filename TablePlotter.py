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


class TablePlotter(Tab):
    sendSerialWriteSignal = pyqtSignal(str, object)
    startRecordSignal = pyqtSignal(str, str, str)
    stopRecordSignal = pyqtSignal(str)
    renameTabSignal = pyqtSignal()

    def __init__(self, name, connectedPorts: list = None, port: str = "ALL", UUID=None, parent=None):
        super().__init__("TablePlotter", name, port, UUID, parent)

        self.color1 = QColor(26, 26, 26)
        self.color2 = QColor(77, 0, 0)
        self.colorScale = spectra.scale([self.color1.name(), self.color2.name()]).domain([0, 65535])

        self.loggingFilePath = os.getcwd()

        self.calibration = CalibrationOfData()
        self.receivedData = []
        self.receivedValueData = []
        self.receivedCalValueData = []
        self.maxRefreshRate = 10  # Hz
        self.lastRefreshTime = 0
        self.currentLengthOfData = 0

        self.connectedPorts = connectedPorts
        self.port = port

        self.shownType = "Hex"

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

        self.kennbinCombobox = QComboBox()
        self.kennbinCombobox.addItem("ALL Kennbin")
        self.kennbinCombobox.setCurrentText("ALL Kennbin")
        self.kennbinCombobox.setEditable(True)

        self.colorPicker1Button = QPushButton("")
        self.colorPicker1Button.setFixedWidth(20)
        self.colorPicker1Button.setStyleSheet("background-color : " + self.color1.name())
        self.colorPicker1Button.clicked.connect(self.colorPicker1)
        self.colorPicker1Button.setContentsMargins(0, 0, 0, 0)
        self.colorPicker2Button = QPushButton("")
        self.colorPicker2Button.setFixedWidth(20)
        self.colorPicker2Button.setStyleSheet("background-color : " + self.color2.name())
        self.colorPicker2Button.clicked.connect(self.colorPicker2)
        self.colorPicker2Button.setContentsMargins(0, 0, 0, 0)

        colorOptionsLayout = QHBoxLayout()
        colorOptionsLayout.setContentsMargins(0, 0, 0, 0)
        colorOptionsLayout.setSpacing(1)
        colorOptionsLayout.addWidget(self.colorPicker1Button)
        colorOptionsLayout.addWidget(self.colorPicker2Button)

        addColumnButton = QPushButton("+ Column")
        addColumnButton.clicked.connect(self.addColumn)
        deleteColumnButton = QPushButton("- Column")
        deleteColumnButton.clicked.connect(self.deleteLastColumn)

        optionsLayout = QHBoxLayout()
        optionsLayout.addWidget(self.portCombobox)
        optionsLayout.addWidget(self.baudrateCombobox)
        optionsLayout.addWidget(self.kennbinCombobox)
        optionsLayout.addStretch()
        optionsLayout.addLayout(colorOptionsLayout)
        optionsLayout.addStretch()
        optionsLayout.addWidget(deleteColumnButton)
        optionsLayout.addWidget(addColumnButton)

        self.dataCounterLabel = QLabel("Data couter")
        self.dataCounterLabel.setFixedWidth(200)

        self.shownTypeCB = QComboBox()
        self.shownTypeCB.addItem("Show: Hex")
        self.shownTypeCB.addItem("Show: Values")
        self.shownTypeCB.addItem("Show: cal. Values")
        self.shownTypeCB.currentTextChanged.connect(self.changeShownType)

        options2Layout = QHBoxLayout()
        options2Layout.addWidget(self.dataCounterLabel)
        options2Layout.addStretch()
        options2Layout.addWidget(self.shownTypeCB)
        options2Layout.addStretch()

        self.colNumber = 8
        self.table = QTableWidget(0, 0)
        self.resizeTable(0, self.colNumber)

        self.loadCalibrationButton = QPushButton("Import Calibration File", self)
        self.loadCalibrationButton.clicked.connect(self.calibrationButtonPressed)
        self.loadCalibrationText = CalibrationFileLabel("No File loaded", self)
        self.loadCalibrationText.setStyleSheet("color: #808080")

        self.loggingCheckbox = QCheckBox("Logging")
        self.loggingCheckbox.adjustSize()
        self.loggingCheckbox.stateChanged.connect(self.btnstate)

        self.startLoggingButton = QPushButton("Start logging")
        self.startLoggingButton.pressed.connect(self.startRecording)
        self.stopLoggingButton = QPushButton("Stop logging")
        self.stopLoggingButton.pressed.connect(self.stopRecording)

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

        options3Layout = QHBoxLayout()
        options3Layout.addWidget(self.loadCalibrationButton)
        options3Layout.addWidget(self.loadCalibrationText)
        options3Layout.addStretch()
        options3Layout.addLayout(fileSaveLayout)
        options3Layout.addSpacing(10)
        # options3Layout.addWidget(self.loggingCheckbox)

        vLoggingLayout = QVBoxLayout()
        vLoggingLayout.addWidget(self.startLoggingButton)
        vLoggingLayout.addWidget(self.stopLoggingButton)
        options3Layout.addLayout(vLoggingLayout)

        mainLayout = QGridLayout()
        mainLayout.addLayout(optionsLayout, 0, 0)
        mainLayout.addLayout(options2Layout, 1, 0)
        mainLayout.addWidget(self.table, 2, 0)
        mainLayout.addLayout(options3Layout, 3, 0)

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

    def resizeTable(self, rowCount: int, columnCount: int):
        if rowCount == 0:
            rowCount = int(math.ceil(len(self.receivedData[1:]) / columnCount))

        self.colNumber = columnCount
        self.changeTableSize(rowCount, columnCount)
        self.changeTableHeaderLabels()
        self.changeTableColumnWidth(90)

        for countY in range(0, self.table.rowCount()):
            for countX in range(0, self.table.columnCount()):
                tableContendIndex = countY * (self.table.columnCount()) + countX
                if len(self.receivedData[1:]) > tableContendIndex:
                    if self.receivedCalValueData and self.shownType == "cal. Values" and \
                            self.calibration.configured and len(self.receivedCalValueData[1:]) > tableContendIndex:
                        self.table.setItem(countY, countX,
                                           QTableWidgetItem("%.2f" % self.receivedCalValueData[1:][tableContendIndex]))
                    elif self.shownType == "Hex":
                        self.table.setItem(countY, countX, QTableWidgetItem(self.receivedData[1:][tableContendIndex]))
                    elif self.shownType == "Values":
                        self.table.setItem(countY, countX, QTableWidgetItem(str(self.receivedValueData[1:][tableContendIndex])))
                    else:
                        self.table.setItem(countY, countX, QTableWidgetItem(""))

                    number = int(self.receivedData[1:][tableContendIndex], 16)
                    self.table.item(countY, countX).setBackground(QColor(self.colorScale(number).hexcode))
                else:
                    self.table.setItem(countY, countX, QTableWidgetItem(""))
                self.table.item(countY, countX).setTextAlignment(Qt.AlignCenter)

    def changeTableSize(self, rowCount: int, columnCount: int):
        self.table.setRowCount(rowCount)
        self.table.setColumnCount(columnCount)

    def clearTable(self, dataLength: int = 0):
        counter = 0
        for countY in range(0, self.table.rowCount()):
            for countX in range(0, self.table.columnCount()):
                self.table.item(countY, countX).setBackground(QColor(Qt.transparent))
                if counter >= dataLength:
                    self.table.item(countY, countX).setText("")
                counter += 1

    def changeTableHeaderLabels(self):
        verticalHeaderLabels = []
        for count in range(0, self.table.rowCount()):
            verticalHeaderLabels.append("AN " + str(count))
        self.table.setVerticalHeaderLabels(verticalHeaderLabels)
        horizontalHeaderLabels = []
        for count in range(0, self.table.columnCount()):
            horizontalHeaderLabels.append("CH " + str(count))
        self.table.setHorizontalHeaderLabels(horizontalHeaderLabels)

    def changeTableColumnWidth(self, width):
        for count in range(0, self.table.columnCount()):
            self.table.setColumnWidth(count, width)

    def addColumn(self):
        self.resizeTable(0, self.table.columnCount() + 1)

    def deleteLastColumn(self):
        if self.table.columnCount() > 1:
            self.resizeTable(0, self.table.columnCount() - 1)

    def colorPicker1(self):
        color = QColorDialog.getColor().name()
        self.colorPicker1Button.setStyleSheet("background-color : " + color)
        self.color1 = QColor(color)
        self.colorScale = spectra.scale([self.color1.name(), self.color2.name()]).domain([0, 65535])

    def colorPicker2(self):
        color = QColorDialog.getColor().name()
        self.colorPicker2Button.setStyleSheet("background-color : " + color)
        self.color2 = QColor(color)
        self.colorScale = spectra.scale([self.color1.name(), self.color2.name()]).domain([0, 65535])

    def getNewFilePath(self):
        filePath = QFileDialog.getExistingDirectory(None, "Select Folder", "",
                                                    QFileDialog.DontUseNativeDialog | QFileDialog.ShowDirsOnly)
        # filePath = QFileDialog.getExistingDirectory(None, "Select Folder", "", QFileDialog.ShowDirsOnly)
        if filePath:
            self.loggingFilePath = filePath
            self.filePathLineEdit.setText(filePath)

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

    def btnstate(self, state):
        if state == Qt.Checked:
            if self.fileAutoTimeCB.isChecked() or self.fileNameLineEdit.text() == "":
                fileName = self.fileNameLineEdit.text() + datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + ".txt"
            else:
                fileName = self.fileNameLineEdit.text() + ".txt"
            if self.portCombobox.currentText() == "COM-ALL":
                self.startRecordSignal.emit("ALL", self.loggingFilePath, fileName)
            else:
                self.startRecordSignal.emit(self.portCombobox.currentText(), self.loggingFilePath, fileName)
        else:
            if self.portCombobox.currentText() == "COM-ALL":
                self.stopRecordSignal.emit("ALL")
            else:
                self.stopRecordSignal.emit(self.portCombobox.currentText())

    def receiveData(self, obj: SerialParameters, data):
        kennbin = binascii.hexlify(obj.Kennbin).decode("utf-8")
        if(self.kennbinCombobox.findText(kennbin) == -1):
            self.kennbinCombobox.addItem(kennbin)
        if self.kennbinCombobox.currentText() != kennbin and \
                self.kennbinCombobox.currentText() != "ALL Kennbin":
            return
        if self.portCombobox.currentText() != obj.port and self.portCombobox.currentText() != "COM-ALL":
            return
        if self.baudrateCombobox.currentText() != str(obj.baudrate) + " Baud" and \
                self.baudrateCombobox.currentText() != "ALL Baud":
            return

        if obj.readTextIndex == "read_WU_device":
            if time.time() > self.lastRefreshTime + (1 / self.maxRefreshRate):
                self.lastRefreshTime = time.time()
                self.receivedData = data
                if len(data[1:]) != self.currentLengthOfData:
                    self.currentLengthOfData = len(data[1:])
                    self.clearTable(len(data[1:]))
                    if int(math.ceil(len(data[1:]) / self.colNumber)) != self.table.rowCount():
                        self.resizeTable(int(math.ceil(len(data[1:]) / self.colNumber)), self.colNumber)

                self.receivedValueData = []
                for numberIndex in range(0, len(data)):
                    self.receivedValueData.append(int(data[numberIndex], 16))

                self.receivedCalValueData = []
                if self.calibration.configured:
                    self.receivedCalValueData = self.calibration.calibrate(self.receivedValueData)

                self.dataCounterLabel.setText(str(int(data[0], 16)))

                temp_data = []
                temp_receivedData = []
                temp_receivedValueData = []
                temp_receivedCalValueData = []
                if len(data) > 1:
                    temp_data = data[1:]
                if len(self.receivedValueData) > 1:
                    temp_receivedValueData = self.receivedValueData[1:]
                if self.receivedCalValueData is not None and len(self.receivedCalValueData) > 1:
                    temp_receivedCalValueData = self.receivedCalValueData[1:]

                for numberIndex in range(0, len(temp_data)):
                    rowCount = numberIndex // self.colNumber
                    colCount = numberIndex % self.colNumber

                    if self.shownType == "Hex":
                        self.table.item(rowCount, colCount).setText(temp_data[numberIndex])
                    elif self.shownType == "Values":
                        self.table.item(rowCount, colCount).setText(str(temp_receivedValueData[numberIndex]))
                    elif self.shownType == "cal. Values":
                        if self.calibration.configured:
                            if numberIndex < len(temp_receivedCalValueData) and temp_receivedCalValueData[numberIndex] is not None:
                                self.table.item(rowCount, colCount).setText(
                                    "%.2f" % temp_receivedCalValueData[numberIndex])
                            else:
                                self.table.item(rowCount, colCount).setText("0")

                    self.table.item(rowCount, colCount).setBackground(
                        QColor(self.colorScale(temp_receivedValueData[numberIndex]).hexcode))

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
            self.kennbinCombobox.setCurrentText(tempSettings["kennbin"])
            self.color1 = QColor(tempSettings["color1"])
            self.colorPicker1Button.setStyleSheet("background-color : " + self.color1.name())
            self.color2 = QColor(tempSettings["color2"])
            self.colorPicker2Button.setStyleSheet("background-color : " + self.color2.name())
            self.colorScale = spectra.scale([self.color1.name(), self.color2.name()]).domain([0, 65535])
            self.resizeTable(0, tempSettings["columnNumber"])
            if os.path.exists(tempSettings["calibrationFilePath"]):
                self.loadCalibrationFromSaveSettings(tempSettings["calibrationFilePath"])
            if os.path.isdir(tempSettings["loggingFilePath"]):
                self.filePathLineEdit.setText(tempSettings["loggingFilePath"])
                self.loggingFilePath = tempSettings["loggingFilePath"]
            self.fileNameLineEdit.setText(tempSettings["loggingFileName"])
            self.fileAutoTimeCB.setChecked(tempSettings["autoTimeChecked"])

    def saveSettings(self, settings: QSettings = None):
        tempSettings = {"port": self.portCombobox.currentText(),
                        "baud": self.baudrateCombobox.currentText(),
                        "kennbin": self.kennbinCombobox.currentText(),
                        "color1": self.color1.name(),
                        "color2": self.color2.name(),
                        "columnNumber": self.colNumber,
                        "calibrationFilePath": self.calibration.pathName,
                        "loggingFilePath": self.filePathLineEdit.text(),
                        "loggingFileName": self.fileNameLineEdit.text(),
                        "autoTimeChecked": self.fileAutoTimeCB.isChecked()}
        settings.setValue(self.uuid, tempSettings)

    def sendData(self):
        data = "TEST DATA".encode('utf-8')
        if self.portCombobox.currentText() == "COM-ALL":
            self.sendSerialWriteSignal.emit("ALL", data)
        else:
            self.sendSerialWriteSignal.emit(self.portCombobox.currentText(), data)

    def changeShownType(self):
        if self.shownTypeCB.currentText() == "Show: Hex":
            self.shownType = "Hex"
        elif self.shownTypeCB.currentText() == "Show: Values":
            self.shownType = "Values"
        elif self.shownTypeCB.currentText() == "Show: cal. Values":
            if self.calibration.configured:
                self.shownType = "cal. Values"
            else:
                self.shownTypeCB.setCurrentText("Show: Values")
                self.shownType = "Values"
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("No configuration file found")
                msg.setInformativeText("You have to import an configuration file before you can change the table view!")
                msg.setWindowTitle("Warning")
                msg.exec_()
        self.resizeTable(self.table.rowCount(), self.table.columnCount())

    def calibrationButtonPressed(self):
        if self.portCombobox.currentText() == "COM-ALL":
            button = QMessageBox.question(self, "COM ALL selected", "Do you really want to load a calibration file for ALL COM ports? \nIf not, select a specific COM port!")
            if button == QMessageBox.No:
                return None
        if self.kennbinCombobox.currentText() == "ALL Kennbin":
            button = QMessageBox.question(self, "ALL Kennbin selected", "Do you really want to load a calibration file for ALL Kennbin? \nIf not, select a specific Kennbin!")
            if button == QMessageBox.No:
                return None
        if self.calibration.configured:
            button = QMessageBox.question(self, "Calibration already existing", "Do you really want to override the current calibration file?")
            if button == QMessageBox.No:
                return None
        
        fileName = QFileDialog.getOpenFileName(None, "Open Calibration File", os.getcwd(), "csv(*.csv)\nall(*.*)", "",
                                               QFileDialog.DontUseNativeDialog)

        if fileName[0] == "":
            return None

        if self.calibration.readCalibrationFile(fileName[0]) is None:
            print("Error at loading calibration file")
            return
        self.loadCalibrationText.setText(self.calibration.fileName)
        if len(self.receivedValueData) > 0:
            self.receivedCalValueData = self.calibration.calibrate(self.receivedValueData)
        self.shownTypeCB.setCurrentText("Show: cal. Values")
        self.shownType = "cal. Values"
        self.portCombobox.setDisabled(True)
        self.baudrateCombobox.setDisabled(True)
        self.kennbinCombobox.setDisabled(True)

    def dragLabelActivated(self):
        if self.calibration:
            return {"port": None, "path": self.calibration.pathName}
        return {"port": None, "path": None}

    def dropLabelActivated(self, obj):
        if obj["path"] is None:
            return
        self.loadCalibrationFromSaveSettings(obj["path"])

    def loadCalibrationFromSaveSettings(self, path):
        if path == "":
            return None
        if self.portCombobox.currentText() == "COM-ALL":
            button = QMessageBox.question(self, "COM ALL selected", "Do you really want to load a calibration file for ALL COM ports?")
            if button == QMessageBox.No:
                return None
        if self.kennbinCombobox.currentText() == "ALL Kennbin":
            button = QMessageBox.question(self, "ALL Kennbin selected", "Do you really want to load a calibration file for ALL Kennbin?")
            if button == QMessageBox.No:
                return None
        if self.calibration.configured:
            button = QMessageBox.question(self, "Calibration already existing", "Do you really want to override the current calibration file?")
            if button == QMessageBox.No:
                return None

        try:
            if self.calibration.readCalibrationFile(path) is None:
                return
            self.loadCalibrationText.setText(self.calibration.fileName)
            if len(self.receivedValueData) > 0:
                self.receivedCalValueData = self.calibration.calibrate(self.receivedValueData)
            self.shownTypeCB.setCurrentText("Show: cal. Values")
            self.shownType = "cal. Values"
            self.portCombobox.setDisabled(True)
            self.baudrateCombobox.setDisabled(True)
            self.kennbinCombobox.setDisabled(True)
        except:
            pass
