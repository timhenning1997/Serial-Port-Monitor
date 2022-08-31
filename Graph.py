import os
import random
import time
import uuid

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt5.QtGui import QColor, QPalette, QFont
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QApplication, QVBoxLayout, QRadioButton, QCheckBox, QPushButton, \
    QFileDialog, QFormLayout, QWidget, QLabel, QLineEdit, QSpinBox, QColorDialog, QGroupBox, QTableWidget, QMessageBox, \
    QSplitter, QDoubleSpinBox
from pyqtgraph import PlotWidget, mkPen, exporters
from datetime import datetime

from CalibrationFileLabel import CalibrationFileLabel
from CalibrationFilePushButton import CalibrationFilePushButton
from Tab import Tab
from SerialParameters import SerialParameters
from GraphOptionsWindow import GraphOptionsWindow
from UsefulFunctions import *
from CalibrationOfData import *
from FindDataOptionsWindow import FindDataOptionsWindow


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


class GraphLine:
    def __init__(self, name: str, timestamp=None):
        self.name = name
        self.x = []
        self.x_time = []
        self.x_index = []
        self.y = []
        self.dataLine = None

        self.id = str(uuid.uuid1())

        self.visible = True
        self.lineColor = QColor(255, 0, 0, 255)
        self.lineWidth = 1
        self.lineStyle = Qt.PenStyle.SolidLine
        self.symbol = None  # '+'
        self.symbolBrush = QColor(0, 0, 255, 255)
        self.symbolPen = QColor(0, 0, 0, 0)
        self.symbolSize = 12
        self.fillLevel = None
        self.fillLevelBrush = QColor(120, 120, 120, 100)
        self.maxValueCount = 300
        self.timestamp = timestamp
        self.changed = False

    def appendDataPoint(self, y: float, x: float = -1):
        if len(self.x) > self.maxValueCount > 0:
            self.x = self.x[-self.maxValueCount:]
            self.x_time = self.x_time[-self.maxValueCount:]
            self.x_index = self.x_index[-self.maxValueCount:]
            self.x.append(x)

            if self.timestamp is not None:
                self.x_time.append(datetime.now().timestamp() - self.timestamp)
            else:
                self.x_time.append(datetime.now().timestamp())

            if len(self.x_index) > 0:
                self.x_index.append(self.x_index[-1] + 1)
            else:
                self.x_index.append(0)

            self.y = self.y[-self.maxValueCount:]
            self.y.append(y)
        else:
            self.x.append(x)

            if self.timestamp is not None:
                self.x_time.append(datetime.now().timestamp() - self.timestamp)
            else:
                self.x_time.append(datetime.now().timestamp())
            if len(self.x_index) > 0:
                self.x_index.append(self.x_index[-1] + 1)
            else:
                self.x_index.append(0)
            self.y.append(y)


