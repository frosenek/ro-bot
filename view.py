from PySide2 import QtWidgets, QtGui, QtCore

from model.world import Map, Cell


class MapView(QtWidgets.QWidget):
    black = QtGui.QColor(0, 0, 0)
    blue = QtGui.QColor(0, 128, 255)
    navy = QtGui.QColor(0, 0, 128)
    orange = QtGui.QColor(255, 128, 0)
    white = QtGui.QColor(255, 255, 255)
    red = QtGui.QColor(255, 0, 0)
    green = QtGui.QColor(0, 255, 0)
    yellow = QtGui.QColor(236, 252, 58)
    pink = QtGui.QColor(254, 127, 156)
    brown = QtGui.QColor(139, 69, 19)

    scale = 2

    def __init__(self, *args):
        super(MapView, self).__init__(*args)

        self.map = None
        self.base = None
        self.zones = None
        self.path = None
        self.entity = None

        self.show()

    def sizeHint(self):
        if self.map is None:
            return QtCore.QSize(-1, -1)
        return QtCore.QSize(self.map.width * self.scale, self.map.height * self.scale)

    def slot_map(self, map: Map):
        if self.map is not None:
            if self.map.name == map.name:
                return

        self.map = map
        self.base = QtGui.QImage(self.map.width, self.map.height, QtGui.QImage.Format_RGB32)
        self.path = None
        self.entity = None

        painter = QtGui.QPainter()
        painter.begin(self.base)

        for cell in self.map.cells:
            if cell.walkable:
                painter.setPen(self.white)
            elif cell.snipable:
                painter.setPen(self.yellow)
            else:
                painter.setPen(self.black)

            if cell.water:
                painter.setPen(self.blue)
            if cell.cliff:
                painter.setPen(self.brown)

            painter.drawPoint(self.cell_to_qpoint(cell))

        painter.end()
        self.repaint()

    def slot_zones(self, zones):
        if not zones:
            return

        self.zones = QtGui.QImage(self.map.width, self.map.height, QtGui.QImage.Format_ARGB32_Premultiplied)
        self.zones.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter()
        painter.begin(self.zones)

        painter.setPen(self.green)
        for i, zone in enumerate(zones):
            x, y, w, h = zone.x, self.map.height - zone.y, zone.w, -zone.h
            xt, yt = zone.center()
            yt = self.map.height - yt
            painter.drawRect(x, y, w, h)
            painter.drawText(xt, yt, str(i+1))

        painter.end()

    def slot_path(self, path):
        path = path.data
        start, target = path[0], path[-1]

        self.path = QtGui.QImage(self.map.width, self.map.height, QtGui.QImage.Format_ARGB32_Premultiplied)
        self.path.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter()
        painter.begin(self.path)

        painter.setPen(self.green)
        for point in path:
            painter.drawPoint(self.cell_to_qpoint(point))

        painter.setPen(self.red)
        painter.drawPoint(self.cell_to_qpoint(start))
        painter.drawPoint(self.cell_to_qpoint(target))
        painter.drawEllipse(self.cell_to_qpoint(start), 2, 2)
        painter.drawEllipse(self.cell_to_qpoint(target), 2, 2)

        painter.end()

    def update(self):
        if self.map is None:
            return

        self.entity = QtGui.QImage(self.map.width, self.map.height, QtGui.QImage.Format_ARGB32_Premultiplied)
        self.entity.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter()
        painter.begin(self.entity)

        if self.map.char is not None:
            painter.setPen(self.green)
            cell = self.map.cell(self.map.char)
            painter.drawEllipse(self.cell_to_qpoint(cell), 2, 2)

        if len(self.map.mobs) > 0:
            painter.setPen(self.red)
            for mob in self.map.mobs:
                cell = self.map.cell(mob)
                painter.drawEllipse(self.cell_to_qpoint(cell), 2, 2)

        if len(self.map.npcs) > 0:
            painter.setPen(self.navy)
            for npc in self.map.npcs:
                cell = self.map.cell(npc)
                painter.drawEllipse(self.cell_to_qpoint(cell), 2, 2)

        if len(self.map.players) > 0:
            painter.setPen(self.orange)
            for player in self.map.players:
                cell = self.map.cell(player)
                painter.drawEllipse(self.cell_to_qpoint(cell), 2, 2)

        painter.end()
        self.repaint()

    def paintEvent(self, event: QtGui.QPaintEvent):
        if self.map is None:
            return

        image = QtGui.QImage(self.map.width, self.map.height, QtGui.QImage.Format_RGB32)
        painter = QtGui.QPainter()
        painter.begin(image)
        painter.drawImage(0, 0, self.base)
        painter.drawImage(0, 0, self.zones)
        painter.drawImage(0, 0, self.path)
        painter.drawImage(0, 0, self.entity)
        painter.end()
        image = image.scaled(
            self.map.width * self.scale,
            self.map.height * self.scale,
            QtCore.Qt.KeepAspectRatio
        )

        self.setFixedSize(image.width(), image.height())

        painter.begin(self)
        painter.drawImage(0, 0, image)
        painter.end()

    def cell_to_qpoint(self, c: Cell):
        return QtCore.QPoint(c.x, self.map.height - c.y)
