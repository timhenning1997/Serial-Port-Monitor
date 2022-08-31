from random import random

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from TabWidget import TabWidget
from Tab import Tab


def createOneByOneLayout(widget: QWidget, widgetList: list):
    hiddenTabWidget = QTabWidget()
    if widgetList is None:
        widgetList = []
    newWidgetList = []

    deleteOldTabWidgets(hiddenTabWidget, widgetList)
    createNewTabWidgets(widget, newWidgetList, 1)
    distributeTabs(hiddenTabWidget, newWidgetList)

    splitter1H = QSplitter(Qt.Horizontal)
    splitter1H.setHandleWidth(0)
    splitter1H.addWidget(newWidgetList[0])

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(splitter1H)

    clearLayout(widget.layout())
    widget.layout().addLayout(layout)

    widgetList.clear()
    for w in newWidgetList:
        widgetList.append(w)


def createTwoByOneLayout(widget: QWidget, widgetList: list):
    hiddenTabWidget = QTabWidget()
    if widgetList is None:
        widgetList = []
    newWidgetList = []

    deleteOldTabWidgets(hiddenTabWidget, widgetList)
    createNewTabWidgets(widget, newWidgetList, 2)
    distributeTabs(hiddenTabWidget, newWidgetList)

    splitter1H = QSplitter(Qt.Horizontal)
    splitter1H.setHandleWidth(0)
    splitter1H.addWidget(newWidgetList[0])
    splitter1H.addWidget(newWidgetList[1])

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(splitter1H)

    clearLayout(widget.layout())
    widget.layout().addLayout(layout)

    widgetList.clear()
    for w in newWidgetList:
        widgetList.append(w)


def createOneByTwoLayout(widget: QWidget, widgetList: list):
    hiddenTabWidget = QTabWidget()
    if widgetList is None:
        widgetList = []
    newWidgetList = []

    deleteOldTabWidgets(hiddenTabWidget, widgetList)
    createNewTabWidgets(widget, newWidgetList, 2)
    distributeTabs(hiddenTabWidget, newWidgetList)

    splitter1V = QSplitter(Qt.Vertical)
    splitter1V.setHandleWidth(0)
    splitter1V.addWidget(newWidgetList[0])
    splitter1V.addWidget(newWidgetList[1])

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(splitter1V)

    clearLayout(widget.layout())
    widget.layout().addLayout(layout)

    widgetList.clear()
    for w in newWidgetList:
        widgetList.append(w)


def createTwoAndOneLayout(widget: QWidget, widgetList: list):
    hiddenTabWidget = QTabWidget()
    if widgetList is None:
        widgetList = []
    newWidgetList = []

    deleteOldTabWidgets(hiddenTabWidget, widgetList)
    createNewTabWidgets(widget, newWidgetList, 3)
    distributeTabs(hiddenTabWidget, newWidgetList)

    splitter1H = QSplitter(Qt.Horizontal)
    splitter1H.setHandleWidth(0)
    splitter1H.addWidget(newWidgetList[0])
    splitter1H.addWidget(newWidgetList[1])

    splitter1V = QSplitter(Qt.Vertical)
    splitter1V.setHandleWidth(0)
    splitter1V.addWidget(splitter1H)
    splitter1V.addWidget(newWidgetList[2])

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(splitter1V)

    clearLayout(widget.layout())
    widget.layout().addLayout(layout)

    widgetList.clear()
    for w in newWidgetList:
        widgetList.append(w)


def createOneAndTwoLayout(widget: QWidget, widgetList: list):
    hiddenTabWidget = QTabWidget()
    if widgetList is None:
        widgetList = []
    newWidgetList = []

    deleteOldTabWidgets(hiddenTabWidget, widgetList)
    createNewTabWidgets(widget, newWidgetList, 3)
    distributeTabs(hiddenTabWidget, newWidgetList)

    splitter1H = QSplitter(Qt.Horizontal)
    splitter1H.setHandleWidth(0)
    splitter1H.addWidget(newWidgetList[1])
    splitter1H.addWidget(newWidgetList[2])

    splitter1V = QSplitter(Qt.Vertical)
    splitter1V.setHandleWidth(0)
    splitter1V.addWidget(newWidgetList[0])
    splitter1V.addWidget(splitter1H)

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(splitter1V)

    clearLayout(widget.layout())
    widget.layout().addLayout(layout)

    widgetList.clear()
    for w in newWidgetList:
        widgetList.append(w)


def createTwoByTwoLayout(widget: QWidget, widgetList: list):
    hiddenTabWidget = QTabWidget()
    if widgetList is None:
        widgetList = []
    newWidgetList = []

    deleteOldTabWidgets(hiddenTabWidget, widgetList)
    createNewTabWidgets(widget, newWidgetList, 4)
    distributeTabs(hiddenTabWidget, newWidgetList)

    splitter1H = QSplitter(Qt.Horizontal)
    splitter1H.setHandleWidth(0)
    splitter1H.addWidget(newWidgetList[0])
    splitter1H.addWidget(newWidgetList[1])

    splitter2H = QSplitter(Qt.Horizontal)
    splitter2H.setHandleWidth(0)
    splitter2H.addWidget(newWidgetList[2])
    splitter2H.addWidget(newWidgetList[3])

    splitter1V = QSplitter(Qt.Vertical)
    splitter1V.setHandleWidth(0)
    splitter1V.addWidget(splitter1H)
    splitter1V.addWidget(splitter2H)

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(splitter1V)

    clearLayout(widget.layout())
    widget.layout().addLayout(layout)

    widgetList.clear()
    for w in newWidgetList:
        widgetList.append(w)


def addNewTab(widgetList: list, widget: Tab, layoutPosIndex: int = 0):
    if len(widgetList) > 0:
        if len(widgetList) < layoutPosIndex:
            layoutPosIndex = 0
        widgetList[layoutPosIndex].addTab(widget, widget.name)
        widgetList[layoutPosIndex].setCurrentIndex(widgetList[0].count()-1)


def deleteOldTabWidgets(hiddenTabWidget: QTabWidget, widgetList: list):
    for tabWidget in widgetList:
        while tabWidget.widget(0):
            hiddenTabWidget.addTab(tabWidget.widget(0), tabWidget.tabText(0))

    for tabWidget in widgetList:
        tabWidget.deleteLater()


def createNewTabWidgets(widget: QWidget, newWidgetList: list, count: int):
    for i in range(0, count):
        tabWidget = TabWidget(widget)
        newWidgetList.append(tabWidget)


def distributeTabs(hiddenTabWidget: QTabWidget, widgetList: list):
    tabWidgetIndex = 0
    maxtabWidgetIndex = len(widgetList)

    for tabIndex in range(0, hiddenTabWidget.count()):
        if tabWidgetIndex >= maxtabWidgetIndex:
            tabWidgetIndex = 0
        widgetList[tabWidgetIndex].addTab(hiddenTabWidget.widget(0), hiddenTabWidget.tabText(0))
        tabWidgetIndex += 1


def clearLayout(layout):
    if layout is not None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                clearLayout(child.layout())
