#!/usr/bin/python
# ozeasx@gmail.com

import random
from collections import deque
from graph import Graph


class Chromosome(object):
    # Constructor
    def __init__(self, tour, dist=None):
        # Create random tour based on given dimension
        if isinstance(tour, int):
            self._tour = range(1, tour + 1)
            random.shuffle(self._tour)
        # User defined tour
        elif isinstance(tour, (list, tuple, deque)):
            self._tour = tuple(tour)
        # Tour distance
        if dist:
            self._dist = float(dist)
        # Number of cities
        self._dimension = len(self.tour)
        # undirected graph and edges representaition
        if self.tour:
            self._undirected_graph = Graph.gen_undirected_graph(self._tour)
            self._undirected_edges = Graph.gen_undirected_edges(self._tour)

    # Equality (== operator)
    def __eq__(self, other):
        return hash(self) == hash(other)

    # Inequality (!=)
    def __ne__(self, other):
        return not self.__eq__(other)

    # Identity
    def __hash__(self):
        return hash(self._undirected_edges)

    # Get tour
    @property
    def tour(self):
        return self._tour

    # Get tour distance
    @property
    def dist(self):
        return self._dist

    # Get fitness
    @property
    def fitness(self):
        return self._fitness

    # Get dimension
    @property
    def dimension(self):
        return self._dimension

    # Get undirected graph
    @property
    def undirected_graph(self):
        return Graph(self._undirected_graph)

    # Get undirected edges
    @property
    def undirected_edges(self):
        return self._undirected_edges

    # Distance setter
    @dist.setter
    def dist(self, value):
        self._dist = value

    # Fitness setter
    @fitness.setter
    def fitness(self, value):
        self._fitness = value
