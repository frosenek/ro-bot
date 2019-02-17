#ifndef MAP_H
#define MAP_H

#include "point.h"

namespace world {

    class Map {
        public:
            int width, height;
            std::vector<std::vector<Cell>> data;

            Map(); // implemented for cython
            Map(unsigned int width, unsigned int height, unsigned char* data);
            ~Map();

            inline bool in_map_bounds(Point &p);
            int status(Point &p);

            std::vector<Cell*> neighbors(Cell &cell, std::vector<Point> &offsets);
            std::vector<Cell*> Map::neighbors(Cell &cell);

            std::vector<Point> path(Point &start, Point &end);

        private:
            void Map::calculate_weight();
            void Map::calculate_weight_around(Cell &cell, std::vector<std::vector<Point>> &weight_range_offsets);
    };

}

#endif