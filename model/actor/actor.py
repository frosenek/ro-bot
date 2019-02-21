import pyautogui as atg
import random
import logging
import time

from model.base import Point, Rectangle
from model.game import Game

from .fight import Fight
from .route import Route

log = logging.getLogger('app.actor')
log.setLevel(logging.WARNING)

CELL_PIXEL_SIZE = Point(37, 29)


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
        self.x = 0
        self.y = 0
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
        self.x, self.y = x + a + r1, y - b + r2

    def mouse_move(self, start: Point, target: Point):
        self.translate_coordinates(start, target)
        atg.moveTo(self.x, self.y, tween=ease_out_elastic)

    def mouse_drag(self, start: Point, target: Point):
        self.translate_coordinates(start, target)
        atg.dragTo(self.x, self.y, tween=ease_out_elastic)

    def mouse_click(self, start: Point, target: Point):
        self.translate_coordinates(start, target)
        atg.click(self.x, self.y)

    def timed_events(self):
        for key in self.timed_keys:
            if key.timer.elapsed():
                key.press()
                key.timer.reset()


class Actor:

    def __init__(self, game: Game, screen: Rectangle):
        self.game = game
        self.input = Input(screen)

        self.route = Route()
        self.game.updated.map.connect(self.route.slot_map)

        self.fight = Fight(self.input)
        self.game.updated.map.connect(self.fight.slot_map)
        self.game.updated.char.connect(self.fight.slot_char)
        self.game.updated.entities.connect(self.fight.slot_entities)

    def act(self):
        self.input.timed_events()
        self.fight.update()

        if self.fight.has_target():
            if self.game.mouse_state.focus.mob:
                self.input.mouse_move(self.fight.char, self.fight.char)
            elif self.game.mouse_state.over.mob:
                self.input.mouse_click(self.fight.char, self.fight.target)
            else:
                self.input.mouse_drag(self.fight.char, self.fight.target)
            return

        self.route.update()
        self.input.mouse_drag(self.game.char, self.route.point)
        self.input.mouse_click(self.game.char, self.route.point)
