"""
A module for functionality related to the switching operation.
"""

import networkx as nx
from pyrigi.gain_graph.base import GainGraphBase

from pyrigi._utils import _input_check

from collections.abc import Container
from pyrigi.data_type import (
    Vertex,
    DirectedMultiEdge,
    Group,
    GroupElement,
    GainFunction,
)


def switching_operation(
    gain_graph: GainGraphBase,
    v: Vertex,
    element: GroupElement,
    gain_function: GainFunction = None,
    group: Group = None,
) -> None:
    """
    Perform a switching operation on a gain function.

    Definitions
    -----------
     * :prf:ref:`Switching operation <def-switching-operation>`

    Parameters
    ----------
    v:
        The vertex at which to perform the operation.
    element:
        The element of the group with which to perform the operation.
    gain_function:
        The gain function on which to perform the operation. If
        ``gain_function is None``, the gain function of the gain graph will be used.
    group:
        The group associated with the gain function. If ``group is None``, the group of
        the gain graph will be used.

    Examples
    --------
    >>> from sympy.combinatorics import free_group
    >>> S, a, b = free_group("a, b")
    >>> G = GainGraph(S)
    >>> G.add_edges([(1, 1, b), (1, 2, b), (3, 1, b), (2, 3, b)])
    [(1, 1, 0), (1, 2, 0), (3, 1, 0), (2, 3, 0)]
    >>> G.switching_operation(1, a)
    >>> G.gain_function
    {1: {1: {0: a*b*a**-1}, 2: {0: a*b}}, 3: {1: {0: b*a**-1}}, 2: {3: {0: b}}}

    >>> X, c, d = free_group("c, d")
    >>> gain_function = {1: {1: {0: c}, 2: {0: c}}, 3: {1: {0: c}}, 2: {3: {0: c}}}
    >>> G.switching_operation(1, d, gain_function, X)
    >>> gain_function
    {1: {1: {0: d*c*d**-1}, 2: {0: d*c}}, 3: {1: {0: c*d**-1}}, 2: {3: {0: c}}}
    """
    gain_graph._input_check_vertex(v)

    if group is None:
        group = gain_graph.group
    else:
        _input_check.group(group)
    gain_graph._input_check_group_element(element, group)

    if gain_function is None:
        gain_function = gain_graph._gain_function
    gain_graph._input_check_gain_function(group, gain_function)

    for successor in gain_graph.successors(v):
        for edge, gain in gain_function[v][successor].items():
            gain_function[v][successor][edge] = element * gain

    for predecessor in gain_graph.predecessors(v):
        for edge, gain in gain_function[predecessor][v].items():
            gain_function[predecessor][v][edge] = gain * element**-1


def equivalent_gain_function(  # noqa: C901
    gain_graph: GainGraphBase,
    forest: Container[DirectedMultiEdge],
    gain_function: GainFunction = None,
    group: Group = None,
) -> GainFunction:
    r"""
    Given a gain function, find an equivalent gain function with identity gain for each
    edge in a subforest of the graph.

    Since, by definition, a forest is undirected, "forest" in this case refers to a
    subgraph that forms a forest if edge directions are ignored.

    Definitions
    -----------
     * :prf:ref:`Equivalent gain function <def-switching-operation>`

    Parameters
    ----------
    forest:
        The subforest of the graph.
    gain_function:
        A gain function on the graph. If ``gain_function is None``, the gain function of
        the gain graph will be used.
    group:
        The group associated with the gain function. If ``gain_function is None``, the
        group of the gain graph will be used.

    Examples
    --------
    >>> from sympy.combinatorics import free_group
    >>> S, a, b = free_group("a, b")
    >>> G = GainGraph(S)
    >>> G.add_edges([(0, 1, a), (1, 2, b), (0, 2, a**2)])
    [(0, 1, 0), (1, 2, 0), (0, 2, 0)]
    >>> G.equivalent_gain_function([(1, 2, 0)])
    {0: {1: {0: a*b*a**-2}, 2: {0: <identity>}}, 1: {2: {0: <identity>}}}

    >>> X, c, d = free_group("c, d")
    >>> gain_function = {0: {1: {0: c}, 2: {0: c**2}}, 1: {2: {0: d}}}
    >>> G.equivalent_gain_function([(0, 1, 0)], gain_function, X)
    {0: {1: {0: <identity>}, 2: {0: c**2*d**-1*c**-1}}, 1: {2: {0: <identity>}}}
    """
    if gain_function is None:
        gain_function = gain_graph._gain_function

    if group is None:
        group = gain_graph.group
    else:
        _input_check.group(group)

    gain_graph._input_check_gain_function(group, gain_function)

    # Shallow copy the gain function
    copy = {}
    for u, neighbors in gain_function.items():
        copy[u] = {}
        for v, edges in neighbors.items():
            copy[u][v] = {}
            for key, value in edges.items():
                copy[u][v][key] = value
    gain_function = copy

    # Mark all vertices and edges in the forest
    forest_edges = {}
    for edge in forest:
        u, v, k = edge
        gain_graph._input_check_edge(u, v, k)
        edges_u = forest_edges.setdefault(u, {})
        edges_v = forest_edges.setdefault(v, {})
        if v in edges_u or u in edges_v:
            raise ValueError("The given forest has parallel edges.")
        edges_u[v] = edge
        edges_v[u] = edge

    # Check whether the forest is acyclic
    parents = {}
    for vertex in forest_edges:
        if vertex in parents:
            continue
        parents[vertex] = None
        children = [vertex]
        while len(children) > 0:
            vertex = children.pop()
            parent = parents[vertex]
            for child in forest_edges[vertex]:
                if child is parent:
                    continue
                if child in parents:
                    raise ValueError("The given forest has a cycle.")
                parents[child] = vertex
                children.append(child)

    # Instantiate the underlying undirected graph, with (u, v, k) as the key to preserve
    # the orientation of the gain function
    undirected = nx.MultiGraph()
    for u, v, k in gain_graph.edges(keys=True):
        undirected.add_edge(u, v, (u, v, k))

    # Iterate over the connected components of the graph
    seen = set()
    for vertex in gain_graph:
        if vertex in seen:
            continue

        # Search the component to construct a spanning tree T, prioritizing each tree in
        # the forest to ensure its inclusion in T, using a bucket queue
        inside_forest = {}
        outside_forest = {vertex: None}
        while True:
            if len(inside_forest) > 0:
                vertex, in_edge = inside_forest.popitem()
                if vertex in outside_forest:
                    outside_forest.pop(vertex)
            elif len(outside_forest) > 0:
                vertex, in_edge = outside_forest.popitem()
            else:
                break

            seen.add(vertex)

            forest_neighbors = forest_edges.get(vertex, {})
            for child, edges in undirected[vertex].items():
                if child in seen:
                    continue
                if child in forest_neighbors:
                    inside_forest[child] = forest_neighbors[child]
                else:
                    outside_forest[child] = next(iter(edges))

            # Perform a switching operation at each vertex with the gain of the (possibly
            # backward) edge from its parent
            if in_edge is not None:
                u, v, k = in_edge
                unsigned_gain = gain_function[u][v][k]
                gain = unsigned_gain if vertex == v else unsigned_gain**-1
                switching_operation(gain_graph, vertex, gain, gain_function, group)

    return gain_function
