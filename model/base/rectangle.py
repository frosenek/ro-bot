from PySide2 import QtCore

from .base import BaseObject
from .point import Point


class Rectangle(BaseObject):

    def __init__(self, *args):
        super(Rectangle, self).__init__()

        if len(args) == 1:
            rect = args[0]
            if isinstance(rect, QtCore.QRect):
                self._from_qrect(rect)
        elif len(args) == 2:
            p1, p2 = args
            if isinstance(p1, Point) and isinstance(p2, Point):
                self._from_points(p1, p2)
        elif len(args) == 4:
            self._from_tuple(*args)
        else:
            raise NotImplementedError

    def _from_qrect(self, rect: QtCore.QRect):
        self.x = rect.x()
        self.y = rect.y()
        self.w = rect.width()
        self.h = rect.height()

    def _from_points(self, p1: Point, p2: Point):
        self.x = p1.x
        self.y = p1.y
        self.w = p2.x - p1.x
        self.h = p2.y - p1.y

    def _from_tuple(self, x: int, y: int, w: int, h: int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.w
        yield self.h

    def center(self):
        return Point(self.x + self.w / 2, self.y + self.h / 2)

    def __contains__(self, item):
        if isinstance(item, Point):
            return self.contains(item)
        raise NotImplementedError

    def contains(self, p: Point, padding=0):
        return self.x + padding < p.x < self.x + self.w - padding and \
               self.y + padding < p.y < self.y + self.h - padding

    @property
    def x0(self):
        return self.x

    @property
    def y0(self):
        return self.y

    @property
    def x1(self):
        return self.x + self.w

    @property
    def y1(self):
        return self.y + self.h
