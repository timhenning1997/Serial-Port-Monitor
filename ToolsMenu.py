from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from AvailablePorts import AvailablePorts


class ToolsMenu(QMenu):
    addTerminalSignal = pyqtSignal(str)
    addGraphSignal = pyqtSignal(str)
    addPressureControlPanelSignal = pyqtSignal(str)
    addMotorDriverPanelSignal = pyqtSignal(str)
    addTablePlotterSignal = pyqtSignal(str)
    addVarCalculatorSignal = pyqtSignal(str)
    addMeasurementSignal = pyqtSignal(str)

    def __init__(self, connectedPorts: list, parent=None):
        super(ToolsMenu, self).__init__(parent)
        self.setTitle("&Tools")

        terminalMenu = AvailablePorts(connectedPorts, "&Terminal", parent)
        terminalMenu.actionTriggeredSignal.connect(self.addTerminal)
        self.addMenu(terminalMenu)

        graphMenu = AvailablePorts(connectedPorts, "&Graph", parent)
        graphMenu.actionTriggeredSignal.connect(self.addGraph)
        self.addMenu(graphMenu)

        pressureControlMenu = AvailablePorts(connectedPorts, "&PressureControlPanel", parent)
        pressureControlMenu.actionTriggeredSignal.connect(self.addPressureControlPanel)
        self.addMenu(pressureControlMenu)

        motorDriverMenu = AvailablePorts(connectedPorts, "&MotorDriverPanel", parent)
        motorDriverMenu.actionTriggeredSignal.connect(self.addMotorDriverPanel)
        self.addMenu(motorDriverMenu)
        
        tablePlotterMenu = AvailablePorts(connectedPorts, "&TablePlotter", parent)
        tablePlotterMenu.actionTriggeredSignal.connect(self.addTablePlotter)
        self.addMenu(tablePlotterMenu)

        varCalculatorMenu = AvailablePorts(connectedPorts, "&VarCalculator", parent)
        varCalculatorMenu.actionTriggeredSignal.connect(self.addVarCalculator)
        self.addMenu(varCalculatorMenu)

        measurementMenu = AvailablePorts(connectedPorts, "&Measurement", parent)
        measurementMenu.actionTriggeredSignal.connect(self.addMeasurement)
        self.addMenu(measurementMenu)

        self.disconnectAllAction = QAction("&Disconnect All", self)
        self.addAction(self.disconnectAllAction)

    def addTerminal(self, portName):
        self.addTerminalSignal.emit(portName)

    def addGraph(self, portName):
        self.addGraphSignal.emit(portName)

    def addPressureControlPanel(self, portName):
        self.addPressureControlPanelSignal.emit(portName)

    def addMotorDriverPanel(self, portName):
        self.addMotorDriverPanelSignal.emit(portName)
        
    def addTablePlotter(self, portName):
        self.addTablePlotterSignal.emit(portName)

    def addVarCalculator(self, portName):
        self.addVarCalculatorSignal.emit(portName)

    def addMeasurement(self, portName):
        self.addMeasurementSignal.emit(portName)
