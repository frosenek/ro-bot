#ifndef CELLSTATUS_H
#define CELLSTATUS_H

namespace world {

    enum CellStatus {
        GROUND_WALKABLE = 0,
        GROUND_UNWALKABLE = 1,
        WATER_UNWALKABLE = 2,
        WATER_WALKABLE = 3,
        WATER_UNWALKABLE_SNIPABLE = 4,
        CLIFF_UNWALKABLE_SNIPABLE = 5,
        CLIFF_UNWALKABLE = 6,
        UNKNOWN = 7
    };

}

#endif