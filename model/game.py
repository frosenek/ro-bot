import ctypes as ct
import logging

from data.process import Process, Window

from model.base import BaseObject, Point, Signal
from model.world import Map

log = logging.getLogger('app.game')


class Health:
    max = None
    current = None

    def __init__(self, max: int, current: int):
        self.max = max
        self.current = current

    def __repr__(self):
        return f'HP {self.current}/{self.max}'


class Entity(Point):

    def __init__(self, index: int, entity_id: int, x: int, y: int):
        super(Entity, self).__init__(x, y)

        self.index = index
        self.id = entity_id

    def __repr__(self):
        return f'Entity {self.id} ({self.x}, {self.y})'


class LivingEntity(Entity):

    def __init__(self, *args):
        super(LivingEntity, self).__init__(*args)

        self.health = None


class Character(LivingEntity):

    def __init__(self, x: int, y: int):
        super(Character, self).__init__(None, None, x, y)
        self.mouse_over_entity = False
        self.mouse_clicked_entity = False

    def __repr__(self):
        r = f'Character ({self.x}, {self.y})'
        r = r if self.health is None else f'{r}, {self.health}'
        return r


class Mob(LivingEntity):

    def __init__(self, *args):
        super(Mob, self).__init__(*args)

    def __eq__(self, other):
        if other is None:
            return False
        else:
            return self.index == other.index and self.id == other.id

    def __repr__(self):
        r = f'Mob {self.id} ({self.x}, {self.y})'
        r = r if self.health is None else f'{r}, {self.health}'
        return r


class MouseOver:

    def __init__(self):
        self.player = False
        self.char = False
        self.mob = False
        self.npc = False
        self.warp = False
        self.shop = False


class MouseFocus:

    def __init__(self):
        self.mob = False


class MouseState:

    def __init__(self):
        self.over = MouseOver()
        self.focus = MouseFocus()


class GameUpdateSignal(BaseObject):
    map = Signal(BaseObject)
    char = Signal(BaseObject)
    entities = Signal(object, object, object)

    def __init__(self):
        super(GameUpdateSignal, self).__init__()


