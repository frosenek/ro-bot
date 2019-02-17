#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading


class T(threading.Thread):
    lock = threading.Lock()

    def __init__(self):
        super(T, self).__init__()
        self.result = []

    def run(self):
        a = 0
        for _ in range(0, 10000000):
            a += 1
        with self.lock:
            self.result.append(a)

    def has_result(self):
        with self.lock:
            return len(self.result) > 0


t1 = T()
t1.start()
for i in range(0, 100000):
    print(i)
    if t1.has_result():
        break
