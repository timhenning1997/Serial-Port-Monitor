import uuid

from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtWidgets import *
from UsefulFunctions import resource_path

# Calculation widgets
from Calculation.MassFlowCalculation import MassFlowCalculation
from Calculation.FreeProgrammingCalculation import FreeProgrammingCalculation
from Calculation.WallShearStressCalculation import WallShearStressCalculation
from Calculation.DensityCalculation import DensityCalculation
from Calculation.VelocityCalculation import VelocityCalculation


class CalculationWidget(QWidget):
    def __init__(self, globalVarNames, globalVars, parent=None):
        super().__init__(parent)
        self.uuid = str(uuid.uuid4())
        self.globalVarNames = globalVarNames
        self.globalVars = globalVars
        self.parent = parent
        self.paused = True
        self.widgetWidth = 350
        self.mainWidget = None

        self.calculationTypeCombobox = QComboBox()
        self.calculationTypeCombobox.addItem("Free programming")
        self.calculationTypeCombobox.addItem("Massenstrom")
        self.calculationTypeCombobox.addItem("Wandschub")
        self.calculationTypeCombobox.addItem("Dichte")
        self.calculationTypeCombobox.addItem("Geschwindigkeit")

        self.calculationTypeCombobox.setCurrentText("Free programming")
        self.calculationTypeCombobox.currentTextChanged.connect(self.changeCalculationType)

        self.startCalculationButton = QPushButton()
        self.startCalculationButton.setIcon(QIcon(resource_path("res/Icon/play.ico")))
        self.startCalculationButton.clicked.connect(lambda: self.changePausedState("play"))
        self.stopCalculationButton = QPushButton()
        self.stopCalculationButton.setIcon(QIcon(resource_path("res/Icon/pause.ico")))
        self.stopCalculationButton.clicked.connect(lambda: self.changePausedState("pause"))
        self.closeCalculationButton = QPushButton()
        self.closeCalculationButton.setIcon(QIcon(resource_path("res/Icon/close.ico")))
        self.closeCalculationButton.clicked.connect(lambda: self.changePausedState("close"))
        self.closeCalculationButton.clicked.connect(self.closeWidget)
        self.changePausedState("pause")

        self.contractButton = QPushButton("<")
        self.contractButton.setFixedWidth(15)
        self.contractButton.clicked.connect(self.contractWidget)
        self.expandButton = QPushButton(">")
        self.expandButton.setFixedWidth(15)
        self.expandButton.clicked.connect(self.expandWidget)

        sizeLayout = QHBoxLayout()
        sizeLayout.setSpacing(0)
        sizeLayout.addWidget(self.contractButton)
        sizeLayout.addWidget(self.expandButton)

        self.mainCalculationLayout = QVBoxLayout()
        self.mainWidget = FreeProgrammingCalculation(self.globalVarNames, self.globalVars, self)
        self.mainCalculationLayout.addWidget(self.mainWidget)
        self.setFixedWidth(self.widgetWidth)

        optionsLayout = QHBoxLayout()
        optionsLayout.addLayout(sizeLayout)
        optionsLayout.addWidget(self.calculationTypeCombobox)
        optionsLayout.addStretch()
        optionsLayout.addWidget(self.startCalculationButton)
        optionsLayout.addWidget(self.stopCalculationButton)
        optionsLayout.addWidget(self.closeCalculationButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(optionsLayout)
        mainLayout.addLayout(self.mainCalculationLayout)

        self.setLayout(mainLayout)

    def forcePauseState(self):
        self.changePausedState("pause")

    def changePausedState(self, button: str):
        if button == "play":
            self.paused = False
            self.highlightButtonBackgroupColor("play")
        elif button == "pause":
            self.paused = True
            self.highlightButtonBackgroupColor("pause")
        else:
            self.paused = True
            self.highlightButtonBackgroupColor("close")
        if self.mainWidget:
            self.mainWidget.changePausedState(button)

    def expandWidget(self):
        self.widgetWidth += 30
        self.setFixedWidth(self.widgetWidth)
        self.parent.resizeTableColumns()

    def contractWidget(self):
        self.widgetWidth -= 30
        self.setFixedWidth(self.widgetWidth)
        self.parent.resizeTableColumns()

    def highlightButtonBackgroupColor(self, button: str):
        tempButtonColor = "background-color: " + QApplication.palette().color(QPalette.Button).name()
        self.startCalculationButton.setStyleSheet(tempButtonColor)
        self.stopCalculationButton.setStyleSheet(tempButtonColor)
        self.closeCalculationButton.setStyleSheet(tempButtonColor)

        tempHighlightColor = "background-color: " + QApplication.palette().color(QPalette.ButtonText).name()
        if button == "play":
            self.startCalculationButton.setStyleSheet(tempHighlightColor)
        elif button == "pause":
            self.stopCalculationButton.setStyleSheet(tempHighlightColor)
        else:
            self.closeCalculationButton.setStyleSheet(tempHighlightColor)

    def closeWidget(self):
        self.parent.closeCalculationWidget(self.uuid)

    def changeCalculationType(self):
        self.changePausedState("pause")
        for i in reversed(range(self.mainCalculationLayout.count())):
            self.mainCalculationLayout.itemAt(i).widget().deleteLater()
        if self.calculationTypeCombobox.currentText() == "Free programming":
            self.mainWidget = FreeProgrammingCalculation(self.globalVarNames, self.globalVars, self)
        if self.calculationTypeCombobox.currentText() == "Massenstrom":
            self.mainWidget = MassFlowCalculation(self.globalVarNames, self.globalVars)
        if self.calculationTypeCombobox.currentText() == "Wandschub":
            self.mainWidget = WallShearStressCalculation(self.globalVarNames, self.globalVars)
        if self.calculationTypeCombobox.currentText() == "Dichte":
            self.mainWidget = DensityCalculation(self.globalVarNames, self.globalVars)
        if self.calculationTypeCombobox.currentText() == "Geschwindigkeit":
            self.mainWidget = VelocityCalculation(self.globalVarNames, self.globalVars)

        self.mainCalculationLayout.addWidget(self.mainWidget)
        self.parent.resizeTableColumns()

    def save(self):
        temp = self.mainWidget.save()
        temp["calWidgetWidth"] = self.widgetWidth
        return temp

    def load(self, option):
        self.widgetWidth = option["calWidgetWidth"]
        self.setFixedWidth(self.widgetWidth)
        self.parent.resizeTableColumns()

        self.mainWidget.load(option)

    def calculate(self):
        if not self.paused:
            self.mainWidget.calculate()
