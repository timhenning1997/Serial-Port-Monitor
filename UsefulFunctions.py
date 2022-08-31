import os
import sys
from PyQt5.QtWidgets import QFrame, QSizePolicy


def isFloat(s: str):
    try:
        float(s)
    except ValueError:
        return False
    return True


def isInt(s: str):
    try:
        int(s)
    except ValueError:
        return False
    return True


def returnFloat(s: str):
    try:
        float(s)
    except ValueError:
        return -1
    return float(s)


def returnInt(s: str):
    try:
        int(s)
    except ValueError:
        return -1
    return int(s)


def convertPressureUnits(value: float, fromUnit: str = "Pa", toUnit: str = "Pa"):
    conversionFactor = 1
    if fromUnit == "Pa":
        conversionFactor *= 1
    elif fromUnit == "kPa":
        conversionFactor *= 1000
    elif fromUnit == "MPa":
        conversionFactor *= 1000000
    elif fromUnit == "bar":
        conversionFactor *= 100000

    if toUnit == "Pa":
        conversionFactor /= 1
    elif toUnit == "kPa":
        conversionFactor /= 1000
    elif toUnit == "MPa":
        conversionFactor /= 1000000
    elif toUnit == "bar":
        conversionFactor /= 100000

    return value * conversionFactor


def convertTimeUnits(value: float, fromUnit: str = "s", toUnit: str = "s"):
    conversionFactor = 1
    if fromUnit == "s":
        conversionFactor *= 1
    elif fromUnit == "min":
        conversionFactor *= 60
    elif fromUnit == "h":
        conversionFactor *= 3600
    elif fromUnit == "ms":
        conversionFactor /= 1000

    if toUnit == "s":
        conversionFactor /= 1
    elif toUnit == "min":
        conversionFactor /= 60
    elif toUnit == "h":
        conversionFactor /= 3600
    elif toUnit == "ms":
        conversionFactor *= 1000

    return value * conversionFactor


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class QHLine(QFrame):
  def __init__(self):
    super().__init__()
    self.setMinimumWidth(1)
    self.setFixedHeight(20)
    self.setFrameShape(QFrame.HLine)
    self.setFrameShadow(QFrame.Sunken)
    self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
    return
