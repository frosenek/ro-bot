#include "cell.h"
#include "cellstatus.h"

namespace world {

    Cell::Cell() : Point() {
        this->status = CellStatus::GROUND_WALKABLE;
        this->weight = 0.0;
    }

    Cell::Cell(int x, int y, CellStatus status) : Point(x, y) {
        this->status = CellStatus(status);
        this->weight = 0.0;
    }

    Cell::~Cell () {}

    bool Cell::walkable() {
        return this->status == CellStatus::GROUND_WALKABLE ||
               this->status == CellStatus::WATER_WALKABLE;
    }

}