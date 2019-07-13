import logging

from model.world import PathNotFoundException

log = logging.getLogger('app.actor.fighter')
log.setLevel(logging.DEBUG)

# dictionary: target -> priority (lower value := higher priority)
# TARGET_PRIORITY_MAP = {1048: 1}
TARGET_PRIORITY_MAP = {1271: 1, 1077: 1} # alligator / poison spore


# TARGET_PRIORITY_MAP = {1013: 1, 1092: 1}
# TARGET_PRIORITY_MAP = {1023: 2, 1273: 2, 1686: 1}
# TARGET_PRIORITY_MAP = {1170: 2, 1188: 2, 1186: 2, 1068: 2, 1028: 2, 1026: 2, 1016: 1}

class Fight:

    def __init__(self, input):
        self.input = input
        self.last = None
        self.target = None
        self.targets = None

        self.map = None
        self.char = None
        self.mobs = None
        self.players = None

        self.active = False
        self.target_died = False

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
                log.debug(f'Player near: {player}')
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

        # Mob entities persist after dying for displaying their death animation.
        # Combined with the circumstance that health information only exists if
        # the health is neither full nor empty the active and last attributes are
        # needed to avoid moving to the point at which the mob died.
        if self.target is not None and self.active:
            if self.target.health is None:
                self.last = self.target
                self.target = None
                self.active = False
        elif self.target is not None and not self.active:
            if self.target.health is not None:
                self.active = True

        if self.target is None and not self.targets:
            self.active = False
            return

        while self.target is None and self.targets and not self.players_near():
            self.target = self.targets.pop(0)
            if self.target == self.last:
                self.target = None

        if self.target is None:
            self.active = False
            return

        while True:
            try:
                path_to_target = self.map.path(self.char, self.target)
                # path to target likely blocked by unwalkable area
                if len(path_to_target) < 15:
                    break
            except PathNotFoundException:
                pass

            log.debug(f'Target {self.target} not reachable')
            # try next target in list
            if len(self.targets) > 0:
                self.target = self.targets.pop(0)
                log.debug(f'Acquired new target {self.target}')
            # all targets seem to be out of reach
            else:
                log.debug(f'Could not acquire target')
                self.target = None
                return

        # enemy is pretty far away, the router is probably not needed though
        # with an interim point to walk to
        # FIXME: for ranged characters
        if self.char.distance(self.target) > 10:
            interim = self.char + ((self.target - self.char) / 2)
            log.debug(f'Moving to {interim} in order to reach target {self.target}')
            self.input.mouse_drag(self.char, interim)
            self.input.mouse_click(self.char, interim)
            return
