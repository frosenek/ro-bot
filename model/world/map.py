from enum import Enum

import logging
import random

from data.file import FieldFile
from model.base import BaseObject, Point, Rectangle

from .exceptions import PathNotFoundException
from .world import ExtMap

# logger
log = logging.getLogger('app.map')
log.setLevel(logging.WARNING)


class CellStatus(Enum):
    GROUND_WALKABLE = 0
    GROUND_UNWALKABLE = 1
    WATER_UNWALKABLE = 2
    WATER_WALKABLE = 3
    WATER_UNWALKABLE_SNIPABLE = 4
    CLIFF_UNWALKABLE_SNIPABLE = 5
    CLIFF_UNWALKABLE = 6
    UNKNOWN = 7

    def walkable(self) -> bool:
        return self == CellStatus.GROUND_WALKABLE or \
               self == CellStatus.WATER_WALKABLE

    def snipable(self) -> bool:
        return self == CellStatus.GROUND_WALKABLE or \
               self == CellStatus.WATER_UNWALKABLE_SNIPABLE or \
               self == CellStatus.CLIFF_UNWALKABLE_SNIPABLE

    def water(self) -> bool:
        return self == CellStatus.WATER_WALKABLE or \
               self == CellStatus.WATER_UNWALKABLE or \
               self == CellStatus.WATER_UNWALKABLE_SNIPABLE

    def cliff(self) -> bool:
        return self == CellStatus.CLIFF_UNWALKABLE or \
               self == CellStatus.CLIFF_UNWALKABLE_SNIPABLE


class Cell(Point):

    def __init__(self, x: int, y: int, status: CellStatus):
        super(Cell, self).__init__(x, y)

        self.x = x
        self.y = y

        # caching commonly queried statuses
        self.walkable = status.walkable()
        self.snipable = status.snipable()
        self.water = status.water()
        self.cliff = status.cliff()

    def __repr__(self):
        return f'Cell {super(Cell, self).__repr__()}'


class Map(BaseObject):
    unwalkable_padding = 5

    char = None
    npcs = []
    mobs = []
    players = []

    def __init__(self, name: str):
        super(Map, self).__init__()

        self.name = name
        self._width, self._height, data = FieldFile(name).load()

        # noinspection PyArgumentList
        self.map = ExtMap(self._width, self._height, data)

        # game saves entity coordinates in float relative to center of the map
        # needed to calculate entities position on the map
        self.x0 = -((self.width / 2) * 5.0)
        self.y0 = -((self.height / 2) * 5.0)

    @property
    def width(self):
        return self._width - 1

    @property
    def height(self):
        return self._height - 1

    def in_unwalkable_padding(self, x: int, y: int):
        if x < self.unwalkable_padding or x > self.width - self.unwalkable_padding:
            return True
        if y < self.unwalkable_padding or y > self.height - self.unwalkable_padding:
            return True
        return False

    @property
    def cells(self):
        for x in range(0, self.width):
            for y in range(0, self.height):
                yield self.cell((x, y))

    def cell(self, key: (int, int)):
        x, y = key

        if 0 > x > self.width:
            raise IndexError
        if 0 > y > self.height:
            raise IndexError

        return Cell(x, y, CellStatus(self.map.status(x, y)))

    def random_walkable_cell(self, area: Rectangle = None):
        if area:
            x0, y0 = area.x0, area.y0
            x1, y1 = area.x1, area.y1
        else:
            x0, y0 = 0, 0
            x1, y1 = self.width, self.height

        while True:
            cell = self.cell((random.randint(x0, x1), random.randint(y0, y1)))
            if cell.walkable:
                break

        return cell

    def set_char(self, char):
        self.char = self.cell(char)

    def set_entities(self, npcs, mobs, players):
        self.npcs = [self.cell((x, y)) for x, y in npcs]
        self.mobs = [self.cell((x, y)) for x, y in mobs]
        self.players = [self.cell((x, y)) for x, y in players]

    def path(self, start: Point, target: Point):
        path = self.map.path(start, target)
        if not path:
            raise PathNotFoundException
        return path
