from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class TabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAcceptDrops(True)
        self.tabBar = self.tabBar()
        self.tabBar.setMouseTracking(True)
        self.indexTab = None
        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabBar.setProperty("Source", "TabBarWidget")

        self.tabCloseRequested.connect(self.closeTab)

    def mouseMoveEvent(self, e):
        if e.buttons() != Qt.MouseButton.RightButton:
            return

        globalPos = self.mapToGlobal(e.pos())
        tabBar = self.tabBar
        posInTab = tabBar.mapFromGlobal(globalPos)
        self.indexTab = tabBar.tabAt(e.pos())
        tabRect = tabBar.tabRect(self.indexTab)

        pixmap = QPixmap(tabRect.size())
        tabBar.render(pixmap, QPoint(), QRegion(tabRect))
        mimeData = QMimeData()
        drag = QDrag(tabBar)
        drag.setMimeData(mimeData)
        drag.setPixmap(pixmap)
        cursor = QCursor(Qt.CursorShape.OpenHandCursor)
        drag.setHotSpot(e.pos() - posInTab)
        drag.setDragCursor(cursor.pixmap(), Qt.DropAction.MoveAction)
        dropAction = drag.exec_(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, e):
        e.accept()
        if e.source().parentWidget() != self:
            return
        self.parent.TABINDEX = self.indexOf(self.widget(self.indexTab))

    def dragLeaveEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        if e.source().property("Source") != "TabBarWidget":
            return
        #if e.source().parentWidget() == self:
        #    return

        e.setDropAction(Qt.DropAction.MoveAction)
        e.accept()
        counter = self.count()
        globalPos = self.mapToGlobal(e.pos())
        tabBar = self.tabBar
        posInTab = tabBar.mapFromGlobal(globalPos)

        if counter == 0:
            self.addTab(e.source().parentWidget().widget(self.parent.TABINDEX), e.source().tabText(self.parent.TABINDEX))
        else:
            mousePosIndex = 0
            for count in range(0, counter):
                if posInTab.x() > tabBar.tabRect(count).left() + 1 + qRound(tabBar.tabRect(count).width() / 2):
                    mousePosIndex = count + 1
            if e.source().parentWidget() == self and e.source().parentWidget().indexTab < mousePosIndex:
                mousePosIndex -= 1
            self.insertTab(mousePosIndex, e.source().parentWidget().widget(self.parent.TABINDEX), e.source().tabText(self.parent.TABINDEX))

    def closeTab(self, currentIndex):
        currentQWidget = self.widget(currentIndex)
        currentQWidget.close()
        currentQWidget.deleteLater()
        self.removeTab(currentIndex)

    def closeCurrentTab(self):
        currentQWidget = self.widget(self.currentIndex())
        currentQWidget.deleteLater()
        self.removeTab(self.currentIndex())

    def renameTabs(self):
        for count in range(0, self.count()):
            self.setTabText(count, self.widget(count).name)
