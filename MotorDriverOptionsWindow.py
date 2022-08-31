from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class MotorDriverOptionsWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Motor options")

        # __________ Motor Option Labels __________
        speedLabel = QLabel("Speed [rpm]")
        minPosLabel = QLabel("Min Pos [mm]")
        maxPosLabel = QLabel("Max Pos [mm]")
        stepsPerRevLabel = QLabel("Steps per revolution")
        stepsPerMMLabel = QLabel("Steps per mm")
        controlRefreshLabel = QLabel("Control refresh")

        # __________ Motor Options Widgets __________
        self.motorSpeedSpinBox = QSpinBox()
        self.motorSpeedSpinBox.setRange(1, 10000000)

        self.minPosSpinBox = QSpinBox()
        self.minPosSpinBox.setRange(0, 10000000)
        self.maxPosSpinBox = QSpinBox()
        self.maxPosSpinBox.setRange(0, 10000000)

        self.reverseDirCB = QCheckBox("reverse Direction")

        self.stepsPerRevSpinBox = QSpinBox()
        self.stepsPerRevSpinBox.setRange(0, 10000000)

        self.stepsPerMMSpinBox = QSpinBox()
        self.stepsPerMMSpinBox.setRange(0, 10000000)

        self.controlRefreshSpinBox = QSpinBox()
        self.controlRefreshSpinBox.setRange(0, 10000)


        optionsLayout = QGridLayout()
        optionsLayout.addWidget(speedLabel, 0, 0)
        optionsLayout.addWidget(self.motorSpeedSpinBox, 0, 1)
        optionsLayout.addWidget(minPosLabel, 1, 0)
        optionsLayout.addWidget(self.minPosSpinBox, 1, 1)
        optionsLayout.addWidget(maxPosLabel, 2, 0)
        optionsLayout.addWidget(self.maxPosSpinBox, 2, 1)
        optionsLayout.addWidget(self.reverseDirCB, 3, 1)
        optionsLayout.addWidget(stepsPerRevLabel, 5, 0)
        optionsLayout.addWidget(self.stepsPerRevSpinBox, 5, 1)
        optionsLayout.addWidget(stepsPerMMLabel, 6, 0)
        optionsLayout.addWidget(self.stepsPerMMSpinBox, 6, 1)
        optionsLayout.addWidget(controlRefreshLabel, 7, 0)
        optionsLayout.addWidget(self.controlRefreshSpinBox, 7, 1)


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
        gridLayout.addLayout(optionsLayout, 0, 0)
        gridLayout.addLayout(submitButtonLayout, 1, 0)

        self.setLayout(gridLayout)

        # __________ QPushButton Function __________
        self.cancelButton.clicked.connect(self.close)