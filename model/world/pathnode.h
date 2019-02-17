#ifndef PATHNODE_H
#define PATHNODE_H

#include "point.h"
#include "cell.h"

namespace world {

    class PathNode : public Cell {
        public:
            double f, g, h;
            PathNode* pred;

            PathNode(); // implemented for cython
            PathNode(Cell const &cell);
            PathNode(Cell const &cell, PathNode* predecessor);
            ~PathNode();

            bool operator > (const PathNode &other) const;

            friend std::ostream& operator << (std::ostream& stream, const PathNode& p);

            void calc_f();
            void calc_g();
            void calc_h(Point &target);
    };

}

#endif