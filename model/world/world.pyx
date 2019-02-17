# distutils: language = c++

import numpy as np
cimport numpy as np

from model.base import Point

cimport model.world.map as ext

cdef class ExtMap:
    cdef ext.Map*map

    def __cinit__(self, unsigned int width, unsigned int height, np.ndarray[unsigned char, ndim=2, mode="c"] data):
        self.map = new ext.Map(width, height, &data[0, 0])

    def __dealloc__(self):
        del self.map

    def path(self, start: Point, target: Point):
        cdef int x0, y0, x1, y1
        x0, y0, x1, y1 = start.x, start.y, target.x, target.y

        path, cpp_path = [], self.map.path(ext.Point(x0, y0), ext.Point(x1, y1))
        for cpp_point in cpp_path:
            path.append(Point(cpp_point.x, cpp_point.y))

        return path

    @property
    def width(self):
        return self.map.width

    @property
    def height(self):
        return self.map.height

    def status(self, int x, int y):
        return self.map.status(ext.Point(x, y))
