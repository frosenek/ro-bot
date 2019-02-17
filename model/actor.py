from collections import deque

import pyautogui as atg
import random
import logging
import time

from model.base import BaseObject, Signal, Point, Rectangle
from model.game import Game
from model.world import PathNotFoundException

log = logging.getLogger('app.actor')
log_path = logging.getLogger('app.actor.path')
log_router = logging.getLogger('app.actor.router')
log_fighter = logging.getLogger('app.actor.fighter')

log.setLevel(logging.WARNING)
log_path.setLevel(logging.WARNING)
log_router.setLevel(logging.WARNING)
log_fighter.setLevel(logging.WARNING)

CELL_PIXEL_SIZE = Point(37, 29)

TARGET_PRIORITY_MAP = {1271: 1, 1077: 1}
# dictionary: target -> priority (lower value := higher priority)
# TARGET_PRIORITY_MAP = {1013: 1, 1092: 1}
# TARGET_PRIORITY_MAP = {1023: 2, 1273: 2, 1686: 1}
# TARGET_PRIORITY_MAP = {1170: 2, 1188: 2, 1186: 2, 1068: 2, 1028: 2, 1026: 2, 1016: 1}


def ease_out_elastic(n):
    return atg.easeOutElastic(n, amplitude=0.5, period=1)


class Timer:

    def __init__(self, interval: int, start_elapsed=True):
        self.interval = interval
        self.init = 0 if start_elapsed else time.time()

    def elapsed(self):
        return time.time() - self.init > self.interval

    def reset(self):
        self.init = time.time()


class Key:

    def __init__(self, symbol: str, timer=None):
        self.symbol = symbol
        self.timer = timer

    def press(self):
        atg.press(self.symbol)


class Input:

    def __init__(self, screen: Rectangle):
        self.screen = screen
        self.timed_keys = []
        self.timed_keys = [
            Key('f2', Timer(301)),  # two-hand quicken
            Key('f5', Timer(181)),  # authoritative badge
            Key('f6', Timer(1801)),  # awakening potion
        ]

    def translate_coordinates(self, start: Point, target: Point):
        a, b = (target - start) * CELL_PIXEL_SIZE
        x, y = self.screen.center()
        r1, r2 = random.randint(-2, 2), random.randint(-2, 2)
        return Point(x + a + r1, y - b + r2)

    def move_to(self, start: Point, target: Point):
        x, y = self.translate_coordinates(start, target)
        atg.dragTo(x, y, button='left', tween=ease_out_elastic)

    def attack_at(self, start: Point, target: Point):
        x, y = self.translate_coordinates(start, target)
        x, y = x, y + random.randint(0, 10)
        atg.moveTo(x, y)
        atg.click(x, y)

    def timed_events(self):
        for key in self.timed_keys:
            if key.timer.elapsed():
                key.press()
                key.timer.reset()


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


class Router(BaseObject):
    updated = RouterUpdateSignal()

    def __init__(self):
        super(Router, self).__init__()
        self.map = None
        self.zones = [
            Rectangle(66, 350, 5, 5),
            Rectangle(60, 50, 5, 5),
            Rectangle(170, 180, 5, 5),
            Rectangle(210, 90, 5, 5),
            Rectangle(66, 350, 5, 5),
            Rectangle(320, 120, 5, 5),
            Rectangle(170, 340, 5, 5)
        ]
        # self.zones = [
        #     Rectangle(40, 260, 120, 100),
        #     Rectangle(40, 150, 120, 100),
        #     Rectangle(40, 20, 120, 120),
        #     Rectangle(170, 20, 100, 120),
        #     Rectangle(170, 150, 100, 100),
        #     Rectangle(280, 110, 25, 100),
        #     Rectangle(280, 20, 20, 20),
        #     Rectangle(170, 260, 100, 100),
        # ]

        self.paths = deque()
        self.idx = 0

        self.previous_point = None
        self.stuck = 0

    def slot_map(self, map):
        self.map = map
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
            log_router.debug(f'Calculating path no. {len(self.paths) + 1}')
            self.path_to_next_zone()

        # remove completed path
        if self.path.completed() and self.map.char.distance(self.point) < 3:
            log_router.debug(f'End of {self.path} has been reached')
            self.remove_path()

        # distance to current path is stretching too far
        # (maybe the character has wandered off while hunting/avoiding monsters)
        if self.map.char.distance(self.point) > 10:
            log_router.debug(f'1. Too far (d: {self.map.char.distance(self.point):.2f}) off the path')
            # find closest point on path to current position
            self.path.set_closest_to(self.map.char)
            # still distanced too far from path
            # generate a path to the current path
            if self.map.char.distance(self.point) > 10:
                log_router.debug(f'2. Too far (d: {self.map.char.distance(self.point):.2f}) off the path')
                if len(self.paths) > 2:
                    log_router.debug(f'Interim path already exists and will be removed')
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
        log_router.debug(f'Append path => {self.paths}')

    def prepend_path(self, target: Point):
        self.paths.appendleft(Path(self.map.path(self.map.char, target)))
        self.updated.path.emit(self.path)
        log_router.debug(f'Prepended path => {self.paths}')

    def remove_path(self):
        log_router.debug(f'Removing {self.path}')
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


