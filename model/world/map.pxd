# note: cannot use "# distutils: sources = source.cpp" in pxd files
cdef extern from "point.cpp":
    pass

cdef extern from "cell.cpp":
    pass

cdef extern from "pathnode.cpp":
    pass

cdef extern from "map.cpp":
    pass


from libcpp.vector cimport vector


cdef extern from "point.h" namespace "world":
    cdef cppclass Point:
        int x, y

        Point() except +
        Point(int x, int y) except +


cdef extern from "map.h" namespace "world":
    cdef cppclass Map:
        int width, height

        Map() except +
        Map(unsigned int, unsigned int, unsigned char*) except +
        int status(Point)
        vector[Point] path(Point, Point)
