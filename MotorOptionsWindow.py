from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class MotorOptionsWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Motor options")

        # __________ Motor Option Labels __________
        controlStateLabel = QLabel("Control state")
        motorAccLabel = QLabel("Motor acceleration")
        motorSpeedFastLabel = QLabel("Fast")
        motorSpeedMediumLabel = QLabel("Medium")
        motorSpeedSlowLabel = QLabel("Slow")
        motorDistMediumLabel = QLabel("Away")
        motorDistCloseLabel = QLabel("Medium")
        motorDistOnPointLabel = QLabel("Close")
        minPressureLabel = QLabel("Minimum pressure [Pa]")
        maxPressureLabel = QLabel("Maximum pressure [Pa]")
        motorControlRefreshLabel = QLabel("Control refresh")

        # __________ Motor Options Widgets __________
        self.controlStateCB = QComboBox()
        self.controlStateCB.addItem("FORCED BLOW OFF")
        self.controlStateCB.addItem("VALVE BLOW OFF")
        self.controlStateCB.addItem("SOLENOID BLOW OFF")

        self.motorAccelerationSpinBox = QSpinBox()
        self.motorAccelerationSpinBox.setRange(0, 255)

        self.motorSpeedFastSpinBox = QSpinBox()
        self.motorSpeedFastSpinBox.setRange(0, 255)
        self.motorSpeedMediumSpinBox = QSpinBox()
        self.motorSpeedMediumSpinBox.setRange(0, 255)
        self.motorSpeedSlowSpinBox = QSpinBox()
        self.motorSpeedSlowSpinBox.setRange(0, 255)

        self.motorDistMediumSpinBox = QSpinBox()
        self.motorDistMediumSpinBox.setRange(0, 400)
        self.motorDistCloseSpinBox = QSpinBox()
        self.motorDistCloseSpinBox.setRange(0, 400)
        self.motorDistOnPointSpinBox = QSpinBox()
        self.motorDistOnPointSpinBox.setRange(0, 400)

        self.minPressureSpinBox = QSpinBox()
        self.minPressureSpinBox.setRange(100000, 1000000)
        self.maxPressuerSpinBox = QSpinBox()
        self.maxPressuerSpinBox.setRange(100000, 1000000)

        self.motorControlRefreshSpinBox = QSpinBox()
        self.motorControlRefreshSpinBox.setRange(0, 1000)

        motorSpeedLayout = QGridLayout()
        motorSpeedLayout.addWidget(motorSpeedFastLabel, 0, 0)
        motorSpeedLayout.addWidget(self.motorSpeedFastSpinBox, 1, 0)
        motorSpeedLayout.addWidget(motorSpeedMediumLabel, 0, 1)
        motorSpeedLayout.addWidget(self.motorSpeedMediumSpinBox, 1, 1)
        motorSpeedLayout.addWidget(motorSpeedSlowLabel, 0, 2)
        motorSpeedLayout.addWidget(self.motorSpeedSlowSpinBox, 1, 2)

        motorSpeedGroupBox = QGroupBox("Motor speed")
        motorSpeedGroupBox.setLayout(motorSpeedLayout)

        motorDistLayout = QGridLayout()
        motorDistLayout.addWidget(motorDistMediumLabel, 0, 0)
        motorDistLayout.addWidget(self.motorDistMediumSpinBox, 1, 0)
        motorDistLayout.addWidget(motorDistCloseLabel, 0, 1)
        motorDistLayout.addWidget(self.motorDistCloseSpinBox, 1, 1)
        motorDistLayout.addWidget(motorDistOnPointLabel, 0, 2)
        motorDistLayout.addWidget(self.motorDistOnPointSpinBox, 1, 2)

        motorDistGroupBox = QGroupBox("Distance to target")
        motorDistGroupBox.setLayout(motorDistLayout)

        minMaxPressureLayout = QGridLayout()
        minMaxPressureLayout.addWidget(minPressureLabel, 0, 0)
        minMaxPressureLayout.addWidget(self.minPressureSpinBox, 1, 0)
        minMaxPressureLayout.addWidget(maxPressureLabel, 0, 1)
        minMaxPressureLayout.addWidget(self.maxPressuerSpinBox, 1, 1)

        minMaxPressureGroupBox = QGroupBox("Pressure requirements")
        minMaxPressureGroupBox.setLayout(minMaxPressureLayout)

        motorOptionsLayout = QGridLayout()
        motorOptionsLayout.setSpacing(10)
        motorOptionsLayout.addWidget(controlStateLabel, 0, 0)
        motorOptionsLayout.addWidget(self.controlStateCB, 0, 1)
        motorOptionsLayout.addWidget(motorAccLabel, 1, 0)
        motorOptionsLayout.addWidget(self.motorAccelerationSpinBox, 1, 1)
        motorOptionsLayout.addWidget(motorSpeedGroupBox, 2, 0, 1, 2)
        motorOptionsLayout.addWidget(motorDistGroupBox, 3, 0, 1, 2)
        motorOptionsLayout.addWidget(minMaxPressureGroupBox, 4, 0, 1, 2)
        motorOptionsLayout.addWidget(motorControlRefreshLabel, 5, 0)
        motorOptionsLayout.addWidget(self.motorControlRefreshSpinBox, 5, 1)



        # __________ Submit Button Layout __________
        self.cancelButton = QPushButton("Cancel")
        self.applyButton = QPushButton("Apply")
        self.okButton = QPushButton("OK")
        self.okButton.setAutoDefault(True)
        QTimer.singleShot(0, self.okButton.setFocus)

        submitButtonLayout = QHBoxLayout()
        submitButtonLayout.setContentsMargins(0, 30, 0, 0)
        submitButtonLayout.addWidget(self.okButton)
        submitButtonLayout.addWidget(self.applyButton)
        submitButtonLayout.addWidget(self.cancelButton)


        # __________ Main Grid Layout __________
        gridLayout = QGridLayout()
        gridLayout.addLayout(motorOptionsLayout, 0, 0)
        gridLayout.addLayout(submitButtonLayout, 1, 0)

        self.setLayout(gridLayout)

        # __________ QPushButton Function __________
        self.cancelButton.clicked.connect(self.close)