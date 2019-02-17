#ifndef CELL_H
#define CELL_H

#include "point.h"
#include "cellstatus.h"

namespace world {

    class Cell : public Point {
        public:
            CellStatus status;
            double weight;

            Cell(); // implemented for cython
            Cell(int x, int y, CellStatus status);
            ~Cell();

            bool walkable();
    };

}

#endif