#!/usr/bin/python
# ozeasx@gmail.com

from tsp import TSPLIB
from shell import Shell


class VRP(TSPLIB):
    def __init__(self, instance_path):
        # Call super init
        TSPLIB.__init__(self, instance_path)

        # Set capacity
        self._capacity = int(Shell.run("grep CAPACITY " + instance_path
                                       + " | cut -d':' -f2").strip())
        # Mim number of vehicles
        self._trucks = int(Shell.run("grep TRUCKS " + instance_path
                                     + " | cut -d':' -f2").strip())

        # Load demand array
        with open(instance_path) as instance:
            read = False
            self._demand = list()
            for word in instance:
                # End loop if EOF
                if word.strip() == "DEPOT_SECTION":
                    break
                # If do, store tour
                if read:
                    s = word.split()
                    self._demand.append(int(s[1]))
                # If DEMAND_SECTION, set 'read'
                if word.strip() == "DEMAND_SECTION":
                    read = True

        if self._best_solution is not None:
            self._best_solution.load = self.tour_load(self._best_solution.tour)

    # Get vehicles capacity
    @property
    def capacity(self):
        return self._capacity

    # Get best known tour
    @property
    def best_solution(self):
        return self._best_solution

    # Get min number of vehicles
    @property
    def trucks(self):
        return self._trucks

    # Set a new best tour and write to file
    @best_solution.setter
    def best_solution(self, solution):

        # Set best solution
        if self._best_solution is None:
            self._best_solution = solution
        elif (solution.dist < self._best_solution.dist
              and all(load <= self._capacity for load in solution.load)):
            self._best_solution = solution
        else:
            return

        # Write new solution to file
        with open(self._instance_name + ".opt.tour.new", 'w') as best:
            best.write("NAME : " + self._name + ".opt.tour.new\n")
            best.write("COMMENT : Length " + str(solution.dist)
                                           + ", ozeasx@gmail.com\n")
            best.write("TYPE : TOUR\n")
            best.write("DIMENSION : " + str(self._dimension) + "\n")
            best.write("LOAD : " + str(solution.load) + "\n")
            best.write("TOUR_SECTION\n")
            for node in solution.tour:
                best.write(str(node) + "\n")
            best.write("-1\n")
            best.write("EOF\n")

    # Get tour demand
    def tour_load(self, tour):
        demand = list()
        demand.append(0)
        for i, c in enumerate(tour):
            if i == 0:
                continue
            if c == 1:
                demand.append(0)
            else:
                demand[-1] += self._demand[c - 1]
        return tuple(demand)

    # Calc AB_cycle distance using distance matrix (memory)
    def ab_cycle_dist(self, ab_cycle):
        # Convert deque to list
        aux = list(ab_cycle)
        # Distance
        dist = 0
        # Distance lookup
        for i, j in zip(aux[0::2], aux[1::2]):
            # Ignore ghost nodes
            t = [abs(i)-1, abs(j)-1]
            # Depots
            if t[0] >= self._dimension:
                t[0] = 0
            if t[1] >= self._dimension:
                t[1] = 0
            dist += self._dm[self._cindex(*sorted(t))]
        # Return result
        return dist


# Test section
if __name__ == '__main__':
    vrp = VRP("../cvrp/F-n45-k4.vrp")
    # print vrp._capacity
    # print vrp._trucks
    print vrp.ab_cycle_dist([1, 2, 3, 1])
    print vrp.ab_cycle_dist([1, 2, 3, -47])
    print vrp.ab_cycle_dist([1, 2, 3, 47])