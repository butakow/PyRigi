"""
A module for gain graphs.
"""

from __future__ import annotations

from pyrigi.gain_graph.base import GainGraphBase
from . import _general as general
from ._algorithms import switching

from pyrigi._utils._doc import copy_doc, doc_category, generate_category_tables

from collections.abc import Container, Hashable, Sequence
from pyrigi.data_type import (
    Vertex,
    DirectedMultiEdge,
    Group,
    GroupElement,
    GainFunction,
)


class GainGraph(GainGraphBase):
    """
    Definitions
    -----------
     * :prf:ref:`Gain graph <def-gain-graph>`

    Parameters
    ----------
    group:
        A supported group. If ``group is None``, the initializer will raise a
        :exc:`TypeError`.
    gain_function:
        A gain function on the graph compatible with the group. If an edge in the domain
        of the gain function is not in the graph, it will be added.
    incoming_graph_data:
        See :meth:`networkx.MultiDiGraph.__init__`.
    multigraph_input:
        See :meth:`networkx.MultiDiGraph.__init__`.
    attr:
        Attributes to set for the graph.

    Examples
    --------
    >>> from sympy.combinatorics import CyclicGroup, Permutation
    >>> G = GainGraph(CyclicGroup(4), {0: {1: {2: Permutation(0, 2)(1, 3)}}})
    >>> print(G)
    GainGraph with vertices [0, 1] and gains {(0, 1, 2): (0 2)(1 3)}

    >>> G = GainGraph(CyclicGroup(2), name="Michael")
    >>> G.add_vertices([0, 'a'])
    >>> G.add_edges([(0, 7, Permutation(1)), (0, 7, Permutation(0, 1))])
    [(0, 7, 0), (0, 7, 1)]
    >>> print(G)
    GainGraph with vertices [0, 'a', 7] and gains {(0, 7, 0): (1), (0, 7, 1): (0 1)}
    >>> G.graph["name"]
    'Michael'

    METHODS

    Notes
    -----
    This class subclasses :class:`networkx.MultiDiGraph` and retains its
    structure for graph, vertex, and edge attributes. However, many of its methods are
    overridden to maintain the properties of the gain function. As a result, this class
    is not guaranteed to be compatible with functions of NetworkX graphs, nor can
    NetworkX graph views be created using this class. (Note that
    :meth:`~networkx.MultiDiGraph.to_directed` and
    :meth:`~networkx.MultiDiGraph.to_undirected` create views using the
    :class:`~networkx.MultiDiGraph` and :class:`~networkx.MultiGraph` classes,
    respectively, which is supported.)

    :class:`~sympy.combinatorics.perm_groups.PermutationGroup` overrides
    :meth:`object.__getstate__` to return ``None``, so non-argument attributes of
    instances of :class:`~sympy.combinatorics.perm_groups.PermutationGroup` are not
    preserved on :external+python:ref:`deep copy <shallow_vs_deep_copy>`. Since
    :external+sympy:ref:`SymPy best practices dictate that expressions should be rebuildable from their constructor arguments <best-practices-args-invariants>`,
    this class does not override this behavior of
    :class:`~sympy.combinatorics.perm_groups.PermutationGroup`. In practice, this means
    that if a gain graph ``G`` on a
    :class:`~sympy.combinatorics.perm_groups.PermutationGroup` has a graph, vertex, or
    edge attribute that references an attribute of the group, that reference may not be
    shared by ``copy.deepcopy(G).group``.
    """  # noqa: E501

    @doc_category("Gain graph manipulation")
    @copy_doc(general.update)
    def update(
        self,
        edges: (
            GainGraph
            | Container[
                tuple[Vertex, Vertex, GroupElement]
                | tuple[Vertex, Vertex, GroupElement, Hashable]
                | tuple[Vertex, Vertex, GroupElement, Hashable, dict]
            ]
        ) = None,
        vertices: Container[Vertex | tuple[Vertex, dict]] = None,
    ) -> list[DirectedMultiEdge]:
        return general.update(self, edges=edges, vertices=vertices)

    @doc_category("Other")
    @copy_doc(general.copy)
    def copy(self) -> GainGraph:
        return general.copy(self)

    @doc_category("Other")
    @copy_doc(general.reverse)
    def reverse(self) -> GainGraph:
        return general.reverse(self)

    @doc_category("Gain graph properties")
    @copy_doc(general.walk_gain)
    def walk_gain(self, walk: Sequence[tuple[DirectedMultiEdge, bool]]) -> GroupElement:
        return general.walk_gain(self, walk=walk)

    @doc_category("Gain graph algorithms")
    @copy_doc(switching.switching_operation)
    def switching_operation(
        self,
        v: Vertex,
        element: GroupElement,
        gain_function: GainFunction = None,
        group: Group = None,
    ) -> None:
        switching.switching_operation(
            self, v=v, element=element, gain_function=gain_function, group=group
        )

    @doc_category("Gain graph algorithms")
    @copy_doc(switching.equivalent_gain_function)
    def equivalent_gain_function(
        self,
        forest: Container[DirectedMultiEdge],
        gain_function: GainFunction = None,
        group: Group = None,
    ) -> GainFunction:
        return switching.equivalent_gain_function(
            self, forest=forest, gain_function=gain_function, group=group
        )


GainGraph.__doc__ = GainGraph.__doc__.replace(
    "METHODS",
    generate_category_tables(
        GainGraph,
        1,
        [
            "Attribute getters",
            "Gain graph manipulation",
            "Gain graph properties",
            "Gain graph algorithms",
            "Other",
            "Waiting for implementation",
        ],
        include_all=False,
        add_attributes=False,
    ),
)
