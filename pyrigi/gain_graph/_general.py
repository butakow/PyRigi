"""
A module for general gain graph functionality.
"""

from pyrigi.gain_graph.base import GainGraphBase

from copy import deepcopy

from collections.abc import Container, Hashable, Sequence
from pyrigi.data_type import Vertex, DirectedMultiEdge, GroupElement


def update(
    gain_graph: GainGraphBase,
    edges: (
        GainGraphBase
        | Container[
            tuple[Vertex, Vertex, GroupElement]
            | tuple[Vertex, Vertex, GroupElement, Hashable]
            | tuple[Vertex, Vertex, GroupElement, Hashable, dict]
        ]
    ) = None,
    vertices: Container[Vertex | tuple[Vertex, dict]] = None,
) -> list[DirectedMultiEdge]:
    """
    Update the vertices, edges, and/or graph attributes of the gain graph.

    This method returns a list of the added and/or updated edges. If ``edges is None``
    and ``vertices is None``, this method will raise a :exc:`TypeError`.

    Parameters
    ----------
    edges:
        If this parameter is another gain graph, then its vertices, edges, and graph
        attributes will be used to update the gain graph, with all edges assigned new
        keys. Otherwise, this parameter can be any container accepted by
        :meth:`.add_edges`, and the list returned by this method will be in the iteration
        order of the container.
    vertices:
        Any container accepted by :meth:`.add_vertices`. If ``edges`` is a gain graph,
        then this parameter is ignored.

    Examples
    --------
    >>> from sympy.combinatorics import SymmetricGroup, CyclicGroup, Permutation
    >>> G = GainGraph(SymmetricGroup(3), {0: {1: {2: Permutation(0, 2)}}}, rank=0)
    >>> H = GainGraph(CyclicGroup(3), rank=1, file=2)
    >>> H.add_vertices([(0, {"secret": True}), 3])
    >>> H.add_edge(0, 1, Permutation(2), 2, a=3)
    (0, 1, 2)
    >>> G.new_edge_key(0, 1)
    1
    >>> G.update(H)
    [(0, 1, 1)]
    >>> (3 in G) and G.nodes[0]["secret"]
    True
    >>> G.graph
    {'rank': 1, 'file': 2}

    >>> edges = [(0, 3, Permutation(2)), (0, 1, Permutation(1, 2), 0, dict(a=1, b=2))]
    >>> G.update(edges, [(0, {"secret": False}), 4])
    [(0, 3, 0), (0, 1, 0)]
    >>> print(G.gain(0, 1, 0))
    (1 2)
    >>> G.edges[0, 1, 0]
    {'a': 1, 'b': 2}
    >>> (4 in G) and not G.nodes[0]["secret"]
    True
    """
    added = []
    if isinstance(edges, GainGraphBase):
        graph_vertices = edges.vertices
        graph_edges = edges.edges
        graph_attrs = edges.graph
        gain_function = edges._gain_function

        gain_graph.add_vertices(graph_vertices.data())
        gain_graph.graph.update(graph_attrs)
        return gain_graph.add_edges(
            (u, v, gain_function[u][v][k], None, d)
            for u, v, k, d in graph_edges.data(keys=True)
        )
    else:
        if (edges is None) and (vertices is None):
            raise TypeError("Nothing was given to update.")
        if edges is not None:
            added = gain_graph.add_edges(edges)
        if vertices is not None:
            gain_graph.add_vertices(vertices)
    return added


