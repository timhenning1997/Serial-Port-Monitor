from PyQt5.QtCore import QMimeData, Qt
from PyQt5.QtGui import QDrag, QMouseEvent
from PyQt5.QtWidgets import QLabel


class CalibrationFileLabel(QLabel):

    def __init__(self, text: str, parent):
        super().__init__(text, parent)

        self.parent = parent

        self.setAcceptDrops(True)
        self.setProperty("Source", "CalibrationFile")

    def mousePressEvent(self, event: QMouseEvent):
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

    def dropEvent(self, e: QDrag):
        if e.source().property("Source") != "CalibrationFile":
            return
        port = e.mimeData().property("port")
        path = e.mimeData().property("path")
        self.parent.dropLabelActivated({"port": port, "path": path})
