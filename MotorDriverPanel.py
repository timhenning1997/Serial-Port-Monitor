import os
import time

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from Tab import Tab
from datetime import datetime
from SerialParameters import SerialParameters
from MotorDriverOptionsWindow import MotorDriverOptionsWindow
from UsefulFunctions import convertPressureUnits, convertTimeUnits, isInt, isFloat, returnInt, resource_path


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


class MotorDriverPanel(Tab):
    sendSerialWriteSignal = pyqtSignal(str, object)
    renameTabSignal = pyqtSignal()

    def __init__(self, name, connectedPorts: list = None, port: str = "ALL", parent=None):
        super().__init__("MotorDriverPanel", name, port, parent)

        self.connectedPorts = connectedPorts
        self.port = port

        self.timeUnit = "s"
        self.motorPos = 0
        self.targetPos = 0
        self.lastTargetPos = 0

        self.currentMessage = ""
        self.nextMessage = ""
        self.waitForResponseMessage = ""
        self.waitForResponseNextMessage = ""
        self.resendMessageTimer = QTimer()
        self.failedResendMessageTimer = QTimer()
        self.startedSendingMessage = False

        self.motorSpeed = 180
        self.minPos = 0
        self.maxPos = 10
        self.reverseDirection = False
        self.stepsPerRev = 200
        self.stepsPerMM = 200
        self.controlRefreshTime = 30

        self.updateScheduleTimer = QTimer()
        self.updateScheduleTimer.timeout.connect(self.updateProgress)
        self.elapsedTimer = QElapsedTimer()
        self.elapsedTimer.start()
        self.moveToNextPositionPointTimer = QTimer()
        self.currentPositionPoint = 0

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

        self.motorCalibrationButton = QPushButton("Motor calibration")
        self.motorCalibrationButton.clicked.connect(self.sendCalibrationMessage)

        optionsLayout = QHBoxLayout()
        optionsLayout.addWidget(self.portCombobox)
        optionsLayout.addWidget(self.baudrateCombobox)
        optionsLayout.addStretch()
        optionsLayout.addWidget(self.motorCalibrationButton)
        optionsLayout.addWidget(self.motorOptionsButton)

        targetPosTextLabel = QLabel("Target pos:")
        targetPosTextLabel.setFixedWidth(60)
        self.targetPosLabel = QLabel("0.00 mm")
        self.targetPosLabel.setFixedWidth(60)
        actualPosTextLabel = QLabel("Actual pos:")
        actualPosTextLabel.setFixedWidth(60)
        self.actualPosLabel = QLabel("0.00 mm")
        self.actualPosLabel.setFixedWidth(60)

        targetPosLayout = QHBoxLayout()
        targetPosLayout.addWidget(targetPosTextLabel)
        targetPosLayout.addWidget(self.targetPosLabel)
        actualPosLayout = QHBoxLayout()
        actualPosLayout.addWidget(actualPosTextLabel)
        actualPosLayout.addWidget(self.actualPosLabel)
        positionTextLayout = QVBoxLayout()
        positionTextLayout.addStretch()
        positionTextLayout.addLayout(targetPosLayout)
        positionTextLayout.addLayout(actualPosLayout)
        positionTextLayout.addStretch()

        self.minPosLabel = QLabel("0 mm")
        self.maxPosLabel = QLabel("10 mm")
        self.posSlider = QSlider()
        self.posSlider.setRange(0, 2000)
        self.posSlider.setInvertedAppearance(True)
        self.posSlider.setEnabled(False)
        self.eStopButton = QPushButton("STOP / Last Target")
        self.eStopButton.setStyleSheet("background-color: red")
        self.eStopButton.pressed.connect(self.sendLastTargetMessage)
        positionSliderLayout = QVBoxLayout()
        positionSliderLayout.addWidget(self.minPosLabel)
        positionSliderLayout.addWidget(self.posSlider)
        positionSliderLayout.addWidget(self.maxPosLabel)
        # positionSliderLayout.addWidget(self.eStopButton)
        positionSliderLayout.setAlignment(self.minPosLabel, Qt.AlignHCenter)
        positionSliderLayout.setAlignment(self.posSlider, Qt.AlignHCenter)
        positionSliderLayout.setAlignment(self.maxPosLabel, Qt.AlignHCenter)
        # positionSliderLayout.setAlignment(self.eStopButton, Qt.AlignHCenter)

        emptyLabel = QLabel(" ")
        emptyLabel2 = QLabel("        ")

        self.moveUpButton = QPushButton("Move up")
        self.moveUpButton.clicked.connect(self.sendMoveUpMessage)
        self.moveUpValueSB = QDoubleSpinBox()
        self.moveUpValueSB.setRange(0, 10000)
        self.moveUpUnitSB = QComboBox()
        self.moveUpUnitSB.addItems(["mm", "steps", "degrees", "revolutions"])

        self.moveDownButton = QPushButton("Move down")
        self.moveDownButton.clicked.connect(self.sendMoveDownMessage)
        self.moveDownValueSB = QDoubleSpinBox()
        self.moveDownValueSB.setRange(0, 10000)
        self.moveDownUnitSB = QComboBox()
        self.moveDownUnitSB.addItems(["mm", "steps", "degrees", "revolutions"])

        self.setPosToButton = QPushButton("Set position to")
        self.setPosToButton.clicked.connect(self.setPositionToMessage)
        self.setPosToValueSB = QSpinBox()
        self.setPosToValueSB.setRange(0, 10000)
        self.setPosToUnitSB = QComboBox()
        self.setPosToUnitSB.addItem("mm")

        self.moveToPosButton = QPushButton("Move to position")
        self.moveToPosButton.clicked.connect(self.moveToMessage)
        self.moveToPosValueSB = QDoubleSpinBox()
        self.moveToPosValueSB.setRange(0, 10000)
        self.moveToPosUnitSB = QComboBox()
        self.moveToPosUnitSB.addItem("mm")

        moveMotorButtonsGridLayout = QGridLayout()
        moveMotorButtonsGridLayout.addWidget(self.moveUpButton, 0, 0)
        moveMotorButtonsGridLayout.addWidget(self.moveUpValueSB, 0, 1)
        moveMotorButtonsGridLayout.addWidget(self.moveUpUnitSB, 0, 2)
        moveMotorButtonsGridLayout.addWidget(self.moveDownButton, 1, 0)
        moveMotorButtonsGridLayout.addWidget(self.moveDownValueSB, 1, 1)
        moveMotorButtonsGridLayout.addWidget(self.moveDownUnitSB, 1, 2)
        # moveMotorButtonsGridLayout.addWidget(self.setPosToButton, 2, 0)
        # moveMotorButtonsGridLayout.addWidget(self.setPosToValueSB, 2, 1)
        # moveMotorButtonsGridLayout.addWidget(self.setPosToUnitSB, 2, 2)
        moveMotorButtonsGridLayout.addWidget(emptyLabel, 3, 0)
        moveMotorButtonsGridLayout.addWidget(self.moveToPosButton, 4, 0)
        moveMotorButtonsGridLayout.addWidget(self.moveToPosValueSB, 4, 1)
        moveMotorButtonsGridLayout.addWidget(self.moveToPosUnitSB, 4, 2)

        moveMotorButtonsLayout = QVBoxLayout()
        moveMotorButtonsLayout.addStretch()
        moveMotorButtonsLayout.addLayout(moveMotorButtonsGridLayout)
        moveMotorButtonsLayout.addStretch()

        motorDisplayLayout = QHBoxLayout()
        motorDisplayLayout.addLayout(positionTextLayout)
        motorDisplayLayout.addLayout(positionSliderLayout)
        motorDisplayLayout.addWidget(emptyLabel2)
        motorDisplayLayout.addLayout(moveMotorButtonsLayout)
        motorDisplayLayout.addStretch()

        self.lockScheduleCB = QCheckBox("Lock")
        self.lockScheduleCB.stateChanged.connect(self.lockSchedule)
        self.failedSendingLabel = QLabel("")
        self.readTxtFileButton = QPushButton("Select File")
        self.readTxtFileButton.clicked.connect(self.readFile)

        scheduleLayout = QHBoxLayout()
        scheduleLayout.addWidget(self.lockScheduleCB)
        scheduleLayout.addWidget(self.failedSendingLabel)
        scheduleLayout.addStretch()
        scheduleLayout.addWidget(self.readTxtFileButton)

        self.table = QTableWidget(3, 1)
        self.table.setVerticalHeaderLabels(['Position', 'Time', 'Progress'])
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        positionUnitCB = QComboBox()
        positionUnitCB.addItem("mm")

        self.timeUnitCB = QComboBox()
        self.timeUnitCB.addItem("s")
        self.timeUnitCB.addItem("min")
        self.timeUnitCB.addItem("h")
        self.timeUnitCB.currentTextChanged.connect(self.changeTimeUnit)

        CB3 = QComboBox()
        CB3.addItem("%")

        self.table.setCellWidget(0, 0, positionUnitCB)
        self.table.setCellWidget(1, 0, self.timeUnitCB)
        self.table.setCellWidget(2, 0, CB3)
        self.table.setColumnWidth(0, 60)

        self.table.setFixedHeight(1 + self.table.rowHeight(0) + self.table.rowHeight(1) + self.table.rowHeight(
            2) + self.table.verticalHeader().width() + self.table.verticalScrollBar().height())

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
        mainLayout.addLayout(motorDisplayLayout)
        mainLayout.addLayout(scheduleLayout)
        mainLayout.addWidget(self.table)
        mainLayout.addLayout(optionsLayout2)

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

    def receiveData(self, obj: SerialParameters, data):
        if self.portCombobox.currentText() != obj.port and self.portCombobox.currentText() != "COM-ALL":
            return
        if self.baudrateCombobox.currentText() != str(
                obj.baudrate) + " Baud" and self.baudrateCombobox.currentText() != "ALL Baud":
            return
        try:
            rawData = data.decode('utf-8')
            self.processFunctionString(rawData)
        except:
            return

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
                elif param == "POS":
                    param = self.getNextParameter(decodedFunction)
                    decodedFunction = self.cutNextParameter(decodedFunction)
                    if param == "NONE":
                        continue
                    elif isInt(param):
                        self.motorPos = returnInt(param)
                        self.posSlider.setValue(self.motorPos)
                        self.actualPosLabel.setText(str(round(float(self.motorPos) / float(self.stepsPerMM))) + " mm")
                elif param == "MIN":
                    param = self.getNextParameter(decodedFunction)
                    decodedFunction = self.cutNextParameter(decodedFunction)
                    if param == "NONE":
                        continue
                    elif isInt(param):
                        self.minPos = round(float(param) / float(self.stepsPerMM))
                        self.minPosLabel.setText(str(self.minPos) + " mm")
                        self.adjustMinMaxPos()
                elif param == "MAX":
                    param = self.getNextParameter(decodedFunction)
                    decodedFunction = self.cutNextParameter(decodedFunction)
                    if param == "NONE":
                        continue
                    elif isInt(param):
                        self.maxPos = round(float(param) / float(self.stepsPerMM))
                        self.maxPosLabel.setText(str(self.maxPos) + " mm")
                        self.adjustMinMaxPos()
            elif param == "r":
                param = self.getNextParameter(decodedFunction)
                decodedFunction = self.cutNextParameter(decodedFunction)
                if param == "NONE":
                    continue
                else:
                    self.receivedSuccessfulTransmissionSignal(param)

    def receivedSuccessfulTransmissionSignal(self, varName: str):
        if self.waitForResponseMessage == varName:
            self.stopTimer(self.resendMessageTimer)
            self.stopTimer(self.failedResendMessageTimer)
            self.currentMessage = ""
            self.waitForResponseMessage = ""
            self.startedSendingMessage = False
            if self.nextMessage != "":
                self.currentMessage = self.nextMessage
                self.waitForResponseMessage = self.waitForResponseNextMessage
                self.nextMessage = ""
                self.waitForResponseNextMessage = ""
                self.sendMessage()

    def sendData(self, dataString: str):
        data = dataString.encode('utf-8')
        data += b'\r\n'
        if self.portCombobox.currentText() == "COM-ALL":
            self.sendSerialWriteSignal.emit("ALL", data)
        else:
            self.sendSerialWriteSignal.emit(self.portCombobox.currentText(), data)

    def getMotorParameters(self):
        self.motorSpeed = self.motorOptionsWindow.motorSpeedSpinBox.value()
        self.minPos = self.motorOptionsWindow.minPosSpinBox.value()
        self.maxPos = self.motorOptionsWindow.maxPosSpinBox.value()
        self.reverseDirection = self.motorOptionsWindow.reverseDirCB.isChecked()
        self.stepsPerRev = self.motorOptionsWindow.stepsPerRevSpinBox.value()
        self.stepsPerMM = self.motorOptionsWindow.stepsPerMMSpinBox.value()
        self.controlRefreshTime = self.motorOptionsWindow.controlRefreshSpinBox.value()

        self.adjustMinMaxPos()
        self.sendMotorOptionsMessage()

    def adjustMinMaxPos(self):
        self.minPosLabel.setText(str(self.minPos) + " mm")
        self.maxPosLabel.setText(str(self.maxPos) + " mm")
        self.posSlider.setRange(self.minPos * self.stepsPerMM, self.maxPos * self.stepsPerMM)
        self.setPosToValueSB.setRange(self.minPos, self.maxPos)
        self.moveToPosValueSB.setRange(self.minPos, self.maxPos)

        for count in range(1, self.table.columnCount()):
            self.table.cellWidget(0, count).setRange(self.minPos, self.maxPos)

    def getMotorParametersAndClose(self):
        self.getMotorParameters()
        self.motorOptionsWindow.close()

    def openMotorOptionsWindow(self):
        self.motorOptionsWindow = MotorDriverOptionsWindow()
        self.motorOptionsWindow.motorSpeedSpinBox.setValue(self.motorSpeed)
        self.motorOptionsWindow.minPosSpinBox.setValue(self.minPos)
        self.motorOptionsWindow.maxPosSpinBox.setValue(self.maxPos)
        self.motorOptionsWindow.reverseDirCB.setChecked(self.reverseDirection)
        self.motorOptionsWindow.stepsPerRevSpinBox.setValue(self.stepsPerRev)
        self.motorOptionsWindow.stepsPerMMSpinBox.setValue(self.stepsPerMM)
        self.motorOptionsWindow.controlRefreshSpinBox.setValue(self.controlRefreshTime)
        self.motorOptionsWindow.okButton.clicked.connect(self.getMotorParametersAndClose)
        self.motorOptionsWindow.applyButton.clicked.connect(self.getMotorParameters)
        self.motorOptionsWindow.show()

    def sendMotorOptionsMessage(self):
        motorSpeed = self.changeRpmToDelay(self.motorSpeed)
        if self.reverseDirection:
            directionString = "T"
        else:
            directionString = "F"
        if self.currentMessage != "":
            self.nextMessage = (self.encodeFunction("s|TINT|" + str(self.controlRefreshTime)) +
                                self.encodeFunction("s|SPEED|" + str(motorSpeed)) +
                                self.encodeFunction("s|DIR|" + directionString))
            self.waitForResponseNextMessage = "DIR"
        else:
            self.currentMessage = (self.encodeFunction("s|TINT|" + str(self.controlRefreshTime)) +
                                   self.encodeFunction("s|SPEED|" + str(motorSpeed)) +
                                   self.encodeFunction("s|DIR|" + directionString))
            self.waitForResponseMessage = "DIR"
            self.sendMessage()

    def addColumn(self):
        self.table.insertColumn(self.table.columnCount())

        QDSB = QDoubleSpinBox()
        QDSB.setRange(self.minPos, self.maxPos)
        QDSB.setButtonSymbols(QAbstractSpinBox.NoButtons)
        QDSB.setAlignment(Qt.AlignHCenter)
        self.table.setCellWidget(0, self.table.columnCount() - 1, QDSB)

        QDSB1 = QDoubleSpinBox()
        QDSB1.setRange(0, 100000000)
        QDSB1.setButtonSymbols(QAbstractSpinBox.NoButtons)
        QDSB1.setAlignment(Qt.AlignHCenter)
        self.table.setCellWidget(1, self.table.columnCount() - 1, QDSB1)

        pB = QProgressBar()
        pB.setValue(0)
        # pB.setStyleSheet('text-align: center')
        self.table.setCellWidget(2, self.table.columnCount() - 1, pB)

    def deleteLastColumn(self):
        if self.table.columnCount() > 1:
            self.table.removeColumn(self.table.columnCount() - 1)

    def clearTable(self):
        for columnIndex in range(self.table.columnCount() - 1, 0, -1):
            self.deleteLastColumn()

    def clearProgress(self):
        for columnIndex in range(1, self.table.columnCount()):
            self.table.cellWidget(2, columnIndex).setValue(0)

    def changeTimeUnit(self):
        for count in range(1, self.table.columnCount()):
            val = self.table.cellWidget(1, count).value()
            timeValue = convertTimeUnits(val, self.timeUnit, self.timeUnitCB.currentText())
            self.table.cellWidget(1, count).setValue(timeValue)
        self.timeUnit = self.timeUnitCB.currentText()

    def lockSchedule(self):
        if self.lockScheduleCB.isChecked():
            self.table.setEnabled(False)
            self.addColumnButton.setEnabled(False)
            self.deleteColumnButton.setEnabled(False)
        else:
            self.table.setEnabled(True)
            self.addColumnButton.setEnabled(True)
            self.deleteColumnButton.setEnabled(True)

    def startSchedule(self):
        self.currentPositionPoint = 0
        if self.table.columnCount() < 2:
            return
        self.updateScheduleTimer.start(100)
        self.startButton.setEnabled(False)
        self.addColumnButton.setEnabled(False)
        self.deleteColumnButton.setEnabled(False)
        self.clearProgress()
        self.nextSchedulePoint()

    def nextSchedulePoint(self):
        self.elapsedTimer.restart()
        self.stopTimer(self.moveToNextPositionPointTimer)
        self.currentPositionPoint += 1

        if self.table.columnCount() < 2:
            return
        for count in range(1, self.currentPositionPoint):
            self.table.cellWidget(2, count).setValue(100)
        if self.table.columnCount() - 1 < self.currentPositionPoint:
            return

        motorPos = self.table.cellWidget(0, self.currentPositionPoint).value()
        tVal = self.table.cellWidget(1, self.currentPositionPoint).value()
        timeInMS = convertTimeUnits(tVal, self.timeUnit, "ms")

        setPoint = int(motorPos * self.stepsPerMM)
        self.lastTargetPos = self.targetPos
        self.targetPos = setPoint
        self.updateTargetPos()
        if self.currentMessage != "":
            self.nextMessage = self.encodeFunction("s|PSET|" + str(self.targetPos))
            self.waitForResponseNextMessage = "PSET"
        else:
            self.currentMessage = self.encodeFunction("s|PSET|" + str(self.targetPos))
            self.waitForResponseMessage = "PSET"
            self.sendMessage()

        self.moveToNextPositionPointTimer.timeout.connect(self.nextSchedulePoint)
        self.moveToNextPositionPointTimer.start(int(timeInMS))

    def updateProgress(self):
        if self.table.columnCount() - 1 < self.currentPositionPoint:
            return
        tVal = self.table.cellWidget(1, self.currentPositionPoint).value()
        timeInMS = convertTimeUnits(tVal, self.timeUnit, "ms")
        timerTime = self.elapsedTimer.elapsed()
        if timeInMS == 0:
            return
        self.table.cellWidget(2, self.currentPositionPoint).setValue(round((timerTime / timeInMS) * 100.0))

    def stopSchedule(self):
        self.stopTimer(self.moveToNextPositionPointTimer)
        self.updateScheduleTimer.stop()
        self.currentPositionPoint = 0
        self.startButton.setEnabled(True)
        self.addColumnButton.setEnabled(True)
        self.deleteColumnButton.setEnabled(True)

    def resetSchedule(self):
        self.stopTimer(self.moveToNextPositionPointTimer)
        self.currentPositionPoint = 0
        self.stopSchedule()
        self.clearProgress()

    def stopTimer(self, timer: QTimer):
        timer.stop()
        try:
            timer.disconnect()
        except TypeError:
            pass

    def sendMessage(self):
        if self.currentMessage == "":
            self.stopTimer(self.resendMessageTimer)
            self.stopTimer(self.failedResendMessageTimer)
            return
        if not self.startedSendingMessage:
            self.startedSendingMessage = True
            self.stopTimer(self.resendMessageTimer)
            self.stopTimer(self.failedResendMessageTimer)
            self.sendData(self.currentMessage)
            # SEND
            self.failedResendMessageTimer.start(11000)
            self.failedResendMessageTimer.timeout.connect(self.failedResendNewMessage)
            self.resendMessageTimer.start(2525)
            self.resendMessageTimer.timeout.connect(self.resendNewMessage)
        else:
            self.sendData(self.currentMessage)

    def resendNewMessage(self):
        self.failedSendingLabel.setStyleSheet("color: yellow")
        self.failedSendingLabel.setText("Failed to send message! Try again...")
        self.sendMessage()

    def failedResendNewMessage(self):
        self.failedSendingLabel.setStyleSheet("color: red")
        self.failedSendingLabel.setText("Failed catastrophically to send message!")
        self.stopTimer(self.resendMessageTimer)
        self.stopTimer(self.failedResendMessageTimer)
        self.currentMessage = ""
        self.waitForResponseMessage = ""
        self.startedSendingMessage = False
        if self.nextMessage != "":
            self.currentMessage = self.nextMessage
            self.waitForResponseMessage = self.waitForResponseNextMessage
            self.nextMessage = ""
            self.waitForResponseNextMessage = ""
            self.sendMessage()

    def sendPositionSetMessage(self):
        if self.currentMessage != "":
            self.nextMessage = self.encodeFunction("s|PSET|" + str(self.targetPos))
            self.waitForResponseNextMessage = "PSET"
        else:
            self.currentMessage = self.encodeFunction("s|PSET|" + str(self.targetPos))
            self.waitForResponseMessage = "PSET"
            self.sendMessage()

    def sendMoveUpMessage(self):
        upSteps = self.moveUpValueSB.value()
        if self.moveUpUnitSB.currentText() == "mm":
            upSteps = int(upSteps * self.stepsPerMM)
        elif self.moveUpUnitSB.currentText() == "degrees":
            upSteps = round(float(upSteps) / 360.0 * float(self.stepsPerRev))
        elif self.moveUpUnitSB.currentText() == "revolutions":
            upSteps = int(upSteps * self.stepsPerRev)
        self.lastTargetPos = self.targetPos
        self.targetPos = int(self.targetPos + upSteps)
        self.updateTargetPos()
        self.sendPositionSetMessage()

    def sendMoveDownMessage(self):
        downSteps = self.moveDownValueSB.value()
        if self.moveDownUnitSB.currentText() == "mm":
            downSteps = int(downSteps * self.stepsPerMM)
        elif self.moveDownUnitSB.currentText() == "degrees":
            downSteps = round(float(downSteps) / 360.0 * float(self.stepsPerRev))
        elif self.moveDownUnitSB.currentText() == "revolutions":
            downSteps = int(downSteps * self.stepsPerRev)
        self.lastTargetPos = self.targetPos
        self.targetPos = int(self.targetPos - downSteps)
        self.updateTargetPos()
        self.sendPositionSetMessage()

    def sendLastTargetMessage(self):
        setPoint = self.lastTargetPos
        self.targetPos = setPoint
        self.updateTargetPos()

        if self.currentMessage != "":
            self.nextMessage = self.encodeFunction("s|PSET|" + str(self.targetPos))
            self.waitForResponseNextMessage = "PSET"
        else:
            self.currentMessage = self.encodeFunction("s|PSET|" + str(self.targetPos))
            self.waitForResponseMessage = "PSET"
            self.sendMessage()

    def setPositionToMessage(self):
        setPoint = self.setPosToValueSB.value() * self.stepsPerMM
        self.lastTargetPos = self.targetPos
        self.targetPos = setPoint
        self.updateTargetPos()

        if self.currentMessage != "":
            self.nextMessage = self.encodeFunction("s|APSET|" + str(self.targetPos)) + self.encodeFunction(
                "s|PSET|" + str(self.targetPos))
            self.waitForResponseNextMessage = "APSET"
        else:
            self.currentMessage = self.encodeFunction("s|APSET|" + str(self.targetPos)) + self.encodeFunction(
                "s|PSET|" + str(self.targetPos))
            self.waitForResponseMessage = "APSET"
            self.sendMessage()

    def moveToMessage(self):
        setPoint = int(self.moveToPosValueSB.value() * self.stepsPerMM)
        self.lastTargetPos = self.targetPos
        self.targetPos = setPoint
        self.updateTargetPos()

        if self.currentMessage != "":
            self.nextMessage = self.encodeFunction("s|PSET|" + str(self.targetPos))
            self.waitForResponseNextMessage = "PSET"
        else:
            self.currentMessage = self.encodeFunction("s|PSET|" + str(self.targetPos))
            self.waitForResponseMessage = "PSET"
            self.sendMessage()

    def sendCalibrationMessage(self):
        if self.currentMessage != "":
            self.nextMessage = self.encodeFunction("s|KAL")
            self.waitForResponseNextMessage = "KAL"
        else:
            self.currentMessage = self.encodeFunction("s|KAL")
            self.waitForResponseMessage = "KAL"
            self.sendMessage()

    def updateTargetPos(self):
        self.targetPosLabel.setText("{:.2f}".format((float(self.targetPos) / float(self.stepsPerMM))) + " mm")

    def readFile(self):
        self.clearTable()

        fname = QFileDialog.getOpenFileName(self, "Open file",
                                            os.path.realpath(__file__),
                                            "Input file (*.txt)")
        if fname[0] == "":
            return
        f = open(fname[0], 'r')
        fileLines = f.readlines()
        for line in fileLines:
            commands = line.split()
            if len(commands) <= 1:
                continue
            if commands[0].upper() == "SPEED":
                if isInt(commands[1]):
                    self.motorSpeed = int(commands[1])
            elif commands[0].upper() == "MIN":
                if isInt(commands[1]):
                    self.minPos = int(commands[1])
            elif commands[0].upper() == "MAX":
                if isInt(commands[1]):
                    self.maxPos = int(commands[1])
            elif commands[0].upper() == "REVERSE":
                if commands[1].upper() == "TRUE":
                    self.reverseDirection = True
                elif commands[1].upper() == "FALSE":
                    self.reverseDirection = False
            elif commands[0].upper() == "STEPSPERREVOLUTION":
                if isInt(commands[1]):
                    self.stepsPerRev = int(commands[1])
            elif commands[0].upper() == "STEPSPERMM":
                if isInt(commands[1]):
                    self.stepsPerMM = int(commands[1])
            elif commands[0].upper() == "CONTROLREFRESHTIME":
                if isInt(commands[1]):
                    self.controlRefreshTime = int(commands[1])

            if len(commands) <= 2:
                continue
            if isInt(commands[0]) and isFloat(commands[1]):
                if commands[2].upper() == "S" or commands[2].upper() == "MIN" or commands[2].upper() == "H":
                    motorPosition = int(commands[0])
                    timeVal = convertTimeUnits(float(commands[1]), commands[2].lower(), self.timeUnit)
                    self.addColumn()
                    self.table.cellWidget(0, self.table.columnCount()-1).setValue(motorPosition)
                    self.table.cellWidget(1, self.table.columnCount()-1).setValue(timeVal)




        self.adjustMinMaxPos()
        self.sendMotorOptionsMessage()

    def encodeFunction(self, functionString: str):
        fString = functionString + "|"
        checkSum = 0
        for c in fString:
            checkSum += ord(c)
        lastChar = chr(90 - (checkSum % 26))
        return "<" + fString + lastChar + ">"

    def decodeFunction(self, functionString: str):
        if functionString.find("<") < 0 or functionString.find(">") < 0 or functionString.find(
                "<") > functionString.find(">"):
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
        return functionString.find("<") != -1 and functionString.find(">") != -1 and functionString.find(
            "<") < functionString.find(">")

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

    def changeRpmToDelay(self, rpmValue):
        return round(1000000.0 / (float(rpmValue) / 60.0) / float(2 * self.stepsPerRev))

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