def copy(gain_graph: GainGraphBase) -> GainGraphBase:
    """
    Return a semi-shallow copy of the gain graph.

    Specifically, this method returns an otherwise deep copy of the gain graph that has
    shallow copies of the graph, vertex, and edge attribute dictionaries, and shares
    references for the vertices and edge keys with the original.

    Examples
    --------
    >>> from sympy.combinatorics import SymmetricGroup, Permutation
    >>> G = GainGraph(SymmetricGroup(4), {0: {1: {2: Permutation(3)}}}, firsts=["Alice"])
    >>> print(G)
    GainGraph with vertices [0, 1] and gains {(0, 1, 2): (3)}
    >>> H = G.copy()
    >>> print(H)
    GainGraph with vertices [0, 1] and gains {(0, 1, 2): (3)}
    >>> H.graph["firsts"].append("Bob")
    >>> H.graph["lasts"] = ["Smith"]
    >>> G.graph, H.graph
    ({'firsts': ['Alice', 'Bob']}, {'firsts': ['Alice', 'Bob'], 'lasts': ['Smith']})
    """
    memo = {}
    memo[id(gain_graph.graph)] = gain_graph.graph.copy()
    for v, d in gain_graph.vertices(data=True):
        memo[id(v)] = v
        memo[id(d)] = d.copy()
    for u, v, k, d in gain_graph.edges.data(keys=True):
        memo[id(u)] = u
        memo[id(v)] = v
        memo[id(k)] = k
        memo[id(d)] = d.copy()
    graph = deepcopy(gain_graph, memo)
    return graph


def reverse(gain_graph: GainGraphBase) -> GainGraphBase:
    """
    Return a semi-deep copy of the gain graph with its edge directions reversed.

    Specifically, this method creates an otherwise deep copy of the gain graph that
    shares references for the vertices and edge keys with the original, and reverses its
    edge directions.

    Examples
    --------
    >>> from sympy.combinatorics import SymmetricGroup, Permutation
    >>> G = GainGraph(SymmetricGroup(4), {0: {1: {2: Permutation(3)}}}, names=["Alice"])
    >>> print(G)
    GainGraph with vertices [0, 1] and gains {(0, 1, 2): (3)}
    >>> H = G.reverse()
    >>> print(H)
    GainGraph with vertices [0, 1] and gains {(1, 0, 2): (3)}
    >>> H.graph["names"].append("Bob")
    >>> G.graph["names"], H.graph["names"]
    (['Alice'], ['Alice', 'Bob'])
    """
    memo = {}
    for v in gain_graph.vertices:
        memo[id(v)] = v
    for u, v, k in gain_graph.edges(keys=True):
        memo[id(u)] = u
        memo[id(v)] = v
        memo[id(k)] = k
    graph = deepcopy(gain_graph, memo)
    reversed_edges = []
    for u, v, k, d in graph.edges.data(keys=True):
        reversed_edges.append((v, u, graph._gain_function[u][v][k], k, d))
    graph.clear_edges()
    graph.add_edges(reversed_edges)
    return graph


def walk_gain(
    gain_graph: GainGraphBase, walk: Sequence[tuple[DirectedMultiEdge, bool]]
) -> GroupElement:
    """
    Compute the gain of a walk in the graph.

    Parameters
    ----------
    walk:
        A sequence of pairs ``(edge, forward)`` where ``edge`` is an edge in the graph
        and ``forward`` is a Boolean such that reversing the edges with
        ``forward = False`` makes the sequence of edges a walk in the graph.

    Examples
    --------
    >>> from sympy.combinatorics import free_group
    >>> S, a, b = free_group("a, b")
    >>> G = GainGraph(S)
    >>> edges = G.add_edges([(1, 3, a**0), (3, 4, b**-1), (4, 5, a**3), (1, 5, b**2)])
    >>> G.walk_gain(zip(edges, [True, True, True, False]))
    b**-1*a**3*b**-2
    """
    result = gain_graph.group.identity
    prev_tail = None
    for (u, v, k), forward in walk:
        gain_graph._input_check_edge(u, v, k)
        elt_gain = gain_graph._gain_function[u][v][k]
        if forward:
            head, tail = u, v
            result *= elt_gain
        else:
            head, tail = v, u
            result *= elt_gain**-1
        if (prev_tail is not None) and (prev_tail != head):
            raise ValueError("The given sequence of edges is not a walk.")
        prev_tail = tail
    return result
