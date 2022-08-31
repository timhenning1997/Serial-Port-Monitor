import math
import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from SerialParameters import SerialParameters
from UsefulFunctions import convertPressureUnits


class PressureScheduleWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Schedule creator")

        # __________ Motor Option Labels __________
        pressureFromLabel = QLabel("From pressure")
        pressureToLabel = QLabel("To pressure")
        lengthOfStayLabel = QLabel("Length of stay")
        hysteresisLabel = QLabel("Hysteresis")

        # __________ Motor Options Widgets __________
        self.fromPressureSpinBox = QDoubleSpinBox()
        self.fromPressureSpinBox.setRange(0, 1000000)
        self.fromPressureSpinBox.valueChanged.connect(self.changeSpacingSpinBoxes)
        self.fromPressureUnitCB = QComboBox()
        self.fromPressureUnitCB.addItem("Pa")
        self.fromPressureUnitCB.addItem("kPa")
        self.fromPressureUnitCB.addItem("MPa")
        self.fromPressureUnitCB.addItem("bar")
        self.fromPressureUnitCB.currentTextChanged.connect(self.changeSpacingSpinBoxes)
        self.toPressureSpinBox = QDoubleSpinBox()
        self.toPressureSpinBox.setRange(0, 1000000)
        self.toPressureSpinBox.valueChanged.connect(self.changeSpacingSpinBoxes)
        self.toPressureUnitCB = QComboBox()
        self.toPressureUnitCB.addItem("Pa")
        self.toPressureUnitCB.addItem("kPa")
        self.toPressureUnitCB.addItem("MPa")
        self.toPressureUnitCB.addItem("bar")
        self.toPressureUnitCB.currentTextChanged.connect(self.changeSpacingSpinBoxes)

        self.spacingSpinBox = QDoubleSpinBox()
        self.spacingSpinBox.setRange(-100000000, 100000000)
        self.spacingSpinBox.valueChanged.connect(self.changeSpacingSpinBoxes)
        self.spacingUnitCB = QComboBox()
        self.spacingUnitCB.addItem("Pa")
        self.spacingUnitCB.addItem("kPa")
        self.spacingUnitCB.addItem("MPa")
        self.spacingUnitCB.addItem("bar")
        self.spacingUnitCB.currentTextChanged.connect(self.changeSpacingSpinBoxes)
        self.stepsCountSpinBox = QSpinBox()
        self.stepsCountSpinBox.setRange(1, 1000)
        self.stepsCountSpinBox.valueChanged.connect(self.changeSpacingSpinBoxes)
        self.spacingRB = QRadioButton("Spacing")
        self.stepsCountRB = QRadioButton("Pressure steps")
        self.spacingRB.toggled.connect(self.toggleSpacingRB)
        self.stepsCountRB.toggled.connect(self.toggleSpacingRB)
        self.spacingRB.setChecked(True)
        spacingGroup = QButtonGroup()
        spacingGroup.addButton(self.spacingRB)
        spacingGroup.addButton(self.stepsCountRB)

        self.lengthOfStaySpinBox = QDoubleSpinBox()
        self.lengthOfStaySpinBox.setRange(0, 1000000)
        self.lengthOfStayUnitCB = QComboBox()
        self.lengthOfStayUnitCB.addItem("s")
        self.lengthOfStayUnitCB.addItem("min")
        self.lengthOfStayUnitCB.addItem("h")

        self.hysteresisCheckBox = QCheckBox()

        # __________ Submit Button Layout __________
        self.cancelButton = QPushButton("Cancel")
        self.applyButton = QPushButton("Apply")
        self.okButton = QPushButton("OK")
        self.okButton.setAutoDefault(True)
        QTimer.singleShot(0, self.okButton.setFocus)

        submitButtonLayout = QHBoxLayout()
        submitButtonLayout.addWidget(self.okButton)
        submitButtonLayout.addWidget(self.applyButton)
        submitButtonLayout.addWidget(self.cancelButton)


        # __________ Main Grid Layout __________
        gridLayout = QGridLayout()
        gridLayout.addWidget(pressureFromLabel, 0, 0)
        gridLayout.addWidget(self.fromPressureSpinBox, 0, 1)
        gridLayout.addWidget(self.fromPressureUnitCB, 0, 2)
        gridLayout.addWidget(pressureToLabel, 1, 0)
        gridLayout.addWidget(self.toPressureSpinBox, 1, 1)
        gridLayout.addWidget(self.toPressureUnitCB, 1, 2)
        gridLayout.addWidget(self.spacingRB, 2, 0)
        gridLayout.addWidget(self.spacingSpinBox, 2, 1)
        gridLayout.addWidget(self.spacingUnitCB, 2, 2)
        gridLayout.addWidget(self.stepsCountRB, 3, 0)
        gridLayout.addWidget(self.stepsCountSpinBox, 3, 1)
        gridLayout.addWidget(lengthOfStayLabel, 4, 0)
        gridLayout.addWidget(self.lengthOfStaySpinBox, 4, 1)
        gridLayout.addWidget(self.lengthOfStayUnitCB, 4, 2)
        gridLayout.addWidget(hysteresisLabel, 5, 0)
        gridLayout.addWidget(self.hysteresisCheckBox, 5, 1)
        gridLayout.addLayout(submitButtonLayout, 6, 1, 1, 2)

        self.setLayout(gridLayout)

        # __________ QPushButton Function __________
        self.cancelButton.clicked.connect(self.close)

    def toggleSpacingRB(self, checked: bool):
        if not checked:
            return
        self.changeSpacingSpinBoxes()
        if self.sender().text() == "Spacing":
            self.spacingSpinBox.setEnabled(True)
            self.stepsCountSpinBox.setEnabled(False)
        elif self.sender().text() == "Pressure steps":
            self.stepsCountSpinBox.setEnabled(True)
            self.spacingSpinBox.setEnabled(False)

    def changeSpacingSpinBoxes(self):
        if self.stepsCountRB.isChecked():
            toV = self.toPressureSpinBox.value()
            toU = self.toPressureUnitCB.currentText()
            fromV = self.fromPressureSpinBox.value()
            fromU = self.fromPressureUnitCB.currentText()
            stepsV = self.stepsCountSpinBox.value()
            spacingValue = (convertPressureUnits(toV, toU) - convertPressureUnits(fromV, fromU)) / stepsV
            self.spacingSpinBox.setValue(convertPressureUnits(spacingValue, "Pa", self.spacingUnitCB.currentText()))
        else:
            toV = self.toPressureSpinBox.value()
            toU = self.toPressureUnitCB.currentText()
            fromV = self.fromPressureSpinBox.value()
            fromU = self.fromPressureUnitCB.currentText()
            spacingV = self.spacingSpinBox.value()
            spacingU = self.spacingUnitCB.currentText()
            if spacingV != 0:
                stepsValue = math.ceil((convertPressureUnits(toV, toU) - convertPressureUnits(fromV, fromU)) / convertPressureUnits(spacingV, spacingU))
                self.stepsCountSpinBox.setValue(stepsValue)