class Graph(Tab):
    renameTabSignal = pyqtSignal()

    def __init__(self, name, connectedPorts: list = None, port: str = "ALL", parent=None):
        super().__init__("Graph", name, port, parent)

        self.connectedPorts = connectedPorts
        self.port = port
        self.dataFindMethod = "Automatic"

        self.graphLines: list[GraphLine] = []
        self.title = None
        self.titleSize = "15pt"
        self.axisLabelText_x = None
        self.axisLabelText_y = None
        self.axisLabelSize = "9pt"
        self.timestamp = datetime.now().timestamp()
        self.maxShownValues = 300
        self.showGridBool = False
        self.showLegendBool = True
        self.plotValueString = "Time"
        self.plotUpdateString = "On input"
        self.plotUpdatetimer = QTimer()
        self.plotUpdatetimer.timeout.connect(self.plotGraph)

        # Colors
        self.backgroundColor = QApplication.palette().color(QPalette.Base)
        self.titleColor = QApplication.palette().color(QPalette.Text)
        self.axisLableColor = QApplication.palette().color(QPalette.Text)
        self.lineColors = [QColor(57, 106, 177),
                           QColor(218, 124, 48),
                           QColor(62, 150, 81),
                           QColor(204, 37, 41),
                           QColor(83, 81, 84),
                           QColor(107, 76, 154),
                           QColor(146, 36, 148)]
        self.colorIndex = 0

        self.axisLabelStyles = {'color': self.axisLableColor, 'font-size': self.axisLabelSize}

        # WU specific
        self.maxRefreshRate = 100  # Hz
        self.lastRefreshTime = 0

        self.wuLayoutshow = False
        self.calibration = CalibrationOfData()
        self.receivedData = []
        self.receivedValueData = []
        self.receivedCalValueData = []
        self.shownType = "Values"

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

        self.optionsButton = QPushButton("Options")
        self.optionsButton.clicked.connect(self.openOptionsWindow)

        self.mouseInteractionCB = QCheckBox("Mouse interaction")
        self.mouseInteractionCB.toggled.connect(self.mouseInteraction)

        self.clearDisplayButton = QPushButton("Clear display")
        self.clearDisplayButton.clicked.connect(self.clearDisplayData)

        self.deleteLinesButton = QPushButton("Delete Lines")
        self.deleteLinesButton.clicked.connect(self.clearAllData)

        optionsLayout = QHBoxLayout()
        optionsLayout.addWidget(self.portCombobox)
        optionsLayout.addWidget(self.baudrateCombobox)
        optionsLayout.addStretch()
        optionsLayout.addWidget(self.optionsButton)
        optionsLayout.addWidget(self.mouseInteractionCB)
        optionsLayout.addStretch()
        optionsLayout.addWidget(self.clearDisplayButton)
        optionsLayout.addWidget(self.deleteLinesButton)

        self.graphWidget = PlotWidget()
        self.graphWidget.addLegend()

        self.shownTypeCB = QComboBox()
        self.shownTypeCB.addItem("Show: Values")
        self.shownTypeCB.addItem("Show: cal. Values")
        self.shownTypeCB.currentTextChanged.connect(self.changeShownType)

        signalFrequencyLabel = QLabel("Signal frequency: ")
        self.signalFrequencySB = QDoubleSpinBox()
        self.signalFrequencySB.setRange(0, 5)
        self.signalFrequencySB.setValue(5)
        self.signalFrequencySB.valueChanged.connect(self.signalFrequencyChanged)
        signalFrequencyUnitLabel = QLabel("Hz")
        signalFrequencyLayout = QHBoxLayout()
        signalFrequencyLayout.addWidget(signalFrequencyLabel)
        signalFrequencyLayout.addWidget(self.signalFrequencySB)
        signalFrequencyLayout.addWidget(signalFrequencyUnitLabel)

        plotDurationLabel = QLabel("Show last minutes: ")
        self.plotDurationSB = QDoubleSpinBox()
        self.plotDurationSB.setRange(0, 1000)
        self.plotDurationSB.setValue(0.67)
        self.plotDurationSB.valueChanged.connect(self.plotDurationChanged)
        plotDurationLayout = QHBoxLayout()
        plotDurationLayout.addWidget(plotDurationLabel)
        plotDurationLayout.addWidget(self.plotDurationSB)

        wuOptionsLayout = QVBoxLayout()
        wuOptionsLayout.addWidget(self.shownTypeCB)
        wuOptionsLayout.addLayout(signalFrequencyLayout)
        wuOptionsLayout.addLayout(plotDurationLayout)
        self.wuOptionsGroupbox = QGroupBox()
        self.wuOptionsGroupbox.setLayout(wuOptionsLayout)

        self.table = QTableWidget(0, 1)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()

        wuSideLayout = QVBoxLayout()
        wuSideLayout.addWidget(self.wuOptionsGroupbox)
        wuSideLayout.addWidget(self.table)

        tempWidget = QWidget()
        tempWidget.setLayout(wuSideLayout)

        self.splitter1H = QSplitter(Qt.Horizontal)
        self.splitter1H.addWidget(self.graphWidget)
        self.splitter1H.addWidget(tempWidget)
        self.splitter1H.setHandleWidth(10)
        self.splitter1H.widget(1).hide()
        graphLayout = QHBoxLayout()
        graphLayout.addWidget(self.splitter1H)

        # graphLayout = QHBoxLayout()
        # graphLayout.addWidget(self.graphWidget)
        # graphLayout.addLayout(wuSideLayout)

        self.loadCalibrationButton = QPushButton("Import Calibration File", self)
        self.loadCalibrationButton.clicked.connect(self.calibrationButtonPressed)
        self.loadCalibrationText = CalibrationFileLabel("No File loaded", self)
        self.loadCalibrationText.setStyleSheet("color: #808080")

        self.exportButton = QPushButton("Save as")
        self.exportButton.clicked.connect(self.exportAs)

        optionsLayout2 = QHBoxLayout()
        optionsLayout2.addWidget(self.loadCalibrationButton)
        optionsLayout2.addWidget(self.loadCalibrationText)
        optionsLayout2.addStretch()
        optionsLayout2.addWidget(self.exportButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(optionsLayout)
        mainLayout.addLayout(graphLayout)
        mainLayout.addLayout(optionsLayout2)
        self.setLayout(mainLayout)

        self.initUI()

        self.changeColors()
        self.mouseInteraction(False)
        self.showGrid(True)
        self.setTitle()
        self.setLabel()

        self.plotGraph()

        # self.setGraphBounds(0, 50)
        # self.graphWidget.plotItem.enableAutoRange(enable=True)
        # self.graphWidget.plotItem.setAutoPan(x=False, y=False)

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

    def changeColors(self):
        self.backgroundColor = QApplication.palette().color(QPalette.Base)
        self.titleColor = QApplication.palette().color(QPalette.Text)
        self.axisLableColor = QApplication.palette().color(QPalette.Text)

        self.graphWidget.setBackground(self.backgroundColor)
        self.graphWidget.setTitle(self.title, color=self.titleColor, size=self.titleSize)
        if self.axisLabelText_y:
            self.graphWidget.setLabel('left',
                                      '<p style="font-size:' + self.axisLabelSize + ';color:' + self.axisLableColor.name() + '">' + self.axisLabelText_y + '</p>')
        if self.axisLabelText_x:
            self.graphWidget.setLabel('bottom',
                                      '<p style="font-size:' + self.axisLabelSize + ';color:' + self.axisLableColor.name() + '">' + self.axisLabelText_x + '</p>')

    def createGraphLine(self, name: str):
        line = GraphLine(name, self.timestamp)

        tempLineColor = self.lineColors[self.colorIndex]
        line.lineColor = tempLineColor
        self.colorIndex += 1
        if self.colorIndex >= len(self.lineColors):
            self.colorIndex = 0

        if not line.visible:
            return
        # pen = mkPen(color=line.lineColor, width=line.lineWidth, style=line.lineStyle)
        pen = mkPen(color=tempLineColor, width=line.lineWidth, style=line.lineStyle)
        line.dataLine = self.graphWidget.plot(line.x, line.y, pen=pen, symbol=line.symbol,
                                              symbolSize=line.symbolSize,
                                              symbolBrush=line.symbolBrush,
                                              symbolPen=line.symbolPen,
                                              fillLevel=line.fillLevel,
                                              brush=line.fillLevelBrush,
                                              name=line.name)
        self.graphLines.append(line)

    def plotGraph(self):
        for line in self.graphLines:
            if line.visible:
                if line.dataLine is not None:
                    if self.maxShownValues is not None and len(line.x) > self.maxShownValues:
                        if self.plotValueString == "Value":
                            line.dataLine.setData(line.x[-self.maxShownValues:], line.y[-self.maxShownValues:])
                        elif self.plotValueString == "Time":
                            line.dataLine.setData(line.x_time[-self.maxShownValues:], line.y[-self.maxShownValues:])
                        elif self.plotValueString == "Index":
                            line.dataLine.setData(line.x_index[-self.maxShownValues:], line.y[-self.maxShownValues:])
                    else:
                        if self.plotValueString == "Value":
                            line.dataLine.setData(line.x, line.y)
                        elif self.plotValueString == "Time":
                            line.dataLine.setData(line.x_time, line.y)
                        elif self.plotValueString == "Index":
                            line.dataLine.setData(line.x_index, line.y)
                if line.changed:
                    line.changed = False
                    self.graphWidget.plotItem.clear()
                    for line in self.graphLines:
                        pen = mkPen(color=line.lineColor, width=line.lineWidth, style=line.lineStyle)
                        if self.plotValueString == "Value":
                            xData = line.x
                        elif self.plotValueString == "Time":
                            xData = line.x_time
                        elif self.plotValueString == "Index":
                            xData = line.x_index

                        line.dataLine = self.graphWidget.plot(xData, line.y, pen=pen, symbol=line.symbol,
                                                              symbolSize=line.symbolSize,
                                                              symbolBrush=line.symbolBrush,
                                                              symbolPen=line.symbolPen,
                                                              fillLevel=line.fillLevel,
                                                              brush=line.fillLevelBrush,
                                                              name=line.name)

    def clearAllData(self):
        self.colorIndex = 0
        for line in self.graphLines:
            if line.dataLine is not None:
                line.dataLine.clear()
                line.x.clear()
                line.x_time.clear()
                line.x_index.clear()
                line.y.clear()
        self.graphLines.clear()
        self.graphWidget.plotItem.clear()
        self.plotGraph()

    def clearDisplayData(self):
        for line in self.graphLines:
            if line.dataLine is not None:
                line.dataLine.clear()
                line.x.clear()
                line.x_time.clear()
                line.x_index.clear()
                line.y.clear()
        self.plotGraph()

    def setGraphBounds(self, xRangeMin=None, xRangeMax=None, yRangeMin=None, yRangeMax=None):
        if xRangeMin is not None and xRangeMax is not None:
            self.graphWidget.setXRange(xRangeMin, xRangeMax, padding=0)
        if yRangeMin is not None and yRangeMax is not None:
            self.graphWidget.setYRange(yRangeMin, yRangeMax, padding=0)

    def mouseInteraction(self, state: bool):
        self.graphWidget.plotItem.setMouseEnabled(x=state)
        self.graphWidget.plotItem.setMouseEnabled(y=state)
        self.graphWidget.plotItem.setMenuEnabled(enableMenu=state, enableViewBoxMenu=state)
        if state:
            self.graphWidget.plotItem.showButtons()
        else:
            self.graphWidget.plotItem.hideButtons()

    def showLegend(self, showBool: bool):
        self.showLegendBool = showBool
        if showBool:
            self.graphWidget.plotItem.legend.show()
        else:
            self.graphWidget.plotItem.legend.hide()

    def showGrid(self, showBool: bool):
        self.showGridBool = showBool
        self.graphWidget.showGrid(x=showBool, y=showBool)

    def setTitle(self):
        self.graphWidget.setTitle(self.title, color=self.titleColor, size=self.titleSize)

    def setLabel(self):
        if self.axisLabelText_y:
            self.graphWidget.setLabel('left',
                                      '<p style="font-size:' + self.axisLabelSize + ';color:' + self.axisLableColor.name() + '">' + self.axisLabelText_y + '</p>')
        else:
            self.graphWidget.setLabel('left', "")
        if self.axisLabelText_x:
            self.graphWidget.setLabel('bottom',
                                      '<p style="font-size:' + self.axisLabelSize + ';color:' + self.axisLableColor.name() + '">' + self.axisLabelText_x + '</p>')
        else:
            self.graphWidget.setLabel('bottom', "")

    def exportAs(self):
        fname = QFileDialog.getSaveFileName(self, 'Save file', 'C:\\Users\\Tim\\Desktop',
                                            "Image files (*.png *.jpg *.tif *.svg *.csv)")
        if fname[0] != '':
            extension = os.path.splitext(fname[0])[1]
            if extension.upper() == ".PNG" or extension.upper() == ".JPG" or extension.upper() == ".TIFF" or extension.upper() == ".TIF":
                exporter = exporters.ImageExporter(self.graphWidget.plotItem)
                exporter.export(fname[0])
            if extension.upper() == ".SVG":
                exporter = exporters.SVGExporter(self.graphWidget.plotItem)
                exporter.export(fname[0])
            if extension.upper() == ".CSV":
                exporter = exporters.CSVExporter(self.graphWidget.plotItem)
                exporter.export(fname[0])

    def openOptionsWindow(self):
        self.optionsWindow = GraphOptionsWindow()
        self.optionsWindow.okButton.clicked.connect(lambda: self.extractParametersAndClose(self.optionsWindow))
        self.optionsWindow.applyButton.clicked.connect(
            lambda: self.extractParametersFromOptionsWindow(self.optionsWindow))
        self.initOptionsWindow(self.optionsWindow)
        self.optionsWindow.show()

    def initOptionsWindow(self, window: GraphOptionsWindow):
        window.graphTitleLineEdit.setText(self.title)
        window.graphTitleSizeSpinBox.setValue(returnInt(self.titleSize.replace("pt", "")))
        window.axisXTextLineEdit.setText(self.axisLabelText_x)
        window.axisYTextLineEdit.setText(self.axisLabelText_y)
        window.axisTextSizeSpinBox.setValue(returnInt(self.axisLabelSize.replace("pt", "")))
        window.showGridCB.setChecked(self.showGridBool)
        window.showLegendCB.setChecked(self.showLegendBool)
        if self.maxShownValues is None:
            window.showValuesCombobox.setCurrentText("all")
        else:
            window.showValuesCombobox.setCurrentText(str(self.maxShownValues))
        window.plotValueCombobox.setCurrentText(self.plotValueString)
        window.plotUpdateCombobox.setCurrentText(self.plotUpdateString)
        window.dataOptionsWindow.dataFindMethodCombobox.setCurrentText(self.dataFindMethod)

        self.initLinesOptionsTabWidget(window)

    def initLinesOptionsTabWidget(self, window: GraphOptionsWindow):
        tabwidget = window.tabwidget
        index = 0
        for line in self.graphLines:
            index += 1

            lineVisibilityLabel = QLabel("Visibility")
            lineTitleLabel = QLabel("Title")
            lineColorLabel = QLabel("Line color")
            lineWidthLabel = QLabel("Line width")
            lineStyleLabel = QLabel("Line style")
            lineSymbolLabel = QLabel("Line symbol")
            lineSymbolColorLabel = QLabel("Symbol color")
            lineSymbolSizeLabel = QLabel("Symbol size")
            lineMaxValueCountLabel = QLabel("Max values")
            lineIDLabel = QLabel("ID")
            lineIDLabel.setFixedHeight(0)

            visibleCB = QCheckBox("")
            visibleCB.setChecked(line.visible)
            lineTitleLineEdit = QLineEdit(line.name)
            lineColorColorPicker = QPushButton(line.lineColor.name())
            lineColorColorPicker.setStyleSheet("background-color : " + line.lineColor.name())
            lineColorColorPicker.clicked.connect(lambda: self.colorPicker(window))
            lineWidthSpinBox = QSpinBox()
            lineWidthSpinBox.setRange(1, 100)
            lineWidthSpinBox.setValue(line.lineWidth)
            lineStyleCombobox = QComboBox()
            lineStyleCombobox.addItem("SolidLine")
            lineStyleCombobox.addItem("DashLine")
            lineStyleCombobox.addItem("DotLine")
            lineStyleCombobox.addItem("DashDotLine")
            lineStyleCombobox.addItem("DashDotDotLine")
            if line.lineStyle == Qt.PenStyle.SolidLine:
                lineStyleCombobox.setCurrentText("SolidLine")
            elif line.lineStyle == Qt.PenStyle.DashLine:
                lineStyleCombobox.setCurrentText("DashLine")
            elif line.lineStyle == Qt.PenStyle.DotLine:
                lineStyleCombobox.setCurrentText("DotLine")
            elif line.lineStyle == Qt.PenStyle.DashDotLine:
                lineStyleCombobox.setCurrentText("DashDotLine")
            elif line.lineStyle == Qt.PenStyle.DashDotDotLine:
                lineStyleCombobox.setCurrentText("DashDotDotLine")
            lineSymbolCombobox = QComboBox()
            lineSymbolCombobox.addItem("None")
            lineSymbolCombobox.addItem("o")
            lineSymbolCombobox.addItem("t")
            lineSymbolCombobox.addItem("t1")
            lineSymbolCombobox.addItem("t2")
            lineSymbolCombobox.addItem("t3")
            lineSymbolCombobox.addItem("s")
            lineSymbolCombobox.addItem("p")
            lineSymbolCombobox.addItem("h")
            lineSymbolCombobox.addItem("star")
            lineSymbolCombobox.addItem("+")
            lineSymbolCombobox.addItem("d")
            lineSymbolCombobox.addItem("x")
            if line.symbol is None:
                lineSymbolCombobox.setCurrentText("None")
            else:
                lineSymbolCombobox.setCurrentText(line.symbol)
            lineSymbolColorPicker = QPushButton(line.symbolBrush.name())
            lineSymbolColorPicker.setStyleSheet("background-color : " + line.symbolBrush.name())
            lineSymbolColorPicker.clicked.connect(lambda: self.colorPicker2(window))
            lineSymbolWidthSpinBox = QSpinBox()
            lineSymbolWidthSpinBox.setRange(1, 100)
            lineSymbolWidthSpinBox.setValue(line.symbolSize)
            lineMaxValueCountCombobox = QComboBox()
            lineMaxValueCountCombobox.setEditable(True)
            lineMaxValueCountCombobox.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
            lineMaxValueCountCombobox.addItem("All")
            lineMaxValueCountCombobox.addItem("10")
            lineMaxValueCountCombobox.addItem("100")
            lineMaxValueCountCombobox.addItem("1000")
            lineMaxValueCountCombobox.addItem("10000")
            lineMaxValueCountCombobox.addItem("100000")
            lineMaxValueCountCombobox.addItem("1000000")
            if line.maxValueCount == 0:
                lineMaxValueCountCombobox.setCurrentText("All")
            else:
                lineMaxValueCountCombobox.setCurrentText(str(line.maxValueCount))
            lineUUIDLabel = QLabel(line.id)
            lineUUIDLabel.setFixedHeight(0)
            lineUUIDLabel.setFixedWidth(0)

            tabLayout = QFormLayout()
            tabLayout.addRow(lineVisibilityLabel, visibleCB)
            tabLayout.addRow(lineTitleLabel, lineTitleLineEdit)
            tabLayout.addRow(lineColorLabel, lineColorColorPicker)
            tabLayout.addRow(lineWidthLabel, lineWidthSpinBox)
            tabLayout.addRow(lineStyleLabel, lineStyleCombobox)
            tabLayout.addRow(lineSymbolLabel, lineSymbolCombobox)
            tabLayout.addRow(lineSymbolColorLabel, lineSymbolColorPicker)
            tabLayout.addRow(lineSymbolSizeLabel, lineSymbolWidthSpinBox)
            tabLayout.addRow(lineMaxValueCountLabel, lineMaxValueCountCombobox)
            tabLayout.addRow(lineIDLabel, lineUUIDLabel)
            tab = QWidget()
            tab.setLayout(tabLayout)
            tabwidget.addTab(tab, str(index))

    def colorPicker(self, window: GraphOptionsWindow):
        button = window.tabwidget.widget(window.tabwidget.currentIndex()).layout().itemAt(5).widget()
        color = QColorDialog.getColor().name()
        button.setText(color)
        button.setStyleSheet("background-color : " + color)

    def colorPicker2(self, window: GraphOptionsWindow):
        button = window.tabwidget.widget(window.tabwidget.currentIndex()).layout().itemAt(13).widget()
        color = QColorDialog.getColor().name()
        button.setText(color)
        button.setStyleSheet("background-color : " + color)

    def setPlotUpdateTimer(self):
        if self.plotUpdateString == "On input":
            self.plotUpdatetimer.stop()
        elif self.plotUpdateString == "30ms":
            self.plotUpdatetimer.start(30)
        elif self.plotUpdateString == "50ms":
            self.plotUpdatetimer.start(50)
        elif self.plotUpdateString == "100ms":
            self.plotUpdatetimer.start(100)
        elif self.plotUpdateString == "200ms":
            self.plotUpdatetimer.start(200)
        elif self.plotUpdateString == "500ms":
            self.plotUpdatetimer.start(500)
        elif self.plotUpdateString == "1s":
            self.plotUpdatetimer.start(1000)
        elif self.plotUpdateString == "2s":
            self.plotUpdatetimer.start(2000)
        elif self.plotUpdateString == "5s":
            self.plotUpdatetimer.start(5000)
        elif self.plotUpdateString == "10s":
            self.plotUpdatetimer.start(10000)
        elif self.plotUpdateString == "20s":
            self.plotUpdatetimer.start(20000)
        elif self.plotUpdateString == "30s":
            self.plotUpdatetimer.start(30000)
        elif self.plotUpdateString == "1m":
            self.plotUpdatetimer.start(60000)
        elif self.plotUpdateString == "2m":
            self.plotUpdatetimer.start(120000)
        elif self.plotUpdateString == "5m":
            self.plotUpdatetimer.start(300000)
        elif self.plotUpdateString == "10m":
            self.plotUpdatetimer.start(600000)

    def extractParametersFromOptionsWindow(self, window: GraphOptionsWindow):
        self.title = window.graphTitleLineEdit.text()
        if self.title.strip() == "":
            self.title = None
        self.titleSize = str(window.graphTitleSizeSpinBox.value()) + "pt"
        self.axisLabelText_x = window.axisXTextLineEdit.text()
        if self.axisLabelText_x.strip() == "":
            self.axisLabelText_x = None
        self.axisLabelText_y = window.axisYTextLineEdit.text()
        if self.axisLabelText_y.strip() == "":
            self.axisLabelText_y = None
        self.axisLabelSize = str(window.axisTextSizeSpinBox.value()) + "pt"
        self.showGrid(window.showGridCB.isChecked())
        self.showLegend(window.showLegendCB.isChecked())
        self.maxShownValues = None
        if isInt(window.showValuesCombobox.currentText()):
            self.maxShownValues = returnInt(window.showValuesCombobox.currentText())
        self.plotValueString = window.plotValueCombobox.currentText()
        self.plotUpdateString = window.plotUpdateCombobox.currentText()
        self.dataFindMethod = window.dataOptionsWindow.dataFindMethodCombobox.currentText()

        for i in range(0, window.tabwidget.count()):
            layout = window.tabwidget.widget(i).layout()
            uuidLine = layout.itemAt(19).widget().text()
            for line in self.graphLines:
                if line.id == uuidLine:
                    line.changed = True
                    line.visible = layout.itemAt(1).widget().isChecked()
                    line.name = layout.itemAt(3).widget().text()
                    line.lineColor = QColor(layout.itemAt(5).widget().text())
                    line.lineWidth = layout.itemAt(7).widget().value()
                    lineStyle = layout.itemAt(9).widget().currentText()
                    if lineStyle == "SolidLine":
                        line.lineStyle = Qt.PenStyle.SolidLine
                    elif lineStyle == "DashLine":
                        line.lineStyle = Qt.PenStyle.DashLine
                    elif lineStyle == "DotLine":
                        line.lineStyle = Qt.PenStyle.DotLine
                    elif lineStyle == "DashDotLine":
                        line.lineStyle = Qt.PenStyle.DashDotLine
                    elif lineStyle == "DashDotDotLine":
                        line.lineStyle = Qt.PenStyle.DashDotDotLine
                    lineSymbol = layout.itemAt(11).widget().currentText()
                    if lineSymbol == "None":
                        line.symbol = None
                    else:
                        line.symbol = lineSymbol
                    line.symbolBrush = QColor(layout.itemAt(13).widget().text())
                    line.symbolSize = layout.itemAt(15).widget().value()
                    maxValue = layout.itemAt(17).widget().currentText()
                    if maxValue == "All":
                        line.maxValueCount = 0
                    else:
                        if isInt(maxValue):
                            line.maxValueCount = returnInt(maxValue)

        for line in self.graphLines:
            if not line.visible:
                line.dataLine.clear()
                line.x.clear()
                line.x_time.clear()
                line.x_index.clear()
                line.y.clear()

        self.setPlotUpdateTimer()
        self.setTitle()
        self.setLabel()

        self.plotGraph()

    def extractParametersAndClose(self, window: GraphOptionsWindow):
        self.extractParametersFromOptionsWindow(window)
        window.close()

    def deleteLastRow(self):
        if self.table.rowCount() > 0:
            self.table.removeRow(self.table.rowCount() - 1)

    def clearTable(self):
        for rowIndex in range(self.table.rowCount(), 0, -1):
            self.deleteLastRow()

    def receiveData(self, obj: SerialParameters, data):
        if self.portCombobox.currentText() != obj.port and self.portCombobox.currentText() != "COM-ALL":
            return
        if self.baudrateCombobox.currentText() != str(
                obj.baudrate) + " Baud" and self.baudrateCombobox.currentText() != "ALL Baud":
            return

        if self.dataFindMethod == "Automatic":
            self.dataFindAutomaitc(obj, data)
        elif self.dataFindMethod == "Every byte":
            self.dataFindByBytey(data, 1)
        elif self.dataFindMethod == "Every 2 bytes":
            self.dataFindByBytey(data, 2)
        elif self.dataFindMethod == "Every 3 bytes":
            self.dataFindByBytey(data, 3)
        elif self.dataFindMethod == "Every 4 bytes":
            self.dataFindByBytey(data, 4)
        elif self.dataFindMethod == "Every 5 bytes":
            self.dataFindByBytey(data, 5)
        elif self.dataFindMethod == "Every 6 bytes":
            self.dataFindByBytey(data, 6)
        elif self.dataFindMethod == "Every 7 bytes":
            self.dataFindByBytey(data, 7)
        elif self.dataFindMethod == "Every 8 bytes":
            self.dataFindByBytey(data, 8)
        elif self.dataFindMethod == "Every 9 bytes":
            self.dataFindByBytey(data, 9)
        elif self.dataFindMethod == "Every 10 bytes":
            self.dataFindByBytey(data, 10)

        if self.plotUpdateString == "On input":
            self.plotGraph()

    def dataFindAutomaitc(self, obj: SerialParameters, data):
        if obj.readTextIndex == "read_WU_device":
            numberValues = []
            numberNames = []
            if time.time() > self.lastRefreshTime + (1 / self.maxRefreshRate):
                self.lastRefreshTime = time.time()

                if not self.wuLayoutshow:
                    self.splitter1H.widget(1).show()
                    self.wuLayoutshow = True

                checkedCBNames = self.checkWUForNewVars(len(data), obj.port)

                self.receivedValueData = []
                for numberIndex in range(0, len(data)):
                    self.receivedValueData.append(int(data[numberIndex], 16))

                self.receivedCalValueData = []
                if self.calibration.configured:
                    self.receivedCalValueData = self.calibration.calibrate(self.receivedValueData)

                for numberIndex in range(0, len(checkedCBNames)):
                    numberNames.append(checkedCBNames[numberIndex][0])
                    if self.shownType == "cal. Values" and self.calibration.configured:
                        numberValues.append(self.receivedCalValueData[checkedCBNames[numberIndex][1]])
                    else:
                        numberValues.append(self.receivedValueData[checkedCBNames[numberIndex][1]])
        else:
            try:
                rawData = data.decode('utf-8')
            except:
                rawData = str(int.from_bytes(data, "little"))

            splittedData = (rawData.replace(":", " ")
                            .replace(";", " ").replace("|", " ").replace(":", " ").replace("(", " ").replace(")", " ")
                            .replace("[", " ").replace("]", " ").replace("{", " ").replace("}", " ").replace("?", " ")
                            .replace("!", " ").replace("#", " ").replace("\"", " ").replace(",", ".").split())

            numberValues = []
            numberNames = []

            for numberIndex in range(0, len(splittedData)):
                if isFloat(splittedData[numberIndex]):
                    numberName = " "
                    for a in range(numberIndex - 1, -1, -1):
                        if splittedData[a].strip() == "":
                            break
                        if isFloat(splittedData[a]):
                            break
                        numberName = splittedData[a]
                        break
                    numberValues.append(returnFloat(splittedData[numberIndex]))
                    numberNames.append(numberName)

        for count in range(0, len(numberValues)):
            if numberNames[count].strip() != "":
                if not any(x.name == numberNames[count] for x in self.graphLines):
                    self.createGraphLine(numberNames[count])
                    self.graphLines[-1].appendDataPoint(numberValues[count])
                for line in self.graphLines:
                    if line.name == numberNames[count]:
                        line.appendDataPoint(numberValues[count])

    def dataFindByBytey(self, data, byteCount: int):
        splittedData = [data[i:i + byteCount] for i in range(0, len(data), byteCount)]
        for count in range(0, len(splittedData)):
            try:
                rawData = splittedData[count].decode('utf-8')
            except:
                rawData = str(int.from_bytes(splittedData[count], "little"))
            if not isFloat(rawData):
                continue
            if not any(x.name == str(count) for x in self.graphLines):
                self.createGraphLine(str(count))
                self.graphLines[-1].appendDataPoint(returnFloat(rawData))
            for line in self.graphLines:
                if line.name == str(count):
                    line.appendDataPoint(returnFloat(rawData))

    def checkWUForNewVars(self, dataCounter, port: str):
        returnData = []
        checkedtableCBNames = []
        tableCBNames = []
        for count in range(0, self.table.rowCount()):
            tempName = self.table.cellWidget(count, 0).text()
            if self.table.cellWidget(count, 0).isChecked():
                checkedtableCBNames.append(tempName)
            tableCBNames.append(tempName)
        for numberIndex in range(0, dataCounter):
            channelName = port + "_"
            channelName += 'CH' + str(numberIndex)
            if self.calibration.configured:
                channelName += "_" + self.calibration.getName(numberIndex)

            if channelName in checkedtableCBNames:
                returnData.append([channelName, numberIndex])
            if not channelName in tableCBNames:
                QCB = QCheckBox(channelName)
                self.table.insertRow(self.table.rowCount())
                self.table.setCellWidget(self.table.rowCount() - 1, 0, QCB)
        self.table.setColumnWidth(0, self.table.width())

        return returnData

    def calibrationButtonPressed(self):
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
        self.clearTable()

    def dragLabelActivated(self):
        if self.calibration:
            return {"port": None, "path": self.calibration.pathName}
        return {"port": None, "path": None}

    def dropLabelActivated(self, obj):
        if obj["path"] is None:
            return
        self.loadCalibrationFromSaveSettings(obj["path"])

    def changeShownType(self):
        if self.shownTypeCB.currentText() == "Show: Values":
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

    def plotDurationChanged(self):
        self.maxShownValues = int(self.plotDurationSB.value() * 60 * self.signalFrequencySB.value())
        for line in self.graphLines:
            line.maxValueCount = int(self.plotDurationSB.value() * 60 * self.signalFrequencySB.value())

    def signalFrequencyChanged(self):
        self.plotDurationChanged()

    def loadCalibrationFromSaveSettings(self, path):
        if path == "":
            return None

        try:
            if self.calibration.readCalibrationFile(path) is None:
                return
            self.loadCalibrationText.setText(self.calibration.fileName)
            if len(self.receivedValueData) > 0:
                self.receivedCalValueData = self.calibration.calibrate(self.receivedValueData)
            self.shownTypeCB.setCurrentText("Show: cal. Values")
            self.shownType = "cal. Values"
        except:
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
            if os.path.exists(tempSettings["calibrationFilePath"]):
                self.loadCalibrationFromSaveSettings(tempSettings["calibrationFilePath"])

    def saveSettings(self, settings: QSettings = None):
        tempSettings = {"port": self.portCombobox.currentText(),
                        "baud": self.baudrateCombobox.currentText(),
                        "calibrationFilePath": self.calibration.pathName}
        settings.setValue(self.uuid, tempSettings)
