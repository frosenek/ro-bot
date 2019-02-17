#ifndef POINT_H
#define POINT_H

namespace world {

    class Point {
        public:
            int x, y;

            Point(); // implemented for cython
            Point(int x, int y);
            ~Point();

            Point operator + (const Point &other) const;
            bool operator == (const Point &other) const;
            bool operator < (const Point &other) const;

            friend std::ostream& operator << (std::ostream& stream, const Point& p);

            static std::vector<Point> Point::circle_area_offsets(unsigned int radius);
            static std::vector<Point> Point::circle_locus_offsets(unsigned int radius);

            double distance(Point &other);
    };

}

#endif