class Fighter:

    def __init__(self, input):
        self.input = input
        self.target = None
        self.targets = None

        self.map = None
        self.char = None
        self.mobs = None
        self.players = None

    def slot_char(self, char):
        self.char = char

    def slot_map(self, map):
        self.map = map

    def slot_entities(self, _, mobs, players):
        self.mobs = mobs
        self.players = players

    def prepare_targets(self):
        if not TARGET_PRIORITY_MAP:
            self.targets = self.mobs
            return

        targets = filter(
            lambda mob: mob.id in TARGET_PRIORITY_MAP,
            self.mobs,
        )

        targets_by_priority_and_distance = sorted(
            targets,
            key=lambda mob: (TARGET_PRIORITY_MAP[mob.id], self.char.distance(mob))
        )

        self.targets = list(targets_by_priority_and_distance)

    def players_near(self):
        if not self.players:
            return False

        for player in self.players:
            # there are some entities that cannot yet be differentiated from players
            # but they are always at the same point and are invisible
            if self.char.distance(player) < 20:
                log.info(f'Player near: {player}')
                return True
        return False

    def retrieve_target_mob(self):
        if self.target is None:
            return

        # compares pointer and mob id
        # health information might have been updated
        for mob in self.targets:
            if self.target == mob:
                self.target = mob
                return

        self.target = None

    def has_target(self):
        return self.target is not None

    def update(self):
        self.prepare_targets()

        if not self.targets:
            self.target = None
            return

        self.retrieve_target_mob()

        if self.target is None:
            log_fighter.debug(f'Target not found')
            # do not start new fights if players are nearby
            if not self.players_near():
                self.target = self.targets.pop(0)
                log_fighter.debug(f'Aquired new target {self.target}')
            else:
                return

        while True:
            try:
                path_to_target = self.map.path(self.char, self.target)
                # path to target likely blocked by unwalkable area
                if len(path_to_target) < 15:
                    break
            except PathNotFoundException:
                pass

            log_fighter.debug(f'Target {self.target} not reachable')
            # try next target in list
            if len(self.targets) > 0:
                self.target = self.targets.pop(0)
                log_fighter.debug(f'Acquired new target {self.target}')
            # all targets seem to be out of reach
            else:
                log_fighter.debug(f'Could not acquire target')
                self.target = None
                return

        # enemy is pretty far away, the router is probably not needed though
        # with an interim point to walk to
        # FIXME: for ranged characters
        if self.char.distance(self.target) > 10:
            interim = self.char + ((self.target - self.char) / 2)
            log_fighter.debug(f'Moving to {interim} in order to reach target {self.target}')
            self.input.move_to(self.char, interim)
            return


class Actor:

    def __init__(self, game: Game, screen: Rectangle):
        self.game = game
        self.input = Input(screen)

        self.router = Router()
        self.game.updated.map.connect(self.router.slot_map)

        self.fighter = Fighter(self.input)
        self.game.updated.map.connect(self.fighter.slot_map)
        self.game.updated.char.connect(self.fighter.slot_char)
        self.game.updated.entities.connect(self.fighter.slot_entities)

    def act(self):
        self.input.timed_events()
        self.fighter.update()

        if self.fighter.has_target():
            self.input.attack_at(self.fighter.char, self.fighter.target)
            return

        self.router.update()
        self.input.move_to(self.router.map.char, self.router.point)
