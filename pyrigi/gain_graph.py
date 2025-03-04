"""
Module for gain graphs.
"""

import networkx as nx
from collections.abc import Hashable
from sympy.combinatorics import Permutation
from sympy.combinatorics.named_groups import CyclicGroup, DihedralGroup

Group = CyclicGroup | DihedralGroup
GainFunction = dict[Hashable, Permutation]

class GainGraph(nx.MultiDiGraph):
    """
    Class representing a gain graph where the group is cyclic or dihedral.
    """

    def __init__(self, group: Group, gain_function: GainFunction = None, *args, **kwargs) -> None:
        """
        Set up the graph and the gain function.
        """
        super().__init__(*args, **kwargs)

        self._group = group

        if gain_function is not None:
            self._check_gain_function(gain_function)

        self._gain_function = gain_function

    def _check_gain_function(self, gain_function: GainFunction) -> None:
        """
        Check if a gain function has the edge set as the domain and the standard permutation
        representation of the group as the codomain.
        """
        for permutation in gain_function.values():
            if permutation not in self.group:
                raise ValueError("Gain function values must be in the standard permutation representation of the group")

        if set(self.edges(keys=True)) != set(gain_function.keys()):
            raise ValueError("Gain function domain must be edge set")

    @property
    def group(self) -> Group:
        """
        Get the group.

        The group is cyclic or dihedral.
        """
        return self._group

    @group.setter
    def group(self, value: Group) -> None:
        """
        Set the group.

        Parameters
        ----------
        group: group must be cyclic or dihedral.
        """
        self._check_gain_function(self.gain_function)
        self._group = value

    @property
    def gain_function(self) -> GainFunction:
        """
        Get the gain function.

        The gain function maps edges to elements of the standard permutation representation of the
        group.
        """
        return self._gain_function

    @gain_function.setter
    def gain_function(self, value: GainFunction) -> None:
        """
        Set the gain function.

        Parameters
        ----------
        gain_function: gain_function must be a map from the edge set to the standard permutation
        representation of the group.
        """
        self._check_gain_function(value)
        self._gain_function = value

    def remove_node(self, n: Hashable) -> None:
        """
        Remove node n from the graph and gain function.

        Parameters
        ----------
        n: n must be a node in the graph.
        """
        for successor in self.successors(n):
            for key in self.get_edge_data(n, successor):
                del self.gain_function[(n, successor, key)]

        for predecessor in self.predecessors(n):
            for key in self.get_edge_data(predecessor, n):
                del self.gain_function[(predecessor, n, key)]

        super().remove_node(n)
