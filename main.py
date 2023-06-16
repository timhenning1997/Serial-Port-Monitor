import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PortMenu import PortMenu
from SerialParameters import SerialParameters
from SerialConnectWindow import SerialConnectWindow
from SerialWorker import SerialThread
from UsefulFunctions import *
from Terminal import Terminal
from Graph import Graph
from PressureControlPanel import PressureControlPanel
from DruckBox2 import DruckBox2
from MotorDriverPanel import MotorDriverPanel
from TablePlotter import TablePlotter
from VarCalculator import VarCalculator
from Measurement import Measurement
from TabWidget import TabWidget
import serial
import LayoutHandler
from LayoutMenu import LayoutMenu
from ColorThemesMenu import ColorThemesMenu
from ToolsMenu import ToolsMenu
from ColorSchemeHandler import ColorSchemeHandler
from time import sleep


class MainWindow(QMainWindow):
    """This is the main class

    Args:
        QMainWindow ([type]): This is the main Argument
    """
    sendSerialWriteSignal = pyqtSignal(str, object)
    killSerialConnectionSignal = pyqtSignal(str)
    pauseSerialConnectionSignal = pyqtSignal(str)
    resumeSerialConnectionSignal = pyqtSignal(str)
    startSerialRecordSignal = pyqtSignal(str, str, str)
    stopSerialRecordSignal = pyqtSignal(str)
    pauseSerialRecordSignal = pyqtSignal(str)
    resumeSerialRecordSignal = pyqtSignal(str)
    writeToFileSignal = pyqtSignal(str, str, str, str)

    madeSerialConnectionSignal = pyqtSignal(object)
    lostSerialConnectionSignal = pyqtSignal(object)
    receiveSerialDataSignal = pyqtSignal(object, object)
    failedSendSerialDataSignal = pyqtSignal(object, object)

    def __init__(self):
        super().__init__()

        # Settings
        self.settings = QSettings('TimSoft', 'Serial Port Monitor')

        # Shortcuts
        self.quitSc = QShortcut(QKeySequence('Ctrl+Q'), self)
        self.quitSc.activated.connect(self.close)


        QThreadPool.setMaxThreadCount(QThreadPool.globalInstance(), 8)


        self.tabWidgets = []
        self.connectedPorts = []
        self.layout = "1x1"

        self.colorSchemeHandler = ColorSchemeHandler(self)

        self.menuBar()
        portMenu = PortMenu(self.connectedPorts, self)
        portMenu.connectActionTriggeredSignal.connect(self.openSerialConnectWindow)
        portMenu.disconnectActionTriggeredSignal.connect(self.killSerialConnection)
        self.menuBar().addMenu(portMenu)
        layoutMenu = LayoutMenu(self)
        layoutMenu.layout1x1Action.triggered.connect(lambda: self.changeLayout("1x1"))
        layoutMenu.layout2x1Action.triggered.connect(lambda: self.changeLayout("2x1"))
        layoutMenu.layout1x2Action.triggered.connect(lambda: self.changeLayout("1x2"))
        layoutMenu.layout2u1Action.triggered.connect(lambda: self.changeLayout("2+1"))
        layoutMenu.layout1u2Action.triggered.connect(lambda: self.changeLayout("1+2"))
        layoutMenu.layout2x2Action.triggered.connect(lambda: self.changeLayout("2x2"))
        self.menuBar().addMenu(layoutMenu)
        colorThemesMenu = ColorThemesMenu(self)
        colorThemesMenu.darkAction.triggered.connect(lambda: self.colorSchemeHandler.setToDarkScheme())
        colorThemesMenu.defaultAction.triggered.connect(lambda: self.colorSchemeHandler.setToDefaultColor())
        #colorThemesMenu.actionTriggeredSignal.connect(self.colorSchemeHandler.setToStyleSheet)
        self.menuBar().addMenu(colorThemesMenu)
        toolsMenu = ToolsMenu(self.connectedPorts, self)
        toolsMenu.addTerminalSignal.connect(self.addTerminal)
        toolsMenu.addGraphSignal.connect(self.addGraph)
        toolsMenu.addPressureControlPanelSignal.connect(self.addPressureControlPanel)
        toolsMenu.addDruckBox2Signal.connect(self.addDruckBox2)
        toolsMenu.addMotorDriverPanelSignal.connect(self.addMotorDriverPanel)
        toolsMenu.addTablePlotterSignal.connect(self.addTablePlotter)
        toolsMenu.addVarCalculatorSignal.connect(self.addVarCalculator)
        toolsMenu.addMeasurementSignal.connect(self.addMeasurement)
        # @TODO toolsMenu.addNEWWINDOWSignal.connect(self.addNEWWINDOW)
        toolsMenu.disconnectAllAction.triggered.connect(lambda: self.killSerialConnection("ALL"))
        self.menuBar().addMenu(toolsMenu)

        self.mainWidget = QWidget()
        self.mainMiddleWidget = QWidget()
        self.mainMiddleWidgetLayout = QVBoxLayout()
        self.mainMiddleWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.mainMiddleWidget.setLayout(self.mainMiddleWidgetLayout)
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.mainMiddleWidget)
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        
        self.statusBar()

        self.initSignalsAndSlots()

        #self.mainTimer100 = QTimer()
        #self.mainTimer100.start(100)

        self.changeLayout("1x1")

        self.applySettings()

        self.setWindowTitle("Serial Port Monitor")
        self.show()

    def initSignalsAndSlots(self):
        self.madeSerialConnectionSignal.connect(self.printMadeConnection)
        self.lostSerialConnectionSignal.connect(self.printLostConnection)
        self.receiveSerialDataSignal.connect(self.printReceivedData)
        self.failedSendSerialDataSignal.connect(self.printFailedSendData)

    def openSerialConnectWindow(self, portName):
        self.serialConnectWindow = SerialConnectWindow(portName)
        self.serialConnectWindow.okButton.clicked.connect(lambda: self.connectToSerial(self.serialConnectWindow))
        self.serialConnectWindow.show()

    def connectToSerial(self, window: SerialConnectWindow):
        serialParam = window.getSerialParameter()
        window.close()

        serialThread = SerialThread(serialParam)
        serialThread.signals.madeConnection.connect(lambda obj: self.madeSerialConnectionSignal.emit(obj))
        serialThread.signals.lostConnection.connect(lambda obj: self.lostSerialConnectionSignal.emit(obj))
        serialThread.signals.receivedData.connect(lambda obj, data: self.receiveSerialDataSignal.emit(obj, data))
        serialThread.signals.failedSendData.connect(lambda obj, data: self.failedSendSerialDataSignal.emit(obj, data))

        self.sendSerialWriteSignal.connect(serialThread.writeSerial)
        self.killSerialConnectionSignal.connect(serialThread.kill)
        self.pauseSerialConnectionSignal.connect(serialThread.pause)
        self.resumeSerialConnectionSignal.connect(serialThread.resume)
        self.startSerialRecordSignal.connect(serialThread.startRecordData)
        self.stopSerialRecordSignal.connect(serialThread.stopRecordData)
        self.pauseSerialRecordSignal.connect(serialThread.pauseRecordData)
        self.resumeSerialRecordSignal.connect(serialThread.resumeRecordData)
        self.writeToFileSignal.connect(serialThread.writeDataToFile)

        QThreadPool.globalInstance().start(serialThread)

    def reconnectToSerial(self, serialParam: SerialParameters):
        serialThread = SerialThread(serialParam)
        serialThread.signals.madeConnection.connect(lambda obj: self.madeSerialConnectionSignal.emit(obj))
        serialThread.signals.lostConnection.connect(lambda obj: self.lostSerialConnectionSignal.emit(obj))
        serialThread.signals.receivedData.connect(lambda obj, data: self.receiveSerialDataSignal.emit(obj, data))
        serialThread.signals.failedSendData.connect(lambda obj, data: self.failedSendSerialDataSignal.emit(obj, data))

        self.sendSerialWriteSignal.connect(serialThread.writeSerial)
        self.killSerialConnectionSignal.connect(serialThread.kill)
        self.pauseSerialConnectionSignal.connect(serialThread.pause)
        self.resumeSerialConnectionSignal.connect(serialThread.resume)
        self.startSerialRecordSignal.connect(serialThread.startRecordData)
        self.stopSerialRecordSignal.connect(serialThread.stopRecordData)
        self.pauseSerialRecordSignal.connect(serialThread.pauseRecordData)
        self.resumeSerialRecordSignal.connect(serialThread.resumeRecordData)
        self.writeToFileSignal.connect(serialThread.writeDataToFile)

        QThreadPool.globalInstance().start(serialThread)

    def killSerialConnection(self, portName):
        self.killSerialConnectionSignal.emit(portName)

    def serialWriteData(self, portName, data):
        self.sendSerialWriteSignal.emit(portName, data)

    def startSerialRecord(self, portName, filePath, fileName):
        self.startSerialRecordSignal.emit(portName, filePath, fileName)

    def stopSerialRecord(self, portName):
        self.stopSerialRecordSignal.emit(portName)

    def pauseSerialRecord(self, portName):
        self.pauseSerialRecordSignal.emit(portName)

    def resumeSerialRecord(self, portName):
        self.resumeSerialRecordSignal.emit(portName)

    def writeToFile(self, text, portName, filePath, fileName):
        self.writeToFileSignal.emit(text, portName, filePath, fileName)

    def pauseSerialConnection(self, portName="ALL"):
        self.pauseSerialConnectionSignal.emit(portName)

    def resumeSerialConnection(self, portName="ALL"):
        self.resumeSerialConnectionSignal.emit(portName)

    def printMadeConnection(self, obj: SerialParameters):
        self.connectedPorts.append(obj)
        #print("Made connection with: " + obj.port)

    def printLostConnection(self, obj):
        for port in self.connectedPorts:
            if port.port == obj.port:
                self.connectedPorts.remove(port)
        #print("Lost connection with: " + obj.port)

    def printReceivedData(self, obj, data):
        pass #print(obj.port + " - " + data)

    def printFailedSendData(self, obj, data):
        pass #print(obj.port + " - " + data.decode('utf-8'))

    def closeEvent(self, event):
        self.killSerialConnection("ALL")
        tabList = []
        tabWidgetCount = 0
        for tabWidget in self.tabWidgets:
            for count in range(0, tabWidget.count()):
                tab = tabWidget.widget(count)
                tempTab = {"tabType": tab.tabType, "port": tab.port, "layoutPosIndex": tabWidgetCount, "uuid": tab.uuid}
                tabList.append(tempTab)
                tab.saveSettings(self.settings)
                tab.close()
            tabWidgetCount += 1
        self.saveSettings(tabList)

    def saveSettings(self, tabList):
        self.settings.setValue('tab list', tabList)
        self.settings.setValue('layout', self.layout)
        self.settings.setValue('window size', self.size())
        self.settings.setValue('window maximized', str(self.isMaximized()))
        self.settings.setValue('window position', self.pos())
        self.settings.setValue('serial connections', self.connectedPorts)

    def applySettings(self):
        try:
            self.resize(self.settings.value('window size'))
            self.move(self.settings.value('window position'))
            if self.settings.value('window maximized').lower() == "true":
                self.showMaximized()
            self.changeLayout(self.settings.value('layout'))

            if self.settings.value('serial connections'):
                for serialParameter in self.settings.value('serial connections'):
                    self.reconnectToSerial(serialParameter)
            
            tabList = self.settings.value('tab list')
            if tabList:
                for tab in tabList:
                    if tab["tabType"] == "Terminal":
                        self.addTerminal(tab["port"], tab["layoutPosIndex"], tab["uuid"])
                    elif tab["tabType"] == "Graph":
                        self.addGraph(tab["port"], tab["layoutPosIndex"], tab["uuid"])
                    elif tab["tabType"] == "PressureControlPanel":
                        self.addPressureControlPanel(tab["port"], tab["layoutPosIndex"], tab["uuid"])
                    elif tab["tabType"] == "DruckBox2":
                        self.addDruckBox2(tab["port"], tab["layoutPosIndex"], tab["uuid"])
                    elif tab["tabType"] == "MotorDriverPanel":
                        self.addMotorDriverPanel(tab["port"], tab["layoutPosIndex"], tab["uuid"])
                    elif tab["tabType"] == "TablePlotter":
                        self.addTablePlotter(tab["port"], tab["layoutPosIndex"], tab["uuid"])
                    elif tab["tabType"] == "VarCalculator":
                        self.addVarCalculator(tab["port"], tab["layoutPosIndex"], tab["uuid"])
                    elif tab["tabType"] == "Measurement":
                        self.addMeasurement(tab["port"], tab["layoutPosIndex"], tab["uuid"])
                    # @TODO  elif tab["tabType"] == "NEWWINDOW":
                    #           self.addNEWWINDOW(tab["port"], tab["layoutPosIndex"], tab["uuid"])
                for tabWidget in self.tabWidgets:
                    for count in range(0, tabWidget.count()):
                        tabWidget.widget(count).applySettings(self.settings)
            self.settings.clear()
        except:
            pass

    def changeTabNames(self):
        for tabWidget in self.tabWidgets:
            tabWidget.renameTabs()

    def changeLayout(self, layoutOption: str):
        if layoutOption == "1x1":
            self.layout = "1x1"
            LayoutHandler.createOneByOneLayout(self.mainMiddleWidget, self.tabWidgets)
        elif layoutOption == "2x1":
            self.layout = "2x1"
            LayoutHandler.createTwoByOneLayout(self.mainMiddleWidget, self.tabWidgets)
        elif layoutOption == "1x2":
            self.layout = "1x2"
            LayoutHandler.createOneByTwoLayout(self.mainMiddleWidget, self.tabWidgets)
        elif layoutOption == "2+1":
            self.layout = "2+1"
            LayoutHandler.createTwoAndOneLayout(self.mainMiddleWidget, self.tabWidgets)
        elif layoutOption == "1+2":
            self.layout = "1+2"
            LayoutHandler.createOneAndTwoLayout(self.mainMiddleWidget, self.tabWidgets)
        elif layoutOption == "2x2":
            self.layout = "2x2"
            LayoutHandler.createTwoByTwoLayout(self.mainMiddleWidget, self.tabWidgets)

    def addTerminal(self, portName, layoutPosIndex: int = 0, UUID=None):
        terminal = Terminal("Terminal: " + portName, self.connectedPorts, portName, UUID)
        self.receiveSerialDataSignal.connect(terminal.receiveData)
        terminal.sendSerialWriteSignal.connect(self.serialWriteData)
        terminal.renameTabSignal.connect(self.changeTabNames)
        LayoutHandler.addNewTab(self.tabWidgets, terminal, layoutPosIndex)

    def addGraph(self, portName, layoutPosIndex: int = 0, UUID=None):
        graph = Graph("Graph: " + portName, self.connectedPorts, portName, UUID)
        self.colorSchemeHandler.colorChangeSignal.connect(graph.changeColors)
        self.receiveSerialDataSignal.connect(graph.receiveData)
        graph.renameTabSignal.connect(self.changeTabNames)

        # NEW LINE
        graph.show()
        #LayoutHandler.addNewTab(self.tabWidgets, graph, layoutPosIndex)

    def addPressureControlPanel(self, portName, layoutPosIndex: int = 0, UUID=None):
        pressurePanel = PressureControlPanel("Pressure control panel: " + portName, self.connectedPorts, portName, UUID)
        self.receiveSerialDataSignal.connect(pressurePanel.receiveData)
        pressurePanel.sendSerialWriteSignal.connect(self.serialWriteData)
        pressurePanel.renameTabSignal.connect(self.changeTabNames)
        LayoutHandler.addNewTab(self.tabWidgets, pressurePanel, layoutPosIndex)
        
    def addDruckBox2(self, portName, layoutPosIndex: int = 0, UUID=None):
        druckBox2 = DruckBox2("DruckBox2: " + portName, self.connectedPorts, portName, UUID)
        self.receiveSerialDataSignal.connect(druckBox2.receiveData)
        druckBox2.sendSerialWriteSignal.connect(self.serialWriteData)
        druckBox2.renameTabSignal.connect(self.changeTabNames)
        LayoutHandler.addNewTab(self.tabWidgets, druckBox2, layoutPosIndex)

    def addMotorDriverPanel(self, portName, layoutPosIndex: int = 0, UUID=None):
        motorDriverPanel = MotorDriverPanel("Motor driver panel: " + portName, self.connectedPorts, portName, UUID)
        self.receiveSerialDataSignal.connect(motorDriverPanel.receiveData)
        motorDriverPanel.sendSerialWriteSignal.connect(self.serialWriteData)
        motorDriverPanel.renameTabSignal.connect(self.changeTabNames)
        LayoutHandler.addNewTab(self.tabWidgets, motorDriverPanel, layoutPosIndex)
        
    def addTablePlotter(self, portName, layoutPosIndex: int = 0, UUID=None):
        tablePlotter = TablePlotter("Table plotter: " + portName, self.connectedPorts, portName, UUID)
        self.receiveSerialDataSignal.connect(tablePlotter.receiveData)
        tablePlotter.sendSerialWriteSignal.connect(self.serialWriteData)
        tablePlotter.startRecordSignal.connect(self.startSerialRecord)
        tablePlotter.stopRecordSignal.connect(self.stopSerialRecord)
        tablePlotter.renameTabSignal.connect(self.changeTabNames)
        LayoutHandler.addNewTab(self.tabWidgets, tablePlotter, layoutPosIndex)

    def addVarCalculator(self, portName, layoutPosIndex: int = 0, UUID=None):
        varCalculator = VarCalculator("Var calculator: " + portName, self.connectedPorts, portName, UUID)
        self.receiveSerialDataSignal.connect(varCalculator.receiveData)
        varCalculator.renameTabSignal.connect(self.changeTabNames)

        # NEW LINE
        # varCalculator.show()
        LayoutHandler.addNewTab(self.tabWidgets, varCalculator, layoutPosIndex)

    def addMeasurement(self, portName, layoutPosIndex: int = 0, UUID=None):
        measurement = Measurement("Measurement: " + portName, self.connectedPorts, portName, UUID)
        self.receiveSerialDataSignal.connect(measurement.receiveData)
        measurement.sendSerialWriteSignal.connect(self.serialWriteData)
        measurement.startRecordSignal.connect(self.startSerialRecord)
        measurement.stopRecordSignal.connect(self.stopSerialRecord)
        measurement.pauseRecordSignal.connect(self.pauseSerialRecord)
        measurement.resumeRecordSignal.connect(self.resumeSerialRecord)
        measurement.writeToFileSignal.connect(self.writeToFile)
        measurement.renameTabSignal.connect(self.changeTabNames)
        LayoutHandler.addNewTab(self.tabWidgets, measurement, layoutPosIndex)

    # @TODO     def addNEWWINDOW(self, portName, layoutPosIndex: int = 0, UUID=None):
    #               newwindow = NEWWINDOW("NewWindow: " + portName, self.connectedPorts, portName, UUID)
    #               self.receiveSerialDataSignal.connect(newwindow.receiveData)
    #               newwindow.sendSerialWriteSignal.connect(self.serialWriteData)
    #               newwindow.startRecordSignal.connect(self.startSerialRecord)
    #               newwindow.stopRecordSignal.connect(self.stopSerialRecord)
    #               newwindow.pauseRecordSignal.connect(self.pauseSerialRecord)
    #               newwindow.resumeRecordSignal.connect(self.resumeSerialRecord)
    #               newwindow.writeToFileSignal.connect(self.writeToFile)
    #               newwindow.renameTabSignal.connect(self.changeTabNames)
    #               LayoutHandler.addNewTab(self.tabWidgets, measurement, layoutPosIndex)^^

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()