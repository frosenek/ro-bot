#include <algorithm>
#include <iterator>
#include <vector>
#include <deque>
#include <set>
#include <map>
#include <utility>

#include "map.h"
#include "point.h"
#include "cellstatus.h"

namespace world {

    struct cmp_min_heap {
        bool operator()(PathNode* &lhs, PathNode* &rhs) const {
            return *lhs > *rhs;
        }
    };

    Map::Map() {}

    Map::Map(unsigned int width, unsigned int height, unsigned char* data) {
        this->width = width;
        this->height = height;
        this->data = std::vector<std::vector<Cell>>(width, std::vector<Cell>(height, Cell()));

        for(unsigned int x = 0; x < width; x++) {
            for(unsigned int y = 0; y < height; y++) {
                this->data[x][y] = Cell(x, y, CellStatus(data[x * height + y]));
            }
        }

        this->calculate_weight();
    }

    Map::~Map() {}

    inline bool Map::in_map_bounds(Point &p) {
        return p.x >= 0 && p.y >= 0 && p.x < this->width && p.y < this->height;
    }

    int Map::status(Point &p) {
        if(this->in_map_bounds(p))
            return this->data[p.x][p.y].status;
        return CellStatus::GROUND_UNWALKABLE;
    }

    std::vector<Cell*> Map::neighbors(Cell &cell, std::vector<Point> &offsets) {
        std::vector<Cell*> neighbors;

        for(auto &offset : offsets) {
            Point neighbor_point = cell + offset;
            if(this->in_map_bounds(neighbor_point)) {
                neighbors.push_back(&this->data[neighbor_point.x][neighbor_point.y]);
            }
        }

        return neighbors;
    }

    std::vector<Cell*> Map::neighbors(Cell &cell) {
        return this->neighbors(cell, Point::circle_area_offsets(1));
    }

    void Map::calculate_weight() {
        std::vector<std::vector<Point>> weight_range_offsets;
        for(int i = 0; i < 6; i++) {
            weight_range_offsets.push_back(Point::circle_locus_offsets(i));
        }

        for(auto &col : this->data) {
            for(auto &cell : col){
                if(!cell.walkable()) {
                    this->calculate_weight_around(cell, weight_range_offsets);
                }
            }
        }
    }

    void Map::calculate_weight_around(Cell &cell, std::vector<std::vector<Point>> &weight_range_offsets) {
        int i = 1;
        double weight;

        for(auto &locus_offsets : weight_range_offsets) {
            weight = 3.0 / i; // decrease weight the farther away from p
            for(auto &neighbor : this->neighbors(cell, locus_offsets)) {
                if(neighbor->walkable() && neighbor->weight < weight) {
                    neighbor->weight = weight;
                }
            }
            i++;
        }
    }

    std::vector<Point> Map::path(Point &start, Point &end) {
        // Caching offsets to immediate neighbors because they are reused often.
        std::vector<Point> neighbor_offsets = Point::circle_area_offsets(1);

        // path: contains copy of all PathNode-Points that form the resulting path
        std::vector<Point> path;

        // nodes: contains all created PathNodes
        std::deque<PathNode> nodes;

        // A min-heap that is used to keep track of the PathNode* with the lowest f
        std::vector<PathNode*> heap;

        std::map<Cell, PathNode*> open;
        std::set<Cell> closed;

        PathNode *current, *target, *neighbor, *neighbor_other;

        nodes.push_back(PathNode(this->data[start.x][start.y]));
        current = &nodes.back();
        nodes.push_back(PathNode(this->data[end.x][end.y]));
        target = &nodes.back();

        open[*current] = current;
        heap.push_back(current);
        while(heap.size()) {
            std::make_heap(heap.begin(), heap.end(), cmp_min_heap());
            std::pop_heap(heap.begin(), heap.end(), cmp_min_heap());

            // Retrieve PathNode* with lowest f from min-heap.
            // The value f represents the sum of the work that has to be done to reach a cell
            // and the distance to the target.
            current = heap.back();

            heap.pop_back();

            // Mark current PathNode as evaluated.
            closed.insert(*current);

            // Break loop if target has been found.
            if(*current == *target) {
                target = current;
                break;
            }

            for(auto &cell_neighbor : this->neighbors(*current, neighbor_offsets)) {
                // Neighbor might be unwalkable or cell already evaluated.
                if(cell_neighbor->walkable() && (closed.find(*cell_neighbor) == closed.end())) {
                    nodes.push_back(PathNode(*cell_neighbor, current));
                    neighbor = &nodes.back();

                    // Calculate g (work that has to be done to reach this point).
                    // node.predecessor.g + node.weight + 1.0
                    neighbor->calc_g();

                    // Check wether neighbor is already in the open map because of another path.
                    auto neighbor_search = open.find(*cell_neighbor);
                    if(neighbor_search != open.end()) {
                        neighbor_other = (*neighbor_search).second;
                        if(neighbor_other->g < neighbor->g) {
                            // Neighbor PathNode's work to be done to reach the Point is greater
                            // than the PathNode's from the open map.
                            // Do not further evaluate because the path is more expensive.
                            continue;
                        } else {
                            // Remove the more expensive PathNode from the heap and open map.
                            heap.erase(
                                std::remove(
                                    heap.begin(),
                                    heap.end(),
                                    neighbor_other
                                ),
                                heap.end()
                            );
                            open.erase(neighbor_search);
                        }
                    }

                    // Calculate h (distance to the target).
                    // Euclidean distance
                    neighbor->calc_h(*target);

                    // Calculate f the sum of g and h, which is used for ordering the min-heap.
                    neighbor->calc_f();

                    heap.push_back(neighbor);
                    std::push_heap(heap.begin(), heap.end());
                    open[*neighbor] = neighbor;
                }
            }
        }

        if(target->pred == 0) {
            return path;
        }

        do {
            path.push_back(*target);
            target = target->pred;
        } while(target->pred != 0);

        std::reverse(path.begin(), path.end());
        path.shrink_to_fit();

        return path;
    }

}

