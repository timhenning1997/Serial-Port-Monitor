from math import pi, sqrt

from Calculation.CalculationChild import *
from PyQt5.QtWidgets import *



class VelocityCalculation(CalculationChild):
    def __init__(self, globalVarNames: [], globalVars: [], parent=None):
        super().__init__(globalVarNames, globalVars, parent)

        self.temperatur = ChannelValueLayout(self, "Temperatur", u"°C")
        self.statDruck = ChannelValueLayout(self, "stat. Druck", "Pa")
        self.centerDruck = ChannelValueLayout(self, "center Druck", "Pa")
        self.gaskonstante = InputFloatValueLayout("R_spez", 287.058, 2, "J/(kg*K)")
        self.result = ResultLayout("Geschwindigkeit", "m/s")

        mainLayout = QVBoxLayout()

        mainLayout.addLayout(self.temperatur)
        mainLayout.addLayout(self.statDruck)
        mainLayout.addLayout(self.centerDruck)
        mainLayout.addLayout(self.gaskonstante)
        mainLayout.addLayout(self.result)
        mainLayout.addStretch()

        self.setLayout(mainLayout)


    def calculate(self):
        self.temperatur.setText("%.2f" % self.temperatur.getValue())
        self.statDruck.setText("%.2f" % self.statDruck.getValue())
        self.centerDruck.setText("%.2f" % self.centerDruck.getValue())

        result = self.calculateVelocity(self.temperatur.getValue(),
                                        self.statDruck.getValue(),
                                        self.centerDruck.getValue(),
                                        self.gaskonstante.getValue())

        self.result.setValue("%.2f" % result)

    def save(self):
        option = {
            "temperatur": self.temperatur.getChannel(),
            "statDruck": self.statDruck.getChannel(),
            "centerDruck": self.centerDruck.getChannel(),
            "gaskonstante": self.gaskonstante.getValue()
        }
        return option

    def load(self, option):
        self.temperatur.setChannel(option["temperatur"])
        self.statDruck.setChannel(option["statDruck"])
        self.centerDruck.setChannel(option["centerDruck"])
        self.gaskonstante.inputValue.setValue(float(option["gaskonstante"]))

    def calculateVelocity(self, temperatur: (float, int), statDruck: (float, int), centerDruck: (float, int), gaskonstante: (float, int) = 287.058):
        rho = statDruck / (gaskonstante * temperatur)
        velocity = sqrt((2 * (centerDruck - statDruck)) / rho)
        
        return velocity
