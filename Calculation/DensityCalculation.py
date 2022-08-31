from Calculation.CalculationChild import *
from PyQt5.QtWidgets import *



class DensityCalculation(CalculationChild):
    def __init__(self, globalVarNames: [], globalVars: [], parent=None):
        super().__init__(globalVarNames, globalVars, parent)

        self.T = ChannelValueLayout(self, "Temprature", u"°C")
        self.p = ChannelValueLayout(self, "Pressure", "Pa")
        self.result = ResultLayout("Dichte", "kg/(m^3)")

        mainLayout = QVBoxLayout()

        mainLayout.addLayout(self.T)
        mainLayout.addLayout(self.p)
        mainLayout.addLayout(self.result)
        mainLayout.addStretch()

        self.setLayout(mainLayout)

    def save(self):
        option = {
            "T": self.T.getChannel(),
            "p": self.p.getValue()
        }
        return option

    def load(self, option):
        self.T.setChannel(option["T"])
        self.p.setChannel(option["p"])

    def calculate(self):
        self.T.setText("%.2f" % self.T.getValue())
        self.p.setText("%.2f" % self.p.getValue())

        result = self.calculateDichte(self.T.getValue(), self.p.getValue())

        self.result.setValue("%.2f" % result)

    def calculateDichte(self, T: (float, int) = 20, p: (float, int) = 1.0125e+5):
        R = 287.058
        rho = p / (R * T)
        return rho