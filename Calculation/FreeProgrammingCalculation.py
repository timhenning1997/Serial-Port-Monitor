import os

from PyQt5.QtCore import Qt

from Calculation.CalculationChild import CalculationChild
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor, QTextCursor, QIcon
from UsefulFunctions import QHLine, resource_path

from io import StringIO
from contextlib import redirect_stdout
from Calculation.SyntaxHighlighter import *
from math import *


class FreeProgrammingCalculation(CalculationChild):
    def __init__(self, globalVarNames: [], globalVars: [], parent=None):
        super().__init__(globalVarNames, globalVars, parent)

        self.lastError = ""
        self.vars = {"x": 1,
                     "y": 2,
                     "z": 3,
                     "once": False}
        self.setup = False

        self.editorTextEdit = QTextEdit()
        self.editorTextEdit.setTabStopDistance(20)
        self.editorTextEdit.setTextColor(QColor(200, 200, 200))
        self.editorTextEdit.setPlainText("#Change result name with:\nself.resultName = 'result'\n\n# To display your result use:\nself.result = 0.12\nprint('output text') \n\n# To load channel vars:\nself.getValue('COM0 / CH0 / Nummer')\n\n# To save variables use:\nself.vars['var'] = 0.12\n\nprint(cos(pi))")
        self.highlight = PythonHighlighter(self.editorTextEdit.document())

        self.consoleTextEditor = QTextEdit()
        self.consoleTextEditor.setMinimumHeight(40)
        self.consoleTextEditor.setReadOnly(True)

        self.resultNameLabel = QLabel("result : ")
        self.resultName = ""
        self.resultLabel = QLabel("---")
        self.result = 0

        openFilePathDialogButton = QPushButton()
        openFilePathDialogButton.setIcon(QIcon(resource_path("res/Icon/folder.ico")))
        openFilePathDialogButton.clicked.connect(self.getFileText)

        resultLayout = QHBoxLayout()
        resultLayout.addWidget(self.resultNameLabel)
        resultLayout.addWidget(self.resultLabel)
        resultLayout.addStretch()
        resultLayout.addWidget(openFilePathDialogButton)

        splitterV = QSplitter(Qt.Vertical)
        splitterV.addWidget(self.editorTextEdit)
        splitterV.addWidget(self.consoleTextEditor)
        splitterV.moveSplitter(300, 1)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(splitterV)
        mainLayout.addWidget(QHLine())
        mainLayout.addLayout(resultLayout)

        self.setLayout(mainLayout)

    def getFileText(self):
        fileName = QFileDialog.getOpenFileName(None, "Open File", os.getcwd(), "txt(*.txt)\nall(*.*)", "",
                                               QFileDialog.DontUseNativeDialog)
        if fileName[0] == "":
            return None

        self.parent.forcePauseState()

        f = open(fileName[0], "r")
        self.editorTextEdit.setPlainText(f.read())

    def calculate(self):
        localDict = {}
        for varCount in range(0, len(self.globalVars)):
            localDict[self.globalVarNames[varCount]] = self.globalVars[varCount]
            
        text = self.editorTextEdit.toPlainText()
        self.resultName = ""
        localDict.update(globals())
        localDict.update(locals())
        try:
            with redirect_stdout(StringIO()) as f:
                exec(text, localDict)
            s = str(f.getvalue()).replace("<", "&lt;").replace(">", "&gt;")
            self.resultLabel.setText(str(self.result))
            if self.result != 0:
                self.resultLabel.setText(str(self.result).strip())
            if str(self.resultName) != "":
                self.resultNameLabel.setText(str(self.resultName).strip() + " : ")
            if str(s) != "":
                self.consoleTextEditor.moveCursor(QTextCursor.End)
                for line in s.splitlines():
                    self.consoleTextEditor.insertHtml(f"<span style=\"color:#ffff00;\"><br>" + line + f"</span>")
                self.consoleTextEditor.moveCursor(QTextCursor.End)
            if self.lastError != "":
                self.lastError = ""
                self.consoleTextEditor.clear()

        except Exception as inst:
            currentError = str(str(type(inst)) + str(inst)).replace("<", "&lt;").replace(">", "&gt;").strip()
            if self.lastError != currentError:
                self.lastError = currentError
                self.consoleTextEditor.moveCursor(QTextCursor.End)
                self.consoleTextEditor.insertHtml(f"<span style=\"color:#ff0000;\"><br>{currentError}</span>")
                self.consoleTextEditor.moveCursor(QTextCursor.End)

        if self.setup:
            self.setup = False

    def changePausedState(self, state: str):
        if state == "play":
            self.setup = True
        elif state == "pause":
            pass
        elif state == "close":
            pass

    def save(self):
        return {"text": self.editorTextEdit.toPlainText()}

    def load(self, option):
        self.editorTextEdit.setPlainText(option["text"])
