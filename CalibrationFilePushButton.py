from PyQt5.QtCore import QMimeData, Qt, QEvent
from PyQt5.QtGui import QDrag, QMouseEvent, QDragLeaveEvent
from PyQt5.QtWidgets import QPushButton, QApplication


class CalibrationFilePushButton(QPushButton):

    def __init__(self, text: str, parent):
        super().__init__(text, parent)

        self.parent = parent

        self.setAcceptDrops(True)
        self.setProperty("Source", "CalibrationFile")

    #def mouseMoveEvent(self, event: QMouseEvent):
    #    pass

    def leaveEvent(self, e: QEvent):
        data = self.parent.dragLabelActivated()
        port = data["port"]
        path = data["path"]

        drag = QDrag(self)
        mime = QMimeData()
        mime.setProperty("port", port)
        mime.setProperty("path", path)
        drag.setMimeData(mime)
        drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, e):
        e.accept()

    def dragLeaveEvent(self, e: QDragLeaveEvent):
        self.clearFocus()

    def dropEvent(self, e: QDrag):
        if e.source().property("Source") != "CalibrationFile":
            return
        port = e.mimeData().property("port")
        path = e.mimeData().property("path")
        self.parent.dropLabelActivated({"port": port, "path": path})

        if self.hasFocus():
            self.clearFocus()
