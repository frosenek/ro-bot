import math

from .base import BaseObject


class Point(BaseObject):

    def __init__(self, x, y):
        super(Point, self).__init__()

        self.x = x
        self.y = y

    def __eq__(self, other: 'Point'):
        return self.x == other.x and \
               self.y == other.y

    # sometimes called by heappush if self.f equals other.f => stable ordering
    def __lt__(self, other: 'Point'):
        if self.x != other.x:
            return self.x < other.x
        return self.y < other.y

    def __add__(self, other: 'Point'):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Point'):
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        if isinstance(other, Point):
            return self._mul_point(other)
        elif isinstance(other, int):
            return self._mul_int(other)

    def _mul_point(self, other: 'Point'):
        return Point(self.x * other.x, self.y * other.y)

    def _mul_int(self, other: int):
        return Point(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, Point):
            return self._div_point(other)
        elif isinstance(other, int):
            return self._div_int(other)

    def _div_point(self, other: 'Point'):
        return Point(int(self.x / other.x), int(self.y / other.y))

    def _div_int(self, other: int):
        return Point(int(self.x / other), int(self.y / other))

    def __iter__(self):
        yield self.x
        yield self.y

    def __repr__(self):
        return f'({self.x}, {self.y})'

    # Euclidean Distance
    def distance(self, other: 'Point'):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    @property
    def key(self):
        return self.x, self.y
