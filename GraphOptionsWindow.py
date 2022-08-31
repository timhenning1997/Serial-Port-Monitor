import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from SerialParameters import SerialParameters
from UsefulFunctions import isInt, returnInt, returnFloat, isFloat
from FindDataOptionsWindow import FindDataOptionsWindow


class GraphOptionsWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.dataOptionsWindow = FindDataOptionsWindow()

        self.setWindowTitle("Graph options")

        # __________ Graph Option Group Box __________
        graphTitleLabel = QLabel("Title")
        graphTitleSizeLabel = QLabel("Title size")
        axisXTextLabel = QLabel("X_axis")
        axisYTextLabel = QLabel("Y_axis")
        axisTextSizeLabel = QLabel("Axis size")
        showLegendLable = QLabel("Show legend")
        showGridLable = QLabel("Show grid")
        showValuesLabel = QLabel("Show values")
        plotValueLabel = QLabel("Plot")
        plotUpdateLabel = QLabel("Plot update")
        findDataLabel = QLabel("")


        self.graphTitleLineEdit = QLineEdit()
        self.graphTitleSizeSpinBox = QSpinBox()
        self.graphTitleSizeSpinBox.setRange(1, 100)
        self.axisXTextLineEdit = QLineEdit()
        self.axisYTextLineEdit = QLineEdit()
        self.axisTextSizeSpinBox = QSpinBox()
        self.axisTextSizeSpinBox.setRange(1, 100)
        self.showGridCB = QCheckBox()
        self.showLegendCB = QCheckBox()
        self.showValuesCombobox = QComboBox()
        self.showValuesCombobox.setEditable(True)
        self.showValuesCombobox.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        self.showValuesCombobox.addItem("all")
        self.showValuesCombobox.addItem("10")
        self.showValuesCombobox.addItem("20")
        self.showValuesCombobox.addItem("50")
        self.showValuesCombobox.addItem("100")
        self.showValuesCombobox.addItem("200")
        self.showValuesCombobox.addItem("500")
        self.showValuesCombobox.addItem("1000")
        self.showValuesCombobox.addItem("2000")
        self.showValuesCombobox.addItem("5000")
        self.showValuesCombobox.addItem("10000")
        self.showValuesCombobox.setCurrentText("all")

        self.plotValueCombobox = QComboBox()
        self.plotValueCombobox.addItem("Index")
        self.plotValueCombobox.addItem("Time")
        self.plotValueCombobox.addItem("Value")

        self.plotUpdateCombobox = QComboBox()
        self.plotUpdateCombobox.addItem("On input")
        self.plotUpdateCombobox.addItem("30ms")
        self.plotUpdateCombobox.addItem("50ms")
        self.plotUpdateCombobox.addItem("100ms")
        self.plotUpdateCombobox.addItem("200ms")
        self.plotUpdateCombobox.addItem("500ms")
        self.plotUpdateCombobox.addItem("1s")
        self.plotUpdateCombobox.addItem("2s")
        self.plotUpdateCombobox.addItem("5s")
        self.plotUpdateCombobox.addItem("10s")
        self.plotUpdateCombobox.addItem("20s")
        self.plotUpdateCombobox.addItem("30s")
        self.plotUpdateCombobox.addItem("1m")
        self.plotUpdateCombobox.addItem("2m")
        self.plotUpdateCombobox.addItem("5m")
        self.plotUpdateCombobox.addItem("10m")

        self.findDataButton = QPushButton("Data options")
        self.findDataButton.clicked.connect(self.openDataOptionsWindow)

        graphOptionsLayout = QFormLayout()
        graphOptionsLayout.addRow(graphTitleLabel, self.graphTitleLineEdit)
        graphOptionsLayout.addRow(graphTitleSizeLabel, self.graphTitleSizeSpinBox)
        graphOptionsLayout.addRow(axisXTextLabel, self.axisXTextLineEdit)
        graphOptionsLayout.addRow(axisYTextLabel, self.axisYTextLineEdit)
        graphOptionsLayout.addRow(axisTextSizeLabel, self.axisTextSizeSpinBox)
        graphOptionsLayout.addRow(showGridLable, self.showGridCB)
        graphOptionsLayout.addRow(showLegendLable, self.showLegendCB)
        graphOptionsLayout.addRow(showValuesLabel, self.showValuesCombobox)
        graphOptionsLayout.addRow(plotValueLabel, self.plotValueCombobox)
        graphOptionsLayout.addRow(plotUpdateLabel, self.plotUpdateCombobox)
        graphOptionsLayout.addRow(findDataLabel, self.findDataButton)

        graphOptionsGroupbox = QGroupBox("Graph options")
        graphOptionsGroupbox.setLayout(graphOptionsLayout)

        # __________ Line Option Group Box __________
        self.tabwidget = QTabWidget(self)

        linesOptionsLayout = QVBoxLayout()
        linesOptionsLayout.addWidget(self.tabwidget)

        linesOptionsGroupbox = QGroupBox("Lines options")
        linesOptionsGroupbox.setLayout(linesOptionsLayout)


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
        gridLayout.addWidget(graphOptionsGroupbox, 0, 0, 1, 1)
        gridLayout.addWidget(linesOptionsGroupbox, 0, 1, 1, 1)
        gridLayout.addLayout(submitButtonLayout, 1, 1, 1, 1)

        self.setLayout(gridLayout)

        # __________ QPushButton Function __________
        self.cancelButton.clicked.connect(self.close)

    def openDataOptionsWindow(self):
        self.dataOptionsWindow.okButton.clicked.connect(lambda: self.getDataParametersAndClose(self.dataOptionsWindow))
        self.dataOptionsWindow.show()

    def getDataOptionsParameters(self, window: FindDataOptionsWindow):
        pass

    def getDataParametersAndClose(self, window: FindDataOptionsWindow):
        self.getDataOptionsParameters(window)
        window.close()

    def closeEvent(self, event):
        self.dataOptionsWindow.close()