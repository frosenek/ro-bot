#include <iostream>
#include "pathnode.h"

namespace world {

    PathNode::PathNode() : Cell() {
        this->f = 0.0;
        this->g = 0.0;
        this->h = 0.0;
        this->pred = 0;
    }

    PathNode::PathNode(Cell const &cell) : Cell(cell) {
        this->f = 0.0;
        this->g = 0.0;
        this->h = 0.0;
        this->pred = 0;
    }

    PathNode::PathNode(Cell const &cell, PathNode* predecessor) : PathNode(cell) {
        this->f = 0.0;
        this->g = 0.0;
        this->h = 0.0;
        this->pred = predecessor;
    }

    PathNode::~PathNode () {}

    bool PathNode::operator > (const PathNode &other) const {
        return this->f > other.f;
    }

    std::ostream& operator << (std::ostream &out, const PathNode &p) {
        out << "PathNode(x: " << p.x << ", y: " << p.y << ", f: " << p.f << ", g: " << p.g << ")";

        return out;
    }

    // A*
    void PathNode::calc_f() {
        this->f = this->g + this->h;
    }

    void PathNode::calc_g() {
        if(this->pred != 0) {
            this->g = this->pred->g + this->weight + 1.0;
        }
    }

    void PathNode::calc_h(Point &target) {
        this->h = this->distance(target);
    }
}