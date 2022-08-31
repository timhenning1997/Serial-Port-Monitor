from PyQt5.QtWidgets import *
from UsefulFunctions import QHLine

class ValueCombobox(QComboBox):
    def __init__(self, parent: QWidget):
        super().__init__()
        self.parent = parent
        self.parent.populateCombobox(self)

    def showPopup(self):
        self.parent.populateCombobox(self)
        super().showPopup()

    #def handleActivated(self, index):
    #    self.lastText = self.itemText(index)


class ChannelValueLayout(QHBoxLayout):
    def __init__(self, parent: QWidget, name: str, unit: str = ""):
        super().__init__()

        self.parent = parent

        self.channelCombobox = ValueCombobox(self.parent)
        self.channelCombobox.setFixedWidth(20)
        name = QLabel(name)
        name.setFixedWidth(100)
        self.channelValue = QLabel("0")

        unitName = QLabel(unit)
        unitName.adjustSize()
        if unitName.width() < 30:
            unitName.setFixedWidth(30)

        self.addWidget(self.channelCombobox)
        self.addWidget(name)
        self.addWidget(self.channelValue)
        self.addWidget(unitName)

    def getValue(self):
        if self.channelCombobox.currentText() in self.parent.globalVarNames:
            return self.parent.globalVars[self.parent.globalVarNames.index(self.channelCombobox.currentText())]
        return 0

    def setText(self, text: str):
        self.channelValue.setText(text)

    def setChannel(self, text: str):
        if self.channelCombobox.findText(text) < 0:
            self.channelCombobox.addItem(text)
        self.channelCombobox.setCurrentText(text)

    def getChannel(self):
        return self.channelCombobox.currentText()


class InputFloatValueLayout(QHBoxLayout):
    def __init__(self, name: str, value: float = 0, decimals: int = 2, unit: str = ""):
        super().__init__()

        tempLabel = QLabel("")
        tempLabel.setFixedWidth(20)
        name = QLabel(name)
        name.setFixedWidth(100)

        self.inputValue = QDoubleSpinBox()
        self.inputValue.setDecimals(decimals)
        self.inputValue.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.inputValue.setRange(-10e50, 10e50)
        self.inputValue.setValue(value)

        unitName = QLabel(unit)
        unitName.adjustSize()
        if unitName.width() < 30:
            unitName.setFixedWidth(30)

        self.addWidget(tempLabel)
        self.addWidget(name)
        self.addWidget(self.inputValue)
        self.addWidget(unitName)

    def getValue(self):
        return self.inputValue.value()


class InputIntValueLayout(QHBoxLayout):
    def __init__(self, name: str, value: int = 0, unit: str = ""):
        super().__init__()

        tempLabel = QLabel("")
        tempLabel.setFixedWidth(20)
        name = QLabel(name)
        name.setFixedWidth(100)

        self.inputValue = QSpinBox()
        self.inputValue.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.inputValue.setRange(-10e8, 10e8)
        self.inputValue.setValue(value)

        unitName = QLabel(unit)
        unitName.adjustSize()
        if unitName.width() < 30:
            unitName.setFixedWidth(30)

        self.addWidget(tempLabel)
        self.addWidget(name)
        self.addWidget(self.inputValue)
        self.addWidget(unitName)

    def getValue(self):
        return self.inputValue.value()


class ResultLayout(QVBoxLayout):
    def __init__(self, name: str, unit: str = ""):
        super().__init__()

        tempLabel = QLabel("")
        tempLabel.setFixedWidth(20)
        name = QLabel(name)
        name.setFixedWidth(100)
        self.result = QLabel("---")

        unitName = QLabel(unit)
        unitName.adjustSize()
        if unitName.width() < 30:
            unitName.setFixedWidth(30)

        tempVBoxLayout = QHBoxLayout()
        tempVBoxLayout.addWidget(tempLabel)
        tempVBoxLayout.addWidget(name)
        tempVBoxLayout.addWidget(self.result)
        tempVBoxLayout.addStretch()
        tempVBoxLayout.addWidget(unitName)

        self.addWidget(QHLine())
        self.addLayout(tempVBoxLayout)

    def setValue(self, text: str):
        self.result.setText(text)


class CalculationChild(QWidget):
    def __init__(self, globalVarNames: [], globalVars: [], parent=None):
        super().__init__(parent)
        
        self.parent = parent

        self.globalVarNames = globalVarNames
        self.globalVars = globalVars

    def getValue(self, name: str):
        if name in self.globalVarNames:
            return self.globalVars[self.globalVarNames.index(name)]
        return 0

    def populateCombobox(self, comboBox: QComboBox):
        comboBox.clear()
        for name in self.globalVarNames:
            comboBox.addItem(name)

    def calculate(self):
        print("No calculation found for that calculation child!")

    def changePausedState(self, state: str):
        pass

    def save(self):
        return None

    def load(self, option):
        pass
