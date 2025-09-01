import pytest

from pyrigi.gain_graph.base import GainGraphBase
from pyrigi.gain_graph import _general as general

from sympy.combinatorics import Permutation
from sympy.combinatorics.named_groups import DihedralGroup
from sympy.combinatorics.free_groups import free_group


def test_update_graph():
    G_1 = DihedralGroup(4)
    gain_graph_1 = GainGraphBase(G_1)
    gain_graph_1.add_edge(0, 1, G_1.identity, 2)

    G_2 = DihedralGroup(4)
    gain_graph_2 = GainGraphBase(G_2, label="abc")
    four_cycle = Permutation(0, 1, 2, 3)
    gain_graph_2.add_vertices([(0, {"label": "def"}), 2])
    gain_graph_2.add_edge(0, 1, four_cycle, 2)

    [(_, _, key)] = general.update(gain_graph_1, gain_graph_2, vertices=["ignored"])
    assert gain_graph_1.graph == {"label": "abc"}
    assert dict(gain_graph_1.vertices(data=True)) == {0: {"label": "def"}, 1: {}, 2: {}}
    assert gain_graph_1.gain_function == {0: {1: {2: G_1.identity, key: four_cycle}}}


def test_update_edges():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edge(0, 1, G.identity, 2)
    four_cycle = Permutation(0, 1, 2, 3)
    added = general.update(
        gain_graph, [(0, 1, four_cycle, 2, {"label": "abc"}), (1, 2, G.identity)], [3]
    )
    assert added == [(0, 1, 2), (1, 2, 0)]
    assert gain_graph.gain_function == {
        0: {1: {2: four_cycle}},
        1: {2: {0: G.identity}},
    }
    assert list(gain_graph.edges.data(keys=True)) == [
        (0, 1, 2, {"label": "abc"}),
        (1, 2, 0, {}),
    ]
    assert list(gain_graph.vertices) == [0, 1, 2, 3]


def test_update_vertices():
    gain_graph = GainGraphBase(DihedralGroup(4))
    gain_graph.add_vertex(0, label="old")
    general.update(gain_graph, vertices=[(0, {"label": "new"}), 1])
    assert dict(gain_graph.vertices(data=True)) == {0: {"label": "new"}, 1: {}}


def test_update_error():
    gain_graph = GainGraphBase(DihedralGroup(4))
    with pytest.raises(TypeError):
        general.update(gain_graph)

    with pytest.raises(TypeError):
        general.update(gain_graph, vertices=[[]])


def test_copy():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G, shared=[0])
    gain_graph.add_vertex(0, shared=[0])
    gain_graph.add_edge(0, 1, G.identity, 2, shared=[0])

    # ensure vertex and edge keys are shared
    h_1, h_2, h_3 = object(), object(), object()
    four_cycle = Permutation(0, 1, 2, 3)
    gain_graph.add_edge(h_1, h_2, four_cycle, h_3)

    copy = general.copy(gain_graph)
    assert copy.__class__ == GainGraphBase

    assert copy.group.equals(G)

    # gain function is deep copied
    assert copy.gain_function == {
        0: {1: {2: G.identity}},
        h_1: {h_2: {h_3: four_cycle}},
    }
    assert copy._gain_function[0][1] is not gain_graph._gain_function[0][1]
    assert copy._gain_function[h_1][h_2] is not gain_graph._gain_function[h_1][h_2]

    # graph, vertex, and edge attrs are shallow copied
    assert gain_graph.graph == copy.graph
    assert gain_graph.graph is not copy.graph
    assert gain_graph.vertices(data=True) == copy.vertices(data=True)
    assert list(gain_graph.edges.data(keys=True)) == list(copy.edges.data(keys=True))
    copy.graph["shared"].append(1)
    copy.vertices[0]["shared"].append(1)
    copy.vertices[0]["unshared"] = 2
    copy[0][1][2]["shared"].append(1)
    copy[0][1][2]["unshared"] = 2
    assert gain_graph.graph == {"shared": [0, 1]}
    assert dict(gain_graph.vertices(data=True)) == {
        0: {"shared": [0, 1]},
        1: {},
        h_1: {},
        h_2: {},
    }
    assert list(gain_graph.edges.data(keys=True)) == [
        (0, 1, 2, {"shared": [0, 1]}),
        (h_1, h_2, h_3, {}),
    ]


def test_reverse():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G, shared=[0])
    gain_graph.add_vertex(0, shared=[0])
    four_cycle = Permutation(0, 1, 2, 3)
    gain_graph.add_edge(0, 1, G.identity, 2, shared=[0])
    gain_graph.add_edge(1, 0, four_cycle, 2)

    # ensure vertex and edge keys are shared
    h_1, h_2, h_3 = object(), object(), object()
    reflection = Permutation(0, 3)(1, 2)
    gain_graph.add_edge(h_1, h_2, reflection, h_3)

    reverse = general.reverse(gain_graph)
    assert reverse.__class__ == GainGraphBase

    assert reverse.group.equals(G)

    # gain function is deep copied
    assert reverse.gain_function == {
        0: {1: {2: four_cycle}},
        1: {0: {2: G.identity}},
        h_2: {h_1: {h_3: reflection}},
    }
    assert gain_graph._gain_function[0][1] is not reverse._gain_function[1][0]
    assert gain_graph._gain_function[1][0] is not reverse._gain_function[0][1]
    assert gain_graph._gain_function[h_1][h_2] is not reverse._gain_function[h_2][h_1]

    # graph, vertex, and edge attrs are deep copied
    assert gain_graph.graph == reverse.graph
    assert gain_graph.vertices(data=True) == reverse.vertices(data=True)
    assert list(reverse.edges.data(keys=True)) == [
        (0, 1, 2, {}),
        (1, 0, 2, {"shared": [0]}),
        (h_2, h_1, h_3, {}),
    ]
    reverse.graph["shared"].append(1)
    reverse.vertices[0]["shared"].append(1)
    reverse[1][0][2]["shared"].append(1)
    assert gain_graph.graph == {"shared": [0]}
    assert dict(gain_graph.vertices(data=True)) == {
        0: {"shared": [0]},
        1: {},
        h_1: {},
        h_2: {},
    }
    assert list(gain_graph.edges.data(keys=True)) == [
        (0, 1, 2, {"shared": [0]}),
        (1, 0, 2, {}),
        (h_1, h_2, h_3, {}),
    ]


def test_walk_gain():
    S, a, b = free_group("a, b")
    gain_graph = GainGraphBase(S)
    ident = S.identity
    edges = gain_graph.add_edges(
        [
            (2, 1, ident),
            (1, 3, ident),
            (2, 3, a),
            (1, 5, b**2),
            (3, 4, b**-1),
            (6, 2, ident),
            (4, 5, a**3),
            (4, 6, ident),
            (5, 6, a),
        ]
    )
    assert (
        general.walk_gain(
            gain_graph,
            [(edges[1], True), (edges[4], True), (edges[6], True), (edges[3], False)],
        )
        == b**-1 * a**3 * b**-2
    )


def test_walk_gain_error():
    S, a, b = free_group("a, b")
    gain_graph = GainGraphBase(S)
    ident = S.identity
    edges = gain_graph.add_edges(
        [
            (2, 1, ident),
            (1, 3, ident),
            (2, 3, a),
            (1, 5, b**2),
            (3, 4, b**-1),
            (6, 2, ident),
            (4, 5, a**3),
            (4, 6, ident),
            (5, 6, a),
        ]
    )
    with pytest.raises(ValueError):
        general.walk_gain(gain_graph, [(edges[0], True), (edges[1], False)])
