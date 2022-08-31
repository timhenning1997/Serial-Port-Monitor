from Calculation.CalculationChild import *
from PyQt5.QtWidgets import *



class WallShearStressCalculation(CalculationChild):
    def __init__(self, globalVarNames: [], globalVars: [], parent=None):
        super().__init__(globalVarNames, globalVars, parent)

        self.dp = ChannelValueLayout(self, "Druckdifferenz", "Pa")
        self.h = InputFloatValueLayout("Kanalhoehe", 0, 4, "m")
        self.dl = InputFloatValueLayout("Messabstand", 0, 4, "m")
        self.result = ResultLayout("Wandschub", "kg/(m*s^2)")

        mainLayout = QVBoxLayout()

        mainLayout.addLayout(self.dp)
        mainLayout.addLayout(self.h)
        mainLayout.addLayout(self.dl)
        mainLayout.addLayout(self.result)
        mainLayout.addStretch()

        self.setLayout(mainLayout)

    def save(self):
        option = {
            "dp": self.dp.getChannel(),
            "h": self.h.getValue(),
            "dl": self.dl.getValue()
        }
        return option

    def load(self, option):
        self.dp.setChannel(option["dp"])
        self.h.inputValue.setValue(float(option["h"]))
        self.dl.inputValue.setValue(float(option["dl"]))

    def calculate(self):
        self.dp.setText("%.2f" % self.dp.getValue())

        result = self.calculateWandschub(self.dp.getValue(),
                                           self.h.getValue(),
                                           self.dl.getValue())

        self.result.setValue("%.2f" % result)

    def calculateWandschub(self, dp: (float, int) = 1.0125e+5, h: (float, int) = 0, dl: (float, int) = 0):
        tau = h / 2 * dp / dl
        return tau