class Game(BaseObject):
    updated = GameUpdateSignal()

    def __init__(self, window_name, process_name: str):
        super(Game, self).__init__()

        self.mouse_state = None

        self.window = Window(window_name)
        self.process = Process(process_name, Process.PROCESS_VM_READ)
        self.memory = self.process.memory
        self.base = 0x400000

        self.map = None
        self.char = None

        self.mobs = list()
        self.npcs = list()
        self.players = list()

    def read(self):
        self.read_map()
        self.read_mouse_state()
        self.read_character()
        self.read_entities()

    def read_mouse_state(self):
        self.mouse_state = MouseState()

        mouse_status_ptr = self.memory.read_ptr_indirect(ct.c_ulong(), self.base, 0x62AA14)

        # defines sprite of mouse pointer
        # 0 => normal mouse
        # 1 => speech bubble => npc
        # 2 => pointing finger => shop, clickable buttons
        # 4 => rotation (right-click)
        # 5 => sword => mob
        # 7 => door => warp
        # 9 => grab item
        # 10 => skill circle
        mouse_sprite = self.memory.read_uint32(mouse_status_ptr + 0xD0 - 0x7C)

        # pointer that only gets set on mouse overs of players
        mouse_over_player = self.memory.read_uint32(mouse_status_ptr + 0xD0 + 0x20)

        # (likely) pointer or offset to a pointer that is set on all mouse overs except shops
        # TODO: Figure out data(structure) at pointers location and what they point to exactly
        mouse_over_entity = self.memory.read_uint32(mouse_status_ptr + 0xD0 + 0x274)

        # set on clicking an entity (in case of mobs: gets set to 0 upon death)
        mouse_focused_entity = self.memory.read_uint32(mouse_status_ptr + 0xD0 + 0x278)

        self.mouse_state.focus.mob = mouse_focused_entity > 0

        if mouse_over_entity > 0:
            if mouse_over_player > 0:
                self.mouse_state.over.player = True
            elif mouse_sprite == 0:
                self.mouse_state.over.char = True

        if mouse_sprite == 1:
            self.mouse_state.over.npc = True
        elif mouse_sprite == 2:
            self.mouse_state.over.shop = True
        elif mouse_sprite == 5:
            self.mouse_state.over.mob = True
        elif mouse_sprite == 7:
            self.mouse_state.over.warp = True

    def read_character(self):
        char_data_ptr = self.memory.read_ptr_indirect(ct.c_ulong(), self.base, 0x62AA14, 0xD0, 0x3C)

        # target coordinate that the character is currently moving to
        # target_x = self.memory.read_uint32(char_data_ptr + 0x140)
        # target_y = self.memory.read_uint32(char_data_ptr + 0x144)

        # current position (float) relative to center of the map
        xf = self.memory.read_float(char_data_ptr + 0x4)
        yf = self.memory.read_float(char_data_ptr + 0xC)

        # convert float coordinate to int
        x = int((xf - self.map.x0) / 5)
        y = int((yf - self.map.y0) / 5)

        self.char = Character(x, y)
        self.updated.char.emit(self.char)

    def read_map(self):
        mapname_addr = self.base + 0x62AA18
        mapname = str()

        while True:
            c = chr(self.memory.read_byte(mapname_addr))
            if c == '.':
                break
            mapname = mapname + c
            mapname_addr = mapname_addr + 1

        if self.map is not None:
            if self.map.name == mapname:
                return

        self.map = Map(mapname)

        # connect current map to entity and character data updates
        # since it only gets recreated on map change
        self.updated.entities.connect(self.map.set_entities)
        self.updated.char.connect(self.map.set_char)
        # note: slot connections get cleaned up by QObject destructor

        self.updated.map.emit(self.map)

    # Doubly linked list of entities
    # size: self.base + 0x62AA14, 0xD0, 0x14 + 4
    # root: self.base + 0x62AA14, 0xD0, 0x14
    #   node.next -> 0x0
    #   node.prev -> 0x4
    def read_entities(self):
        base = self.memory.read_ptr_indirect(ct.c_ulong(), self.base, 0x62AA14, 0xD0)
        size = self.memory.read_uint32(base + 0x14 + 0x4)
        node = self.memory.read_ptr_indirect(ct.c_ulong(), base, 0x14, 0x0)

        self.mobs, self.npcs, self.players = [], [], []
        while size > 0:

            # read entity
            entity_data_ptr = self.memory.read_ptr(node, 0x8)

            # set node pointer to next node and decrease counter
            node = self.memory.read_ptr(node)
            size = size - 1

            # for mobs entity_id will be a mob id which range from 1001 to 2308
            # players sometimes have seemingly random (very big) values allocated
            # npcs seem to have ids < 1000
            entity_id = self.memory.read_uint16(entity_data_ptr + 0x104)

            # target coordinate that the entity is currently moving to
            # target_x = self.memory.read_uint32(entity + 0x140)
            # target_y = self.memory.read_uint32(entity + 0x144)

            # current position (float) relative to center of the map
            xf = self.memory.read_float(entity_data_ptr + 0x4)
            yf = self.memory.read_float(entity_data_ptr + 0xC)

            # convert float coordinate to int
            x = int((xf - self.map.x0) / 5)
            y = int((yf - self.map.y0) / 5)

            # likely another player
            if entity_id == 0 or entity_id > 2308:
                self.players.append(Entity(entity_data_ptr, entity_id, x, y))
                continue

            # likely a non-playable character
            if entity_id < 1000:
                self.npcs.append(Entity(entity_data_ptr, entity_id, x, y))
                continue

            # entity_id seems to be a mob id
            mob = Mob(entity_data_ptr, entity_id, x, y)

            # try reading mob health data
            health = self.memory.read_ptr(entity_data_ptr, 0x2E8)
            health_cur = self.memory.read_uint32(health + 0x78)
            health_max = self.memory.read_uint32(health + 0x7C)

            if 0 < health_cur < health_max:
                mob.health = Health(health_max, health_cur)
            self.mobs.append(mob)
        self.updated.entities.emit(self.npcs, self.mobs, self.players)
