import ctypes as ct
import logging
from contextlib import suppress
from ctypes.wintypes import *

import PyHook3
import psutil
import pythoncom

from model.base import Rectangle

log = logging.getLogger('app.process')
log.setLevel(logging.WARNING)

kernel32 = ct.windll.kernel32
user32 = ct.windll.user32

WNDENUMPROC = ct.WINFUNCTYPE(BOOL, HWND, LPARAM)


class KeyboardHook:
    callbacks = []

    def __init__(self):
        self.pressed = set()
        self.hook_manager = PyHook3.HookManager()
        self.hook_manager.KeyDown = self.on_key_down
        self.hook_manager.KeyUp = self.on_key_up
        self.hook_manager.HookKeyboard()

    def on_key_down(self, event):
        if event.KeyID not in self.pressed:
            self.pressed.add(event.KeyID)
            self.callback()
        return True

    def on_key_up(self, event):
        with suppress(Exception):
            self.pressed.remove(event.KeyID)
        return True

    def set_callback(self, callback, keys):
        self.callbacks.append([callback, keys])

    def callback(self):
        for callback, keys in self.callbacks:
            call = True
            for key in keys:
                if key not in self.pressed:
                    call = False
            if call:
                callback()

    @staticmethod
    def flush():
        pythoncom.PumpMessages()

    def close(self):
        self.hook_manager.UnhookKeyboard()
        user32.PostQuitMessage(0)


class Memory(object):

    def __init__(self, process):
        self._process = process

    def read(self, result, addr: int):
        kernel32.ReadProcessMemory(self._process, addr, ct.byref(result), ct.sizeof(result), 0)
        log.debug(f'Address: {hex(addr)}, value:{result.value}')
        return result.value

    def read_uint16(self, addr: int):
        return self.read(ct.c_ushort(), addr)

    def read_uint32(self, addr: int):
        return self.read(ct.c_ulong(), addr)

    def read_float(self, addr: int):
        return self.read(ct.c_float(), addr)

    def read_byte(self, addr: int):
        return self.read(ct.c_byte(), addr)

    def read_ptr(self, addr: int, offset=0x0):
        log.debug(f'Base: {hex(addr)}, offset: {hex(offset)}')
        return self.read(ct.c_ulong(), addr + offset)

    def read_ptr_indirect(self, result, addr: int, *args):
        base = addr

        if len(args) == 0:
            return self.read(result, addr)

        if len(args) == 1:
            return self.read_ptr(addr, args[0])

        if len(args) > 1:
            for o in args[:-1]:
                if base != 0x0 and addr == 0x0:
                    log.warning('Address has become 0x0 - maybe incorrect pointer?')
                addr = self.read_ptr(addr, o)
        return self.read(result, addr + args[-1])


class Process(object):
    PROCESS_VM_READ = 0x0010
    PROCESS_VM_WRITE = 0x0020

    def __init__(self, name: str, open_privileges=None):
        self.name = name
        self.pid = self._pid()

        self.handle = None
        self.memory = None

        if open_privileges is not None:
            self.open(open_privileges)

    def __del__(self):
        if self.handle is not None:
            self.close()

    def exists(self):
        return self._pid() > 0

    def open(self, privileges):
        if self.pid == 0:
            log.error('Process could not be opened - pid not found')
            raise RuntimeError("Process could not be opened")
        self.handle = kernel32.OpenProcess(privileges, 0, self.pid)
        self.memory = Memory(self.handle)

    def close(self):
        kernel32.CloseHandle(self.handle)
        self.handle = None

    def _pid(self):
        for process in psutil.process_iter():
            if process.name() == self.name:
                return process.pid
        else:
            return 0


class Window(object):

    def __init__(self, name: str):
        self.name = name
        self.hwnd = None
        self.enum_windows()

    def center(self, screen):
        (_, _, w, h) = self.geometry()

        x = int((screen.w - w) / 2)
        y = int((screen.h - h) / 2)

        self.foreground()
        self.reposition(x, y)

    def geometry(self):
        rect = self.window_rect()
        return Rectangle(rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)

    def window_rect(self):
        rect = RECT()
        user32.GetWindowRect(self.hwnd, ct.byref(rect))
        return rect

    def foreground(self):
        user32.BringWindowToTop(self.hwnd)
        user32.SetForegroundWindow(self.hwnd)

    def reposition(self, x, y):
        (_, _, w, h) = self.geometry()
        user32.MoveWindow(self.hwnd, x, y, w, h, False)

    def enum_windows(self):
        user32.EnumWindows(WNDENUMPROC(self.wnd_enum_proc), 0)

    def wnd_enum_proc(self, hwnd, lParam):
        length = user32.GetWindowTextLengthW(hwnd) + 1
        buffer = ct.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buffer, length)

        self.hwnd = None
        if self.name in buffer.value:
            self.hwnd = hwnd
            return False
        return True
