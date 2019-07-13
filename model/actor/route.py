from collections import deque

import logging

from model.base import BaseObject, Signal, Point, Rectangle

log_path = logging.getLogger('app.actor.path')
log_route = logging.getLogger('app.actor.router')

log_path.setLevel(logging.WARNING)
log_route.setLevel(logging.WARNING)

PRT_SEW1_ROUTE = [
    Rectangle(282, 297, 3, 3),
    Rectangle(35, 297, 3, 3),
    Rectangle(124, 261, 3, 3),
    Rectangle(101, 237, 3, 3),
    Rectangle(139, 182, 3, 3),
    Rectangle(76, 180, 3, 3),
    Rectangle(20, 263, 3, 3),
    Rectangle(23, 232, 3, 3),
    Rectangle(34, 181, 3, 3),
    Rectangle(75, 150, 3, 3),
    Rectangle(30, 115, 3, 3),
    Rectangle(30, 82, 3, 3),
    Rectangle(30, 48, 3, 3),
    Rectangle(129, 147, 3, 3),
    Rectangle(30, 20, 3, 3),
    Rectangle(290, 20, 3, 3),
    Rectangle(237, 49, 3, 3),
    Rectangle(285, 49, 3, 3),
    Rectangle(285, 83, 3, 3),
    Rectangle(197, 154, 3, 3),
    Rectangle(285, 116, 3, 3),
    Rectangle(241, 149, 3, 3),
    Rectangle(283, 200, 3, 3),
    Rectangle(285, 233, 3, 3),
    Rectangle(296, 263, 3, 3),
    Rectangle(201, 259, 3, 3),
    Rectangle(221, 231, 3, 3),
    Rectangle(197, 183, 3, 3),
]


class Path(BaseObject):

    def __init__(self, data):
        super(Path, self).__init__()
        self.data = data
        self.idx = 0

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return f'Path [{self.data[0]} -> {self.data[-1]}]'

    def __getitem__(self, item):
        return self.data[item]

    def exists(self):
        return self.data is not None

    def step(self, count=1):
        if self.idx + count < len(self.data):
            self.idx = self.idx + count
        else:
            self.idx = len(self.data) - 1

    def set_closest_to(self, target: Point):
        idx, dist = self.idx, target.distance(self.current_point)
        self.idx, min_dist = min(enumerate(self.data), key=lambda v: target.distance(v[1]))
        log_path.debug(f'Updated step from (s: {idx}, d: {dist:.2f}) to closest step (s: {self.idx}, d: {min_dist})')

    def completed(self):
        return self.idx == len(self.data) - 1

    @property
    def current_point(self):
        return self.data[self.idx]


class RouterUpdateSignal(BaseObject):
    path = Signal(BaseObject)
    zones = Signal(object)

    def __init__(self):
        super(RouterUpdateSignal, self).__init__()


class Route(BaseObject):
    updated = RouterUpdateSignal()

    def __init__(self):
        super(Route, self).__init__()
        self.map = None
        self.zones = None

        self.paths = deque()
        self.idx = 0

        self.previous_point = None
        self.stuck = 0

    def slot_map(self, map):
        self.map = map

        mw, mh = map.width, map.height
        cx, cy = Rectangle(0, 0, self.map.width, self.map.height).center()
        cx, cy = int(cx), int(cy)

        self.zones = [
            Rectangle(0, 0, cx, cy),
            Rectangle(0, cy, cx, mh),
            Rectangle(cx, cy, mw, mh),
            Rectangle(cx, 0, mw, cy),
        ]

        self.updated.zones.emit(self.zones)
        self.reset()

    def reset(self):
        self.paths = deque()
        self.idx = 0

        self.previous_point = None
        self.stuck = 0

    def update(self):
        self.check_character_stuck()

        # ensure that there are always at least two paths prepared
        while len(self.paths) < 2:
            log_route.debug(f'Calculating path no. {len(self.paths) + 1}')
            self.path_to_next_zone()

        # remove completed path
        if self.path.completed() and self.map.char.distance(self.point) < 3:
            log_route.debug(f'End of {self.path} has been reached')
            self.remove_path()

        # distance to current path is stretching too far
        # (maybe the character has wandered off while hunting/avoiding monsters)
        if self.map.char.distance(self.point) > 10:
            log_route.debug(f'1. Too far (d: {self.map.char.distance(self.point):.2f}) off the path')
            # find closest point on path to current position
            self.path.set_closest_to(self.map.char)
            # still distanced too far from path
            # generate a path to the current path
            if self.map.char.distance(self.point) > 10:
                log_route.debug(f'2. Too far (d: {self.map.char.distance(self.point):.2f}) off the path')
                if len(self.paths) > 2:
                    log_route.debug(f'Interim path already exists and will be removed')
                    self.remove_path()
                self.prepend_path(self.point)

        # step forward on the current path until it is at least a distance of 7
        # ahead of our current position
        while self.map.char.distance(self.point) < 9 and not self.path.completed():
            self.path.step()

    def path_to_next_zone(self):
        # if no paths that will be traversed exist the starting point is the characters position
        # otherwise the starting point is the last position of the finally traversed path
        start = self.paths[-1][-1] if self.paths else self.map.char

        if self.zones:
            target = self.map.random_walkable_cell(self.zone)
            self.idx = (self.idx + 1) % len(self.zones)
        else:
            target = self.map.random_walkable_cell()

        self.paths.append(Path(self.map.path(start, target)))
        self.updated.path.emit(self.path)
        log_route.debug(f'Append path => {self.paths}')

    def prepend_path(self, target: Point):
        self.paths.appendleft(Path(self.map.path(self.map.char, target)))
        self.updated.path.emit(self.path)
        log_route.debug(f'Prepended path => {self.paths}')

    def remove_path(self):
        log_route.debug(f'Removing {self.path}')
        self.paths.popleft()
        self.updated.path.emit(self.path)

    def check_character_stuck(self):
        if self.previous_point is not None:
            if self.map.char == self.previous_point:
                self.stuck = self.stuck + 1
            else:
                self.stuck = 0
        self.previous_point = self.map.char

    @property
    def path(self):
        if self.paths:
            return self.paths[0]
        return None

    @property
    def point(self):
        if self.path:
            return self.path.current_point

    @property
    def zone(self):
        if self.zones:
            return self.zones[self.idx % len(self.zones)]
        return None
