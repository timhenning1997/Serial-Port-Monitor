from math import pi

from Calculation.CalculationChild import *
from PyQt5.QtWidgets import *
#import numpy as np
#from CoolProp.CoolProp import PropsSI



class MassFlowCalculation(CalculationChild):
    def __init__(self, globalVarNames: [], globalVars: [], parent=None):
        super().__init__(globalVarNames, globalVars, parent)

        self.vordruck = ChannelValueLayout(self, "Vordruck", "Pa")
        self.wirkdruck = ChannelValueLayout(self, "Wirkdruck", "Pa")
        self.temperatur = ChannelValueLayout(self, "Temperatur", u"°C")
        self.D_blende = InputFloatValueLayout("D-Blende", 0.05585, 4, "m")
        self.d_blende = InputFloatValueLayout("d-Blende", 0.037265, 4, "m")
        self.genauigkeit = InputIntValueLayout("Genauigkeit", 6, "10e-n")
        self.result = ResultLayout("Massenstrom", "kg/s")

        mainLayout = QVBoxLayout()

        mainLayout.addLayout(self.vordruck)
        mainLayout.addLayout(self.wirkdruck)
        mainLayout.addLayout(self.temperatur)
        mainLayout.addLayout(self.D_blende)
        mainLayout.addLayout(self.d_blende)
        mainLayout.addLayout(self.genauigkeit)
        mainLayout.addLayout(self.result)
        mainLayout.addStretch()

        self.setLayout(mainLayout)


    def calculate(self):
        self.vordruck.setText("%.2f" % self.vordruck.getValue())
        self.wirkdruck.setText("%.2f" % self.wirkdruck.getValue())
        self.temperatur.setText("%.2f" % self.temperatur.getValue())

        result = self.calculateMassenstrom(self.d_blende.getValue(),
                                           self.D_blende.getValue(),
                                           self.temperatur.getValue(),
                                           self.vordruck.getValue(),
                                           self.wirkdruck.getValue())

        self.result.setValue("%.2f" % result)

    def save(self):
        option = {
            "vordruck": self.vordruck.getChannel(),
            "wirkdruck": self.wirkdruck.getChannel(),
            "temperatur": self.temperatur.getChannel(),
            "D_blende": self.D_blende.getValue(),
            "d_blende": self.d_blende.getValue(),
            "genauigkeit": self.genauigkeit.getValue()
        }
        return option

    def load(self, option):
        self.vordruck.setChannel(option["vordruck"])
        self.wirkdruck.setChannel(option["wirkdruck"])
        self.temperatur.setChannel(option["temperatur"])
        self.D_blende.inputValue.setValue(float(option["D_blende"]))
        self.d_blende.inputValue.setValue(float(option["d_blende"]))
        self.genauigkeit.inputValue.setValue(int(option["genauigkeit"]))

    def calculateMassenstrom(self, d_bl: (float, int) = 0.037265, d_pipe: (float, int) = 0.05585, temp: (float, int) = 300, pvor: (float, int) = 1.0125e+5, pwirk: (float, int) = 0.1 * 10 ** 5):
        R = 287.058
        mu = 18.232e-6

        C = 0.6
        kappa = 1.4

        masse = 42

        rho = pvor / (R * temp)

        beta = d_bl / d_pipe
        calt = C
        m = 0
        alt = 0
        A_ori = pi / 4 * d_bl ** 2
        A_pipe = pi / 4 * d_pipe ** 2
        e_wert = 1 / (1 - beta ** 4) ** 0.5
        epsilon = 1 - (0.351 + 0.256 * beta ** 4 + 0.98 * beta ** 8) * (
                    1 - ((pvor - pwirk) / pvor) ** (1 / kappa))
        c = C
        for n in range(0, 100):
            m_it = c * epsilon * e_wert * A_ori * (2 * rho * pwirk) ** 0.5
            u = m_it / (rho * A_pipe)
            Re = u * d_pipe * rho / mu
            A = (19000 * beta / Re) ** 0.8
            c_a = 0.5961
            c_b = 0.0261 * beta ** 2
            c_c = -0.216 * beta ** 8
            c_d = .000521 * (1e+6 * beta / Re) ** .7
            c_e = (.0188 + .0063 * A) * beta ** 3.5 * (1e+6 / Re) ** .3
            c_g = .011 * (.75 - beta) * (2.8 - d_pipe / 25.4e-3)
            c = c_a + c_b + c_c + c_d + c_e + c_g
            masse = m_it * c / calt
            calt = c
            if abs(masse - alt) < 1e-10:
                break
            alt = masse
        return masse
