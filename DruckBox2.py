import time

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from Tab import Tab
from datetime import datetime
import serial
import serial.tools.list_ports
from SerialParameters import SerialParameters
from PyQt5 import QtSvg
from MotorOptionsWindow import MotorOptionsWindow
from PressureScheduleWindow import PressureScheduleWindow
from UsefulFunctions import convertPressureUnits, convertTimeUnits, isFloat, returnFloat, resource_path, find_nth


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


class DruckBox2(Tab):
    sendSerialWriteSignal = pyqtSignal(str, object)
    renameTabSignal = pyqtSignal()

    def __init__(self, name, connectedPorts: list = None, port: str = "ALL", parent=None):
        super().__init__("DruckBox2", name, port, parent)

        self.connectedPorts = connectedPorts
        self.port = port

        self.fromPressure = 0
        self.fromPressureUnit = "Pa"
        self.toPressure = 0
        self.toPressureUnit = "Pa"
        self.spacing = 0
        self.spacingUnit = "Pa"
        self.pressureSteps = 1
        self.lengthOfStay = 0
        self.lengthOfStayUnit = "s"
        self.hysteresis = False

        self.pressureUnit = "Pa"
        self.timeUnit = "s"

        self.message = ""
        self.waitForVarMessage = ""
        self.waitForMessageTimer = QTimer()
        self.resendMessageTimer = QTimer()
        self.breakResendMessageTimer = QTimer()
        self.sendMessageState = "FREE"

        self.waitForVar = "NONE"
        self.waitForVarTimer = QTimer()
        self.resendTimer = QTimer()
        self.breakResendTimer = QTimer()
        self.nextPressurePointState = "STOP"

        self.transmissionState = "NoTransmission"
        self.motorOptionTransmissionState = ""
        self.motorOptionTransmissionTimer = QTimer()
        self.motorOptionTransmissionTimer.timeout.connect(self.transmitMotorOptions)
        self.transmissionStateCounter = 0

        self.sendPressureUpMessageTimer = QTimer()
        self.sendPressureUpMessageTimer.timeout.connect(self.sendPressureUpMessage)
        self.sendPressureDownMessageTimer = QTimer()
        self.sendPressureDownMessageTimer.timeout.connect(self.sendPressureDownMessage)

        self.clearFailedSendingLabelTimer = QTimer()
        self.clearFailedSendingLabelTimer.timeout.connect(self.clearFailedSendingLabel)

        self.varPSET = 300
        self.varPIN = 0
        self.varPOUT = 0
        self.varConP = 0
        self.varLSO = 10
        self.varMST = "FORCED BLOW OFF"
        self.varMSI = 10
        self.varMSF = 120
        self.varMSM = 70
        self.varMSS = 40
        self.varMDM = 80
        self.varMDC = 20
        self.varMDOP = 4
        self.varMTI = 30
        self.varMIIP = 215000 #320
        self.varMAIP = 750000 #1024

        self.updateScheduleTimer = QTimer()
        self.updateScheduleTimer.timeout.connect(self.updateProgress)
        self.elapsedTimer = QElapsedTimer()
        self.elapsedTimer.start()
        self.moveToNextPressurePointTimer = QTimer()
        self.currentPressurePoint = 0

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

        self.motorOptionsButton = QPushButton("Motor options")
        self.motorOptionsButton.clicked.connect(self.openMotorOptionsWindow)

        optionsLayout = QHBoxLayout()
        optionsLayout.addWidget(self.portCombobox)
        optionsLayout.addWidget(self.baudrateCombobox)
        optionsLayout.addStretch()
        optionsLayout.addWidget(self.motorOptionsButton)

        opacityEffect1 = QGraphicsOpacityEffect()
        opacityEffect1.setOpacity(0.3)
        opacityEffect2 = QGraphicsOpacityEffect()
        opacityEffect2.setOpacity(0.3)
        opacityEffect4 = QGraphicsOpacityEffect()
        opacityEffect4.setOpacity(0.3)

        lcd1UnitLabel = QLabel("bar")
        lcd1UnitLabel.setAlignment(Qt.AlignHCenter)
        lcd1UnitLabel.setGraphicsEffect(opacityEffect1)
        setPressureUnitLabel = QLabel("  bar")
        setPressureUnitLabel.setAlignment(Qt.AlignHCenter)
        setPressureUnitLabel.setGraphicsEffect(opacityEffect4)
        lcd2UnitLabel = QLabel("bar")
        lcd2UnitLabel.setAlignment(Qt.AlignHCenter)
        lcd2UnitLabel.setGraphicsEffect(opacityEffect2)

        self.pressureLCD1 = QLCDNumber()
        self.pressureLCD1.display("-----")
        self.pressureLCD1.setDigitCount(5)
        self.pressureLCD1.setFixedWidth(50)
        self.pressureLCD1.setFixedHeight(25)
        self.pressureLCD1.setSegmentStyle(QLCDNumber.Flat)
        self.pressureLCD1.setFrameShape(QFrame.NoFrame)

        pressureLCD1Layout = QVBoxLayout()
        pressureLCD1Layout.addWidget(self.pressureLCD1)
        pressureLCD1Layout.addWidget(lcd1UnitLabel)

        self.pressureLCD2 = QLCDNumber()
        self.pressureLCD2.display("-----")
        self.pressureLCD2.setDigitCount(5)
        self.pressureLCD2.setFixedWidth(50)
        self.pressureLCD2.setFixedHeight(25)
        self.pressureLCD2.setSegmentStyle(QLCDNumber.Flat)
        self.pressureLCD2.setFrameShape(QFrame.NoFrame)

        pressureLCD2Layout = QVBoxLayout()
        pressureLCD2Layout.addWidget(self.pressureLCD2)
        pressureLCD2Layout.addWidget(lcd2UnitLabel)

        self.pressureSetSpinBox = QDoubleSpinBox()
        self.pressureSetSpinBox.setRange(0, 10)
        self.pressureSetSpinBox.setValue(1)
        self.pressureSetSpinBox.setFixedWidth(60)
        self.pressureSetSpinBox.setAlignment(Qt.AlignCenter)
        self.pressureSetButton = QPushButton("Apply")
        self.pressureSetButton.setFixedWidth(60)
        self.pressureSetButton.clicked.connect(self.sendPressureSetMessage)

        pressureSetButtonLayout = QVBoxLayout()
        pressureSetButtonLayout.addWidget(self.pressureSetSpinBox)
        pressureSetButtonLayout.addWidget(self.pressureSetButton)

        pressureSetLayout = QGridLayout()
        pressureSetLayout.setContentsMargins(23, 0, 0, 0)
        pressureSetLayout.addLayout(pressureSetButtonLayout, 0, 0, 2, 1)
        pressureSetLayout.addWidget(setPressureUnitLabel, 0, 1, 1, 1)

        #C:/Users/Tim/Google Drive/Tim_UNI/Fachpraktikum/PC Software/PyQt5/Main Project/
        svgDruckLeitung1 = QtSvg.QSvgWidget(resource_path('res/Symbole/Druckleitung.svg'))
        svgDruckLeitung1.setFixedHeight(round(563.21765 / 3))
        svgBarometer1 = QtSvg.QSvgWidget(resource_path('res/Symbole/Barometer.svg'))
        svgBarometer1.setFixedSize(round(158.60344 / 3), round(563.216 / 3))
        svgDruckLeitung2 = QtSvg.QSvgWidget(resource_path('res/Symbole/Druckleitung.svg'))
        svgDruckLeitung2.setFixedHeight(round(563.21765 / 3))
        svgDruckregelVentil = QtSvg.QSvgWidget(resource_path('res/Symbole/Druckregelventil.svg'))
        svgDruckregelVentil.setFixedSize(round(343.86719 / 3), round(563.21765 / 3))
        svgDruckLeitung3 = QtSvg.QSvgWidget(resource_path('res/Symbole/Druckleitung.svg'))
        svgDruckLeitung3.setFixedHeight(round(563.21765 / 3))
        svgBarometer2 = QtSvg.QSvgWidget(resource_path('res/Symbole/Barometer.svg'))
        svgBarometer2.setFixedSize(round(158.60344 / 3), round(563.216 / 3))
        svgDruckLeitung4 = QtSvg.QSvgWidget(resource_path('res/Symbole/Druckleitung.svg'))
        svgDruckLeitung4.setFixedHeight(round(563.21765 / 3))
        svgDruckVentil = QtSvg.QSvgWidget(resource_path('res/Symbole/Druckventil.svg'))
        svgDruckVentil.setFixedSize(round(343.86719 / 3), round(563.21765 / 3))
        svgDruckLeitung5 = QtSvg.QSvgWidget(resource_path('res/Symbole/Druckleitung.svg'))
        svgDruckLeitung5.setFixedHeight(round(563.21765 / 3))

        self.druckVentilLabel = QLabel(u"\n\n\u2192")
        self.druckVentilLabel.setAlignment(Qt.AlignHCenter)

        self.druckRegelVentilLabel = QLabel(u"\n\n\n\n\n\u2190")
        self.druckRegelVentilLabel.setAlignment(Qt.AlignRight)

        label3 = QLabel("")
        label3.setFixedWidth(47)
        self.messageTransferLabel = QLabel(u"\u2195")
        self.messageTransferLabel.setFixedWidth(20)
        self.messageTransferLabel.setFont(QFont("Times", 12, QFont.Bold))
        self.messageLabel = QLabel("")
        self.messageLabel.setFixedWidth(200)
        opacityEffect3 = QGraphicsOpacityEffect()
        opacityEffect3.setOpacity(0.2)
        self.messageLabel.setGraphicsEffect(opacityEffect3)
        messageTransferLayout = QHBoxLayout()
        messageTransferLayout.addWidget(label3)
        messageTransferLayout.addWidget(self.messageTransferLabel)
        messageTransferLayout.addWidget(self.messageLabel)
        messageTransferLayout.addStretch()

        self.eStopButton = QPushButton("STOP")
        self.eStopButton.setStyleSheet("background-color: red")
        self.eStopButton.setFixedWidth(70)
        self.eStopButton.pressed.connect(self.sendEmergencyStopMessage)
        self.pressureUpButton = QPushButton(u"p\u2191")
        self.pressureUpButton.setFixedWidth(40)
        self.pressureUpButton.pressed.connect(self.startSendPressureUpMessage)
        self.pressureUpButton.released.connect(self.stopSendPressureUpMessage)
        self.pressureDownButton = QPushButton(u"p\u2193")
        self.pressureDownButton.setFixedWidth(40)
        self.pressureDownButton.pressed.connect(self.startSendPressureDownMessage)
        self.pressureDownButton.released.connect(self.stopSendPressureDownMessage)
        directMotorControlLayout = QHBoxLayout()
        directMotorControlLayout.addWidget(self.eStopButton)
        directMotorControlLayout.addSpacing(10)
        directMotorControlLayout.addWidget(self.pressureUpButton)
        directMotorControlLayout.addWidget(self.pressureDownButton)
        directMotorControlLayout.addStretch()

        pressureDisplayLayout = QGridLayout()
        pressureDisplayLayout.setSpacing(0)
        pressureDisplayLayout.setContentsMargins(0, 20, 0, 0)
        pressureDisplayLayout.addWidget(svgDruckLeitung1, 1, 0)
        pressureDisplayLayout.addLayout(pressureLCD1Layout, 0, 1, 1, 1)
        pressureDisplayLayout.addWidget(svgBarometer1, 1, 1)
        pressureDisplayLayout.addWidget(svgDruckLeitung2, 1, 2)
        pressureDisplayLayout.addWidget(self.druckRegelVentilLabel, 1, 2)
        pressureDisplayLayout.addLayout(pressureSetLayout, 0, 3, 1, 1)
        pressureDisplayLayout.addWidget(svgDruckregelVentil, 1, 3)
        pressureDisplayLayout.addLayout(messageTransferLayout, 2, 3, 1, 6)
        pressureDisplayLayout.addWidget(svgDruckLeitung3, 1, 4)
        pressureDisplayLayout.addLayout(directMotorControlLayout, 2, 4, 1, 4)
        pressureDisplayLayout.addLayout(pressureLCD2Layout, 0, 5, 1, 1)
        pressureDisplayLayout.addWidget(svgBarometer2, 1, 5)
        pressureDisplayLayout.addWidget(svgDruckLeitung4, 1, 6)
        pressureDisplayLayout.addWidget(svgDruckVentil, 1, 7)
        pressureDisplayLayout.addWidget(self.druckVentilLabel, 1, 7)
        pressureDisplayLayout.addWidget(svgDruckLeitung5, 1, 8)

        self.scheduleButton = QPushButton("  Create schedule  ")
        self.scheduleButton.clicked.connect(self.openPressureScheduleWindow)
        self.lockScheduleCB = QCheckBox("Lock")
        self.lockScheduleCB.stateChanged.connect(self.lockSchedule)
        self.failedSendingLabel = QLabel("")
        scheduleLayout = QHBoxLayout()
        scheduleLayout.addWidget(self.scheduleButton)
        scheduleLayout.addWidget(self.lockScheduleCB)
        scheduleLayout.addWidget(self.failedSendingLabel)
        scheduleLayout.addStretch()

        self.table = QTableWidget(3, 1)
        self.table.setVerticalHeaderLabels(['Target pressure', 'Time', 'Progress'])
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.pressureUnitCB = QComboBox()
        self.pressureUnitCB.addItem("Pa")
        self.pressureUnitCB.addItem("kPa")
        self.pressureUnitCB.addItem("MPa")
        self.pressureUnitCB.addItem("bar")
        self.pressureUnitCB.currentTextChanged.connect(self.changePressureUnit)

        self.timeUnitCB = QComboBox()
        self.timeUnitCB.addItem("s")
        self.timeUnitCB.addItem("min")
        self.timeUnitCB.addItem("h")
        self.timeUnitCB.currentTextChanged.connect(self.changeTimeUnit)

        CB3 = QComboBox()
        CB3.addItem("%")

        self.table.setCellWidget(0, 0, self.pressureUnitCB)
        self.table.setCellWidget(1, 0, self.timeUnitCB)
        self.table.setCellWidget(2, 0, CB3)
        self.table.setColumnWidth(0, 60)

        self.table.setFixedHeight(1 + self.table.rowHeight(0) + self.table.rowHeight(1) + self.table.rowHeight(2) + self.table.verticalHeader().width() + self.table.verticalScrollBar().height())

        self.startButton = QPushButton("Start")
        self.startButton.clicked.connect(self.startSchedule)
        self.stopButton = QPushButton("Stop")
        self.stopButton.clicked.connect(self.stopSchedule)
        self.resetButton = QPushButton("Reset")
        self.resetButton.clicked.connect(self.resetSchedule)
        self.addColumnButton = QPushButton("+ Column")
        self.addColumnButton.clicked.connect(self.addColumn)
        self.deleteColumnButton = QPushButton("- Column")
        self.deleteColumnButton.clicked.connect(self.deleteLastColumn)

        optionsLayout2 = QHBoxLayout()
        optionsLayout2.addWidget(self.startButton)
        optionsLayout2.addWidget(self.stopButton)
        optionsLayout2.addWidget(self.resetButton)
        optionsLayout2.addStretch()
        optionsLayout2.addWidget(self.deleteColumnButton)
        optionsLayout2.addWidget(self.addColumnButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(optionsLayout)
        mainLayout.addStretch()
        mainLayout.addLayout(pressureDisplayLayout)
        mainLayout.addStretch()
        mainLayout.addLayout(scheduleLayout)
        mainLayout.addWidget(self.table)
        mainLayout.addLayout(optionsLayout2)
        
        
        self.mainframe = QFrame()
        self.mainframe.setLayout(mainLayout)
        mainLayout2 = QVBoxLayout()
        mainLayout2.setSpacing(0)
        mainLayout2.setContentsMargins(0, 0, 0, 0)
        mainLayout2.addWidget(self.mainframe)

        self.setLayout(mainLayout2)

        self.initUI()
        
        self.mainframe.hide()
        # @TODO Ein Auswahlfenster erstellen wo man angeben kann auf welcher Seite die Messstelle des Druckminderer steht. Vor oder nach dem Volumenstrombooster?

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

    def receiveData(self, obj: SerialParameters, data):
        if self.portCombobox.currentText() != obj.port and self.portCombobox.currentText() != "COM-ALL":
            return
        if self.baudrateCombobox.currentText() != str(obj.baudrate) + " Baud" and self.baudrateCombobox.currentText() != "ALL Baud":
            return
        try:
            messageLabelText = data.decode('utf-8').strip()
        except:
            return
        self.messageLabel.setText(messageLabelText[messageLabelText.find("<")+1:min(messageLabelText.find(">"), find_nth(messageLabelText, "|", 2))])
        self.messageTransferLabel.setText(u"\u2193")

        self.processFunctionString(data.decode('utf-8'))

    def processFunctionString(self, message: str):
        functionString = message
        while self.funcionAvailable(functionString):
            decodedFunction = self.decodeFunction(functionString)
            functionString = self.cutFunction(functionString)

            if decodedFunction is None:
                continue
            param = self.getNextParameter(decodedFunction)
            decodedFunction = self.cutNextParameter(decodedFunction)
            if param == "NONE":
                continue
            elif param == "v":
                param = self.getNextParameter(decodedFunction)
                decodedFunction = self.cutNextParameter(decodedFunction)
                if param == "NONE":
                    continue
                elif param == "PVBIN":
                    param = self.getNextParameter(decodedFunction)
                    decodedFunction = self.cutNextParameter(decodedFunction)
                    if param == "NONE":
                        continue
                    elif isFloat(param):
                        self.varPIN = returnFloat(param)
                        self.pressureLCD1.display(returnFloat(param) / 100000)
                elif param == "PVBOUT":
                    param = self.getNextParameter(decodedFunction)
                    decodedFunction = self.cutNextParameter(decodedFunction)
                    if param == "NONE":
                        continue
                    elif isFloat(param):
                        self.varPOUT = returnFloat(param)
                        self.pressureLCD2.display(returnFloat(param) / 100000)
                elif param == "PIN":
                    param = self.getNextParameter(decodedFunction)
                    decodedFunction = self.cutNextParameter(decodedFunction)
                    if param == "NONE":
                        continue
                    elif isFloat(param):
                        self.varConP = returnFloat(param)
                elif param == "PSET":
                    param = self.getNextParameter(decodedFunction)
                    decodedFunction = self.cutNextParameter(decodedFunction)
                    if param == "NONE":
                        continue
                    elif isFloat(param):
                        self.varPSET = returnFloat(param)
                elif param == "MD":
                    param = self.getNextParameter(decodedFunction)
                    decodedFunction = self.cutNextParameter(decodedFunction)
                    if param == "NONE":
                        continue
                    elif param == "left":
                        self.druckRegelVentilLabel.setText(u"\n\n\n\n\n\u2190")
                    elif param == "right":
                        self.druckRegelVentilLabel.setText(u"\n\n\n\n\n\u2192")
                    elif param == "stop":
                        self.druckRegelVentilLabel.setText(u"\n\n\n\n\n|")
                elif param == "RLY":
                    param = self.getNextParameter(decodedFunction)
                    decodedFunction = self.cutNextParameter(decodedFunction)
                    if param == "NONE":
                        continue
                    elif param == "on":
                        self.druckVentilLabel.setText(u"\n\n\u2192")
                    elif param == "off":
                        self.druckVentilLabel.setText(u"\n\n\u2191")
            elif param == "e":
                param = self.getNextParameter(decodedFunction)
                decodedFunction = self.cutNextParameter(decodedFunction)
                if param == "NONE":
                    continue
                else:
                    self.failedSendingLabel.setStyleSheet("color: red")
                    self.failedSendingLabel.setText("No input pressure for control box!")
                    if not self.clearFailedSendingLabelTimer.isActive():
                        self.clearFailedSendingLabelTimer.start(100)
                    else:
                        self.clearFailedSendingLabelTimer.start(100)
            elif param == "r":
                param = self.getNextParameter(decodedFunction)
                decodedFunction = self.cutNextParameter(decodedFunction)
                if param == "NONE":
                    continue
                else:
                    self.receivedSuccessfulTransmissionSignal(param)

    def clearFailedSendingLabel(self):
        self.clearFailedSendingLabelTimer.stop()
        self.failedSendingLabel.setText("")

    def sendData(self, dataString: str):
        data = dataString.encode('utf-8')
        data += b'\r\n'
        self.messageLabel.setText(dataString[dataString.find("<")+1:min(dataString.find(">"), find_nth(dataString, "|", 2))])
        self.messageTransferLabel.setText(u"\u2191")
        if self.portCombobox.currentText() == "COM-ALL":
            self.sendSerialWriteSignal.emit("ALL", data)
        else:
            self.sendSerialWriteSignal.emit(self.portCombobox.currentText(), data)

    def receivedSuccessfulTransmissionSignal(self, varName: str):
        if self.waitForVar == varName:
            self.waitForVar = "NONE"
            self.transmissionState = "Done"
            self.stopResendTimer()
            self.stopResendMessageTimer()

    def getMotorOptionsParameters(self):
        self.varMST = self.motorOptionsWindow.controlStateCB.currentText()
        self.varMSI = self.motorOptionsWindow.motorAccelerationSpinBox.value()
        self.varMSF = self.motorOptionsWindow.motorSpeedFastSpinBox.value()
        self.varMSM = self.motorOptionsWindow.motorSpeedMediumSpinBox.value()
        self.varMSS = self.motorOptionsWindow.motorSpeedSlowSpinBox.value()
        self.varMDM = self.motorOptionsWindow.motorDistMediumSpinBox.value()
        self.varMDC = self.motorOptionsWindow.motorDistCloseSpinBox.value()
        self.varMDOP = self.motorOptionsWindow.motorDistOnPointSpinBox.value()
        self.varMIIP = self.motorOptionsWindow.minPressureSpinBox.value()
        self.varMAIP = self.motorOptionsWindow.maxPressuerSpinBox.value()
        self.varMTI = self.motorOptionsWindow.motorControlRefreshSpinBox.value()

        self.transmitAllMotorOptionsAtOnce()
        #self.transmissionStateCounter = 0
        #self.transmitMotorOptions()
        #self.motorOptionTransmissionTimer.start(50)

    def getMotorParametersAndClose(self):
        self.getMotorOptionsParameters()
        self.motorOptionsWindow.close()

    def getPressureScheduleParameters(self):
        self.fromPressure = self.pressureScheduleWindow.fromPressureSpinBox.value()
        self.fromPressureUnit = self.pressureScheduleWindow.fromPressureUnitCB.currentText()
        self.toPressure = self.pressureScheduleWindow.toPressureSpinBox.value()
        self.toPressureUnit = self.pressureScheduleWindow.toPressureUnitCB.currentText()
        self.spacing = self.pressureScheduleWindow.spacingSpinBox.value()
        self.spacingUnit = self.pressureScheduleWindow.spacingUnitCB.currentText()
        self.pressureSteps = self.pressureScheduleWindow.stepsCountSpinBox.value()
        self.lengthOfStay = self.pressureScheduleWindow.lengthOfStaySpinBox.value()
        self.lengthOfStayUnit = self.pressureScheduleWindow.lengthOfStayUnitCB.currentText()
        self.hysteresis = self.pressureScheduleWindow.hysteresisCheckBox.isChecked()

        self.clearTable()
        self.createSchedule()

    def getScheduleParametersAndClose(self):
        self.getPressureScheduleParameters()
        self.pressureScheduleWindow.close()

    def openMotorOptionsWindow(self):
        self.motorOptionsWindow = MotorOptionsWindow()
        self.motorOptionsWindow.controlStateCB.setCurrentText(self.varMST)
        self.motorOptionsWindow.motorAccelerationSpinBox.setValue(self.varMSI)
        self.motorOptionsWindow.motorSpeedFastSpinBox.setValue(self.varMSF)
        self.motorOptionsWindow.motorSpeedMediumSpinBox.setValue(self.varMSM)
        self.motorOptionsWindow.motorSpeedSlowSpinBox.setValue(self.varMSS)
        self.motorOptionsWindow.motorDistMediumSpinBox.setValue(self.varMDM)
        self.motorOptionsWindow.motorDistCloseSpinBox.setValue(self.varMDC)
        self.motorOptionsWindow.motorDistOnPointSpinBox.setValue(self.varMDOP)
        self.motorOptionsWindow.minPressureSpinBox.setValue(self.varMIIP)
        self.motorOptionsWindow.maxPressuerSpinBox.setValue(self.varMAIP)
        self.motorOptionsWindow.motorControlRefreshSpinBox.setValue(self.varMTI)
        self.motorOptionsWindow.okButton.clicked.connect(self.getMotorParametersAndClose)
        self.motorOptionsWindow.applyButton.clicked.connect(self.getMotorOptionsParameters)
        self.motorOptionsWindow.show()

    def openPressureScheduleWindow(self):
        self.pressureScheduleWindow = PressureScheduleWindow()
        self.pressureScheduleWindow.okButton.clicked.connect(self.getScheduleParametersAndClose)
        self.pressureScheduleWindow.applyButton.clicked.connect(self.getPressureScheduleParameters)
        self.pressureScheduleWindow.fromPressureSpinBox.setValue(self.fromPressure)
        self.pressureScheduleWindow.fromPressureUnitCB.setCurrentText(self.fromPressureUnit)
        self.pressureScheduleWindow.toPressureSpinBox.setValue(self.toPressure)
        self.pressureScheduleWindow.toPressureUnitCB.setCurrentText(self.toPressureUnit)
        self.pressureScheduleWindow.spacingSpinBox.setValue(self.spacing)
        self.pressureScheduleWindow.spacingUnitCB.setCurrentText(self.spacingUnit)
        self.pressureScheduleWindow.stepsCountSpinBox.setValue(self.pressureSteps)
        self.pressureScheduleWindow.lengthOfStaySpinBox.setValue(self.lengthOfStay)
        self.pressureScheduleWindow.lengthOfStayUnitCB.setCurrentText(self.lengthOfStayUnit)
        self.pressureScheduleWindow.hysteresisCheckBox.setChecked(self.hysteresis)
        self.pressureScheduleWindow.show()

    def addColumn(self):
        self.table.insertColumn(self.table.columnCount())

        QDSB = QDoubleSpinBox()
        QDSB.setRange(0, 10000000)
        QDSB.setButtonSymbols(QAbstractSpinBox.NoButtons)
        QDSB.setAlignment(Qt.AlignHCenter)
        self.table.setCellWidget(0, self.table.columnCount()-1, QDSB)

        QDSB1 = QDoubleSpinBox()
        QDSB1.setRange(0, 100000000)
        QDSB1.setButtonSymbols(QAbstractSpinBox.NoButtons)
        QDSB1.setAlignment(Qt.AlignHCenter)
        self.table.setCellWidget(1, self.table.columnCount()-1, QDSB1)

        pB = QProgressBar()
        pB.setValue(0)
        #pB.setStyleSheet('text-align: center')
        self.table.setCellWidget(2, self.table.columnCount()-1, pB)

    def deleteLastColumn(self):
        if self.table.columnCount() > 1:
            self.table.removeColumn(self.table.columnCount()-1)

    def clearTable(self):
        for columnIndex in range(self.table.columnCount() - 1, 0, -1):
            self.deleteLastColumn()

    def clearProgress(self):
        for columnIndex in range(1, self.table.columnCount()):
            self.table.cellWidget(2, columnIndex).setValue(0)

    def createSchedule(self):
        self.clearTable()
        timeValue = convertTimeUnits(self.lengthOfStay, self.lengthOfStayUnit, self.timeUnitCB.currentText())
        pressureSteps = self.pressureSteps + 1

        for count in range(1, pressureSteps):
            pVal = (count-1) * convertPressureUnits(self.spacing, self.spacingUnit) + convertPressureUnits(self.fromPressure, self.fromPressureUnit)
            pressureValue = convertPressureUnits(pVal, "Pa", self.pressureUnitCB.currentText())
            self.addColumn()
            self.table.cellWidget(0, count).setValue(pressureValue)
            self.table.cellWidget(1, count).setValue(timeValue)

        self.addColumn()
        self.table.cellWidget(0, pressureSteps).setValue(convertPressureUnits(self.toPressure, self.toPressureUnit, self.pressureUnitCB.currentText()))
        self.table.cellWidget(1, pressureSteps).setValue(timeValue)

        if self.hysteresis:
            for count in range(1, pressureSteps):
                pVal = (pressureSteps-count-1) * convertPressureUnits(self.spacing, self.spacingUnit) + convertPressureUnits(self.fromPressure, self.fromPressureUnit)
                pressureValue = convertPressureUnits(pVal, "Pa", self.pressureUnitCB.currentText())
                self.addColumn()
                self.table.cellWidget(0, count + pressureSteps).setValue(pressureValue)
                self.table.cellWidget(1, count + pressureSteps).setValue(timeValue)

    def changePressureUnit(self):
        for count in range(1, self.table.columnCount()):
            val = self.table.cellWidget(0, count).value()
            pressureValue = convertPressureUnits(val, self.pressureUnit, self.pressureUnitCB.currentText())
            self.table.cellWidget(0, count).setValue(pressureValue)
        self.pressureUnit = self.pressureUnitCB.currentText()

    def changeTimeUnit(self):
        for count in range(1, self.table.columnCount()):
            val = self.table.cellWidget(1, count).value()
            timeValue = convertTimeUnits(val, self.timeUnit, self.timeUnitCB.currentText())
            self.table.cellWidget(1, count).setValue(timeValue)
        self.timeUnit = self.timeUnitCB.currentText()

    def startSchedule(self):
        if self.table.columnCount() < 2:
            return
        self.updateScheduleTimer.start(100)
        try:
            self.moveToNextPressurePointTimer.disconnect()
        except TypeError:
            pass
        self.pressureSetButton.setEnabled(False)
        self.startButton.setEnabled(False)
        self.addColumnButton.setEnabled(False)
        self.deleteColumnButton.setEnabled(False)
        self.clearProgress()
        self.currentPressurePoint = 0
        self.moveToNextPressurePointTimer.start(0)
        self.moveToNextPressurePointTimer.timeout.connect(self.moveToNextPressurePoint)

    def updateProgress(self):
        if self.table.columnCount() - 1 < self.currentPressurePoint:
            return
        if self.nextPressurePointState != "STOP":
            return
        tVal = self.table.cellWidget(1, self.currentPressurePoint).value()
        timeInMS = convertTimeUnits(tVal, self.timeUnit, "ms")
        timerTime = self.elapsedTimer.elapsed()
        if timeInMS == 0:
            return
        self.table.cellWidget(2, self.currentPressurePoint).setValue(round((timerTime / timeInMS) * 100.0))

    def stopSchedule(self):
        self.pressureSetButton.setEnabled(True)
        self.startButton.setEnabled(True)
        self.addColumnButton.setEnabled(True)
        self.deleteColumnButton.setEnabled(True)
        self.stopPressureTimer()
        self.stopBreakResendTimer()
        self.stopResendTimer()
        self.updateScheduleTimer.stop()
        self.nextPressurePointState = "STOP"

    def resetSchedule(self):
        self.stopSchedule()
        self.createSchedule()

    def moveToNextPressurePoint(self):
        if self.nextPressurePointState == "STOP":
            self.currentPressurePoint += 1
            self.elapsedTimer.restart()
            if self.table.columnCount() - 1 < self.currentPressurePoint:
                if self.currentPressurePoint > 1:
                    self.table.cellWidget(2, self.table.columnCount()-1).setValue(100)
                self.stopSchedule()
                return
            if self.currentPressurePoint > 1:
                self.table.cellWidget(2, self.currentPressurePoint-1).setValue(100)
            self.stopPressureTimer()
            self.nextPressurePointState = "WAITFORFREE"
            self.moveToNextPressurePoint()
            return
        elif self.nextPressurePointState == "WAITFORFREE":
            self.stopPressureTimer()
            if self.waitForVar == "NONE":
                self.stopBreakResendTimer()
                self.breakResendTimer.start(11000)
                self.breakResendTimer.timeout.connect(self.failedResendMessage)
                self.nextPressurePointState = "SEND"
                self.moveToNextPressurePoint()
                return
            else:
                self.moveToNextPressurePointTimer.start(100)
                self.moveToNextPressurePointTimer.timeout.connect(self.moveToNextPressurePoint)
        elif self.nextPressurePointState == "SEND":
            self.waitForVar = "PSET"
            pVal = self.table.cellWidget(0, self.currentPressurePoint).value()
            pressureInPa = convertPressureUnits(pVal, self.pressureUnit)
            self.sendData(self.encodeFunction("s|PSET|" + str(round(pressureInPa))))
            self.nextPressurePointState = "WAITFORSENDING"
            self.stopResendTimer()
            self.resendTimer.start(2025)
            self.resendTimer.timeout.connect(self.resendMessage)
            self.stopPressureTimer()
            self.moveToNextPressurePointTimer.start(50)
            self.moveToNextPressurePointTimer.timeout.connect(self.moveToNextPressurePoint)
        elif self.nextPressurePointState == "WAITFORSENDING":
            if self.waitForVar == "NONE":
                self.stopResendTimer()
                self.stopBreakResendTimer()
                self.stopPressureTimer()
                self.nextPressurePointState = "MEASURE"
                self.moveToNextPressurePoint()
                return
            else:
                self.stopPressureTimer()
                self.moveToNextPressurePointTimer.start(20)
                self.moveToNextPressurePointTimer.timeout.connect(self.moveToNextPressurePoint)
        elif self.nextPressurePointState == "MEASURE":
            self.failedSendingLabel.setText("")
            self.nextPressurePointState = "STOP"
            self.elapsedTimer.restart()
            tVal = self.table.cellWidget(1, self.currentPressurePoint).value()
            timeInMs = convertTimeUnits(tVal, self.timeUnit, "ms")
            self.stopPressureTimer()
            self.moveToNextPressurePointTimer.start(timeInMs)
            self.moveToNextPressurePointTimer.timeout.connect(self.moveToNextPressurePoint)

    def resendMessage(self):
        self.failedSendingLabel.setStyleSheet("color: yellow")
        self.failedSendingLabel.setText("Failed to send message! Try again...")
        self.nextPressurePointState = "SEND"

    def failedResendMessage(self):
        self.failedSendingLabel.setStyleSheet("color: red")
        self.transmissionState = "NoTransmission"
        self.failedSendingLabel.setText("Failed catastrophically to send schedule pressure message!")
        self.stopSchedule()
        self.nextPressurePointState = "STOP"
        self.waitForVar = "NONE"

    def stopPressureTimer(self):
        self.moveToNextPressurePointTimer.stop()
        try:
            self.moveToNextPressurePointTimer.disconnect()
        except TypeError:
            pass

    def stopResendTimer(self):
        self.resendTimer.stop()
        try:
            self.resendTimer.disconnect()
        except TypeError:
            pass

    def stopBreakResendTimer(self):
        self.breakResendTimer.stop()
        try:
            self.breakResendTimer.disconnect()
        except TypeError:
            pass

    def sendMessage(self):
        if self.message == "":
            self.stopWaitForMessageTimer()
            self.stopResendMessageTimer()
            return
        if self.sendMessageState == "FREE":
            self.stopWaitForMessageTimer()
            if self.waitForVar == "NONE":
                self.sendMessageState = "SEND"
                self.stopBreakResendMessageTimer()
                self.breakResendMessageTimer.start(11000)
                self.breakResendMessageTimer.timeout.connect(self.failedResendNewMessage)
                self.sendMessage()
                return
            else:
                self.waitForMessageTimer.start(50)
                self.waitForMessageTimer.timeout.connect(self.sendMessage)
        elif self.sendMessageState == "SEND":
            self.waitForVar = self.waitForVarMessage
            self.sendData(self.encodeFunction(self.message))
            self.sendMessageState = "WAITFORSENDING"
            self.stopResendMessageTimer()
            self.resendMessageTimer.start(2025)
            self.resendMessageTimer.timeout.connect(self.resendNewMessage)
            self.stopWaitForMessageTimer()
            self.waitForMessageTimer.start(50)
            self.waitForMessageTimer.timeout.connect(self.sendMessage)
        elif self.sendMessageState == "WAITFORSENDING":
            if self.waitForVar == "NONE":
                self.failedSendingLabel.setText("")
                self.stopBreakResendMessageTimer()
                self.stopResendMessageTimer()
                self.stopWaitForMessageTimer()
                self.sendMessageState = "FREE"
                return
            else:
                self.stopWaitForMessageTimer()
                self.waitForMessageTimer.start(20)
                self.waitForMessageTimer.timeout.connect(self.sendMessage)

    def stopWaitForMessageTimer(self):
        self.waitForMessageTimer.stop()
        try:
            self.waitForMessageTimer.disconnect()
        except TypeError:
            pass

    def stopResendMessageTimer(self):
        self.resendMessageTimer.stop()
        try:
            self.resendMessageTimer.disconnect()
        except TypeError:
            pass

    def stopBreakResendMessageTimer(self):
        self.breakResendMessageTimer.stop()
        try:
            self.breakResendMessageTimer.disconnect()
        except TypeError:
            pass

    def resendNewMessage(self):
        self.failedSendingLabel.setStyleSheet("color: yellow")
        self.failedSendingLabel.setText("Failed to send message! Try again...")
        self.sendMessageState = "SEND"

    def failedResendNewMessage(self):
        self.failedSendingLabel.setStyleSheet("color: red")
        self.transmissionState = "NoTransmission"
        self.failedSendingLabel.setText("Failed catastrophically to send message!")
        self.sendMessageState = "FREE"
        self.stopWaitForMessageTimer()
        self.stopResendMessageTimer()
        self.stopBreakResendMessageTimer()
        self.waitForVar = "NONE"

    def sendPressureSetMessage(self):
        self.message = "s|PSET|" + str(convertPressureUnits(self.pressureSetSpinBox.value(), "bar"))
        self.waitForVarMessage = "PSET"
        self.sendMessage()

    def lockSchedule(self):
        if self.lockScheduleCB.isChecked():
            self.table.setEnabled(False)
            self.scheduleButton.setEnabled(False)
            self.addColumnButton.setEnabled(False)
            self.deleteColumnButton.setEnabled(False)
        else:
            self.table.setEnabled(True)
            self.scheduleButton.setEnabled(True)
            self.addColumnButton.setEnabled(True)
            self.deleteColumnButton.setEnabled(True)

    def encodeFunction(self, functionString: str):
        fString = functionString + "|"
        checkSum = 0
        for c in fString:
            checkSum += ord(c)
        lastChar = chr(90 - (checkSum % 26))
        return "<" + fString + lastChar + ">"

    def decodeFunction(self, functionString: str):
        if functionString.find("<") < 0 or functionString.find(">") < 0 or functionString.find("<") > functionString.find(">"):
            return None
        fString = functionString[functionString.find("<") + 1:functionString.find(">")]
        checkSum = 0
        for c in fString:
            checkSum += ord(c)
        lastChar = (checkSum - 90) % 26
        if lastChar != 0:
            return None
        return fString[0:-2]

    def funcionAvailable(self, functionString: str):
        return functionString.find("<") != -1 and functionString.find(">") != -1 and functionString.find("<") < functionString.find(">")

    def cutFunction(self, functionString: str):
        return functionString[functionString.find(">") + 1:]

    def getNextParameter(self, paramString: str):
        outString = "NONE"
        if paramString.find("|") != -1 and len(paramString) > 0:
            outString = paramString[:paramString.find("|")]
        elif len(paramString) > 0:
            outString = paramString
        return outString

    def cutNextParameter(self, paramString: str):
        if paramString.find("|") != -1 and len(paramString) > 0:
            return paramString[paramString.find("|") + 1:]
        return ""

    def sendEmergencyStopMessage(self):
        self.sendData(self.encodeFunction("s|ES"))
        self.stopSchedule()

    def sendPressureUpMessage(self):
        self.sendData(self.encodeFunction("s|TPU"))

    def sendPressureDownMessage(self):
        self.sendData(self.encodeFunction("s|TPD"))

    def startSendPressureUpMessage(self):
        self.sendData(self.encodeFunction("s|TPU"))
        self.sendPressureUpMessageTimer.start(200)

    def startSendPressureDownMessage(self):
        self.sendData(self.encodeFunction("s|TPD"))
        self.sendPressureDownMessageTimer.start(200)

    def stopSendPressureUpMessage(self):
        self.sendPressureUpMessageTimer.stop()

    def stopSendPressureDownMessage(self):
        self.sendPressureDownMessageTimer.stop()

    def transmitAllMotorOptionsAtOnce(self):
        message = (self.encodeFunction("s|MST|" + self.varMST) +
                   self.encodeFunction("s|MSI|" + str(round(self.varMSI))) +
                   self.encodeFunction("s|MSF|" + str(round(self.varMSF))) +
                   self.encodeFunction("s|MSM|" + str(round(self.varMSM))) +
                   self.encodeFunction("s|MSS|" + str(round(self.varMSS))) +
                   self.encodeFunction("s|MDM|" + str(round(self.varMDM))) +
                   self.encodeFunction("s|MDC|" + str(round(self.varMDC))) +
                   self.encodeFunction("s|MDOP|" + str(round(self.varMDOP))) +
                   self.encodeFunction("s|MIIP|" + str(round(self.varMIIP))) +
                   self.encodeFunction("s|MAIP|" + str(round(self.varMAIP))) +
                   self.encodeFunction("s|MTI|" + str(round(self.varMTI))))
        self.sendData(message)

    def transmitMotorOptions(self):
        self.transmissionStateCounter += 1
        if self.transmissionStateCounter > 100:
            self.failedSendingLabel.setStyleSheet("color: red")
            self.failedSendingLabel.setText("Failed catastrophically to send option messages!")
            self.transmissionState = "NoTransmission"
            self.motorOptionTransmissionState = ""
            self.motorOptionTransmissionTimer.stop()
            return
        if self.motorOptionTransmissionState == "":
            self.transmissionState = "NoTransmission"
            self.motorOptionTransmissionState = "MST"
        if self.motorOptionTransmissionState == "MST":
            if self.transmissionState == "NoTransmission":
                self.transmissionState = "Transmit"
                self.message = "s|MST|" + self.varMST
                self.waitForVarMessage = "MST"
                self.sendMessage()
            elif self.transmissionState == "Done":
                self.transmissionState = "NoTransmission"
                self.motorOptionTransmissionState = "MSI"
        if self.motorOptionTransmissionState == "MSI":
            if self.transmissionState == "NoTransmission":
                self.transmissionState = "Transmit"
                self.message = "s|MSI|" + str(round(self.varMSI))
                self.waitForVarMessage = "MSI"
                self.sendMessage()
            elif self.transmissionState == "Done":
                self.transmissionState = "NoTransmission"
                self.motorOptionTransmissionState = "MSF"
        if self.motorOptionTransmissionState == "MSF":
            if self.transmissionState == "NoTransmission":
                self.transmissionState = "Transmit"
                self.message = "s|MSF|" + str(round(self.varMSF))
                self.waitForVarMessage = "MSF"
                self.sendMessage()
            elif self.transmissionState == "Done":
                self.transmissionState = "NoTransmission"
                self.motorOptionTransmissionState = "MSM"
        if self.motorOptionTransmissionState == "MSM":
            if self.transmissionState == "NoTransmission":
                self.transmissionState = "Transmit"
                self.message = "s|MSM|" + str(round(self.varMSM))
                self.waitForVarMessage = "MSM"
                self.sendMessage()
            elif self.transmissionState == "Done":
                self.transmissionState = "NoTransmission"
                self.motorOptionTransmissionState = "MSS"
        if self.motorOptionTransmissionState == "MSS":
            if self.transmissionState == "NoTransmission":
                self.transmissionState = "Transmit"
                self.message = "s|MSS|" + str(round(self.varMSS))
                self.waitForVarMessage = "MSS"
                self.sendMessage()
            elif self.transmissionState == "Done":
                self.transmissionState = "NoTransmission"
                self.motorOptionTransmissionState = "MDM"
        if self.motorOptionTransmissionState == "MDM":
            if self.transmissionState == "NoTransmission":
                self.transmissionState = "Transmit"
                self.message = "s|MDM|" + str(round(self.varMDM))
                self.waitForVarMessage = "MDM"
                self.sendMessage()
            elif self.transmissionState == "Done":
                self.transmissionState = "NoTransmission"
                self.motorOptionTransmissionState = "MDC"
        if self.motorOptionTransmissionState == "MDC":
            if self.transmissionState == "NoTransmission":
                self.transmissionState = "Transmit"
                self.message = "s|MDC|" + str(round(self.varMDC))
                self.waitForVarMessage = "MDC"
                self.sendMessage()
            elif self.transmissionState == "Done":
                self.transmissionState = "NoTransmission"
                self.motorOptionTransmissionState = "MDOP"
        if self.motorOptionTransmissionState == "MDOP":
            if self.transmissionState == "NoTransmission":
                self.transmissionState = "Transmit"
                self.message = "s|MDOP|" + str(round(self.varMDOP))
                self.waitForVarMessage = "MDOP"
                self.sendMessage()
            elif self.transmissionState == "Done":
                self.transmissionState = "NoTransmission"
                self.motorOptionTransmissionState = "MIIP"
        if self.motorOptionTransmissionState == "MIIP":
            if self.transmissionState == "NoTransmission":
                self.transmissionState = "Transmit"
                self.message = "s|MIIP|" + str(round(self.varMIIP))
                self.waitForVarMessage = "MIIP"
                self.sendMessage()
            elif self.transmissionState == "Done":
                self.transmissionState = "NoTransmission"
                self.motorOptionTransmissionState = "MAIP"
        if self.motorOptionTransmissionState == "MAIP":
            if self.transmissionState == "NoTransmission":
                self.transmissionState = "Transmit"
                self.message = "s|MAIP|" + str(round(self.varMAIP))
                self.waitForVarMessage = "MAIP"
                self.sendMessage()
            elif self.transmissionState == "Done":
                self.transmissionState = "NoTransmission"
                self.motorOptionTransmissionState = "MTI"
        if self.motorOptionTransmissionState == "MTI":
            if self.transmissionState == "NoTransmission":
                self.transmissionState = "Transmit"
                self.message = "s|MTI|" + str(round(self.varMTI))
                self.waitForVarMessage = "MTI"
                self.sendMessage()
            elif self.transmissionState == "Done":
                self.transmissionState = "NoTransmission"
                self.motorOptionTransmissionState = ""
                self.motorOptionTransmissionTimer.stop()

    def applySettings(self, settings: QSettings = None):
        if settings.contains(self.uuid):
            tempSettings = settings.value(self.uuid)
            if self.portCombobox.findText(tempSettings["port"]) == -1:
                self.portCombobox.addItem(tempSettings["port"])
            self.portCombobox.lastText = tempSettings["port"]
            self.portCombobox.setCurrentText(tempSettings["port"])
            self.changeTabName()
            self.baudrateCombobox.setCurrentText(tempSettings["baud"])

    def saveSettings(self, settings: QSettings = None):
        tempSettings = {"port": self.portCombobox.currentText(),
                        "baud": self.baudrateCombobox.currentText()}
        settings.setValue(self.uuid, tempSettings)
