#include <iostream>
#include <cmath>
#include <vector>
#include <iterator>
#include <algorithm>
#include "point.h"

namespace world {

    Point::Point () {
        this->x = 0;
        this->y = 0;
    }

    Point::Point (int x, int y) {
        this->x = x;
        this->y = y;
    }

    Point::~Point () {}

    Point Point::operator + (const Point &other) const {
        return Point(this->x + other.x, this->y + other.y);
    }

    bool Point::operator == (const Point &other) const {
        return this->x == other.x && this->y == other.y;
    }

    bool Point::operator < (const Point &other) const {
        return this->x < other.x || (this->x == other.x && this->y < other.y);
    }

    std::ostream& operator << (std::ostream &out, const Point &p) {
        out << "Point(x: " << p.x << ", y: " << p.y << ")";

        return out;
    }

    // returns vector of points that have to be added to a point p
    // to get all points in the area of a circle with radius "radius" around p
    std::vector<Point> Point::circle_area_offsets(unsigned int radius) {
        std::vector<Point> area;
        int r = (int) radius + 1;
        int nr = r * -1;

        for(int x = nr; x < r + 1; x++) {
            for(int y = nr; y < r + 1; y++) {
                if(r * r > (x * x + y * y) && !(x == 0 && y == 0)) {
                    area.push_back(Point(x, y));
                }
            }
        }

        return area;
    }

    // contains points that have to be added to a point p
    // to get all points on the locus of a circle with radius "radius" around p
    std::vector<Point> Point::circle_locus_offsets(unsigned int radius) {
        std::vector<Point> inner, outer, locus;

        outer = Point::circle_area_offsets(radius);
        inner = Point::circle_area_offsets(radius - 1);

        std::set_difference(
            outer.begin(),
            outer.end(),
            inner.begin(),
            inner.end(),
            std::inserter(
                locus,
                locus.begin()
            )
        );

        return locus;
    }

    double Point::distance(Point &other) {
        return sqrt(pow((this->x - other.x), 2) + pow((this->y - other.y), 2));
    }

}

