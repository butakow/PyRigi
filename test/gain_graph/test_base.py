import pytest

from pyrigi.gain_graph.base import GainGraphBase

from sympy.combinatorics import Permutation
from sympy.combinatorics.named_groups import DihedralGroup

from copy import deepcopy


def test_GainGraphBase_attr():
    gain_graph = GainGraphBase(DihedralGroup(4), first="Jeff", last="Graphington")
    assert gain_graph.graph == {"first": "Jeff", "last": "Graphington"}


def test_GainGraphBase_error():
    with pytest.raises(TypeError):
        GainGraphBase()
    with pytest.raises(TypeError):
        GainGraphBase(0)


def test___deepcopy__():

    class MutableHashable:
        def __init__(self):
            self.hash = id(self)
            self.list = []

        def __eq__(self, other):
            return self.hash == other.hash

        def __hash__(self):
            return self.hash

    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G, shared=[0])
    u, v, k = gain_graph.add_edge(
        MutableHashable(), MutableHashable(), G.identity, MutableHashable(), shared=[0]
    )
    gain_graph.add_vertex(u, shared=[0])

    copy = deepcopy(gain_graph)
    assert copy.__class__ == GainGraphBase

    assert copy.group.equals(G)

    # vertices and edge keys are deep copied
    u_c, v_c, k_c = next(iter(copy.edges))
    u_c.list.append(1)
    v_c.list.append(1)
    k_c.list.append(1)
    assert u.list == []
    assert v.list == []
    assert k.list == []

    # gain function is deep copied
    assert copy.gain_function == {u: {v: {k: G.identity}}}
    assert copy._gain_function[u][v] is not gain_graph._gain_function[u][v]

    # graph, vertex, and edge attrs are deep copied
    assert gain_graph.graph == copy.graph
    assert gain_graph.vertices(data=True) == copy.vertices(data=True)
    assert list(copy.edges.data(keys=True)) == [(u, v, k, {"shared": [0]})]
    copy.graph["shared"].append(1)
    copy.vertices[u]["shared"].append(1)
    copy[u][v][k]["shared"].append(1)
    assert gain_graph.graph == {"shared": [0]}
    assert dict(gain_graph.vertices(data=True)) == {u: {"shared": [0]}, v: {}}
    assert list(gain_graph.edges.data(keys=True)) == [(u, v, k, {"shared": [0]})]


def test___deepcopy___memo():
    D3, D4 = DihedralGroup(3), DihedralGroup(4)
    gain_graph = GainGraphBase(D4, pointer=D4)
    copy = deepcopy(gain_graph, {id(D4): D3})
    assert copy.group.equals(D3)
    assert copy.graph == {"pointer": D3}
    assert copy.graph["pointer"] is D3


def test___str__():
    gain_graph = GainGraphBase(DihedralGroup(4))
    gain_graph.add_edges(
        [(1, 0, Permutation(3), 2), ("b", "a", Permutation(0, 3)(1, 2), "c")]
    )
    gain_graph.add_vertices(["b", "a"])
    assert str(gain_graph) == (
        "GainGraphBase with vertices [1, 0, 'b', 'a'] and gains "
        "{(1, 0, 2): (3), ('b', 'a', 'c'): (0 3)(1 2)}"
    )


def test__input_check_group_element():
    D3, D4 = DihedralGroup(3), DihedralGroup(4)
    gain_graph = GainGraphBase(D3)

    gain_graph._input_check_group_element(D3.identity)

    four_cycle = Permutation(0, 1, 2, 3)
    gain_graph._input_check_group_element(four_cycle, D4)
    with pytest.raises(ValueError):
        gain_graph._input_check_group_element(four_cycle)

    with pytest.raises(ValueError):
        gain_graph._input_check_group_element(None)


def test__input_check_gain_function():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edge(0, 0, G.identity, 1)
    gain_function = gain_graph.gain_function

    gain_graph._input_check_gain_function(G, gain_function)

    with pytest.raises(TypeError):
        gain_graph._input_check_gain_function(G, 0)

    # gain function edge not in graph
    gain_function[0][1] = {0: Permutation(0, 1, 2, 3)}
    with pytest.raises(ValueError):
        gain_graph._input_check_gain_function(G, gain_function)
    del gain_function[0][1]
    gain_graph._input_check_gain_function(G, gain_function)

    # graph edge not in gain function
    del gain_function[0][0][1]
    with pytest.raises(ValueError):
        gain_graph._input_check_gain_function(G, gain_function)
    gain_function[0][0][1] = G.identity
    gain_graph._input_check_gain_function(G, gain_function)


def test__input_check_gain_function_add_missing():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edge(0, 0, G.identity, 1)
    gain_function = gain_graph.gain_function
    four_cycle = Permutation(0, 1, 2, 3)
    gain_function[0][1] = {0: four_cycle}
    gain_graph._input_check_gain_function(G, gain_function, add_missing=True)
    assert gain_graph.gain_function == {0: {0: {1: G.identity}, 1: {0: four_cycle}}}


def test__input_check_edge():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edge(0, 1, G.identity, 2)
    gain_graph._input_check_edge(0, 1, 2)
    with pytest.raises(ValueError):
        gain_graph._input_check_edge(0, 1, 3)


def test__input_check_vertex():
    gain_graph = GainGraphBase(DihedralGroup(4))
    gain_graph.add_vertex(0)
    gain_graph._input_check_vertex(0)
    with pytest.raises(ValueError):
        gain_graph._input_check_vertex(1)


def test_group():
    D3, D4 = DihedralGroup(3), DihedralGroup(4)
    gain_graph = GainGraphBase(D4)
    gain_graph.group = D3
    assert gain_graph.group is D3


def test_gain_function():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edge(0, 1, G.identity, 2)
    gain_function = gain_graph.gain_function
    assert gain_function == {0: {1: {2: G.identity}}}
    assert gain_function[0][1] is not gain_graph._gain_function[0][1]


def test_gain():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    ident = G.identity
    gain_graph.add_edge(0, 1, ident, 2)
    gain = gain_graph.gain(0, 1, 2)
    assert gain is ident


def test_set_gain():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edge(0, 1, G.identity, 2)
    four_cycle = Permutation(0, 1, 2, 3)
    gain_graph.set_gain(0, 1, 2, four_cycle)
    assert gain_graph.gain_function == {0: {1: {2: four_cycle}}}


def test_set_gain_function():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edge(0, 1, G.identity, 2)
    four_cycle = Permutation(0, 1, 2, 3)
    gain_graph.set_gain_function({0: {1: {2: four_cycle}}})
    assert gain_graph.gain_function == {0: {1: {2: four_cycle}}}


def test_set_gain_function_group():
    D3, D4 = DihedralGroup(3), DihedralGroup(4)
    gain_graph = GainGraphBase(D3)
    three_cycle = Permutation(0, 1, 2)
    gain_graph.add_edge(0, 1, three_cycle, 2)
    gain_graph.set_gain_function({0: {1: {2: D4.identity}}}, D4)
    assert gain_graph.group is D4
    assert gain_graph.gain_function == {0: {1: {2: D4.identity}}}


def test_add_vertex():
    gain_graph = GainGraphBase(DihedralGroup(4))
    gain_graph.add_vertex(0)
    assert list(gain_graph.vertices) == [0]


def test_add_vertex_attr():
    gain_graph = GainGraphBase(DihedralGroup(4))
    gain_graph.add_vertex(0, fun=True)
    assert dict(gain_graph.vertices(data=True)) == {0: {"fun": True}}
    gain_graph.add_vertex(0, fun=False, difficult=True)
    assert dict(gain_graph.vertices(data=True)) == {
        0: {"fun": False, "difficult": True}
    }


def test_add_vertices():
    gain_graph = GainGraphBase(DihedralGroup(4))
    gain_graph.add_vertices([0, (1, {"label": "old"})])
    gain_graph.add_vertices([(1, {"label": "new"})])
    assert dict(gain_graph.vertices(data=True)) == {0: {}, 1: {"label": "new"}}


def test_add_vertices_attr():
    gain_graph = GainGraphBase(DihedralGroup(4))
    gain_graph.add_vertices([0, (1, {"speed": 80})], speed=75, mass=1000)
    gain_graph.add_vertices([0], mass=2000)
    assert dict(gain_graph.vertices(data=True)) == {
        0: {"speed": 75, "mass": 2000},
        1: {"speed": 80, "mass": 1000},
    }


def test_add_nodes_from():
    gain_graph = GainGraphBase(DihedralGroup(4))
    gain_graph.add_nodes_from([0, (1, {"label": "old"})])
    gain_graph.add_nodes_from([(1, {"label": "new"})])
    assert dict(gain_graph.vertices(data=True)) == {0: {}, 1: {"label": "new"}}


def test_delete_vertex():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edges([(0, 1, G.identity), (1, 0, G.identity)])
    gain_graph.delete_vertex(0)
    assert gain_graph.gain_function == {1: {}}


def test_remove_node():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edges([(0, 1, G.identity), (1, 0, G.identity)])
    gain_graph.remove_node(0)
    assert list(gain_graph.edges) == []


def test_delete_vertices():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edges(
        [
            (0, 1, G.identity),
            (1, 0, G.identity),
        ]
    )
    gain_graph.delete_vertices([0, 2])
    assert gain_graph.gain_function == {1: {}}


def test_remove_nodes_from():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_vertices([0, 1])
    gain_graph.remove_nodes_from([0, 2])
    assert list(gain_graph.vertices) == [1]


def test_add_edge():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    u, v, k = gain_graph.add_edge(0, 1, G.identity)
    assert gain_graph.gain_function == {u: {v: {k: G.identity}}}


def test_add_edge_key():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edge(0, 1, G.identity, 2)
    assert gain_graph.gain_function == {0: {1: {2: G.identity}}}

    four_cycle = Permutation(0, 1, 2, 3)
    gain_graph.add_edge(0, 1, four_cycle, 2)
    assert gain_graph.gain_function == {0: {1: {2: four_cycle}}}


def test_add_edge_attr():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edge(0, 1, G.identity, 2, a=2)
    assert list(gain_graph.edges.data(keys=True)) == [(0, 1, 2, {"a": 2})]

    four_cycle = Permutation(0, 1, 2, 3)
    gain_graph.add_edge(0, 1, four_cycle, 2, a=1, b=2)
    assert list(gain_graph.edges.data(keys=True)) == [(0, 1, 2, {"a": 1, "b": 2})]


def test_add_edges():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    elements = G.elements
    added = gain_graph.add_edges(
        [
            (0, 1, elements[0]),
            (1, 2, elements[1], 2),
            (2, 0, elements[2], None, {"label": "abc"}),
            (0, 3, elements[3], 4, {"label": "old"}),
        ]
    )
    assert added == [(0, 1, 0), (1, 2, 2), (2, 0, 0), (0, 3, 4)]

    gain_graph.add_edges([(1, 2, elements[4], 2, {"label": "new"})])
    assert gain_graph.gain_function == {
        0: {1: {0: elements[0]}, 3: {4: elements[3]}},
        1: {2: {2: elements[4]}},
        2: {0: {0: elements[2]}},
    }
    assert list(gain_graph.edges.data(keys=True)) == [
        (0, 1, 0, {}),
        (0, 3, 4, {"label": "old"}),
        (1, 2, 2, {"label": "new"}),
        (2, 0, 0, {"label": "abc"}),
    ]


def test_add_edges_attr():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    four_cycle = Permutation(0, 1, 2, 3)
    gain_graph.add_edges(
        [(0, 1, G.identity, 2, {"w_1": 1}), (3, 4, four_cycle, 5)], w_1=2, w_2=2
    )
    gain_graph.add_edges([(3, 4, four_cycle, 5)], w_2=3)
    assert list(gain_graph.edges.data(keys=True)) == [
        (0, 1, 2, {"w_1": 1, "w_2": 2}),
        (3, 4, 5, {"w_1": 2, "w_2": 3}),
    ]


def test_add_edges_error():
    gain_graph = GainGraphBase(DihedralGroup(4))
    with pytest.raises(TypeError):
        gain_graph.add_edges([(0, 1)])


def test_add_edges_from():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    elements = G.elements
    added = gain_graph.add_edges_from(
        [
            (0, 1, elements[0]),
            (1, 2, elements[1], 2),
            (2, 0, elements[2], None, {"label": "abc"}),
            (0, 3, elements[3], 4, {"label": "old"}),
        ]
    )
    assert added == [(0, 1, 0), (1, 2, 2), (2, 0, 0), (0, 3, 4)]
    assert gain_graph.gain_function == {
        0: {1: {0: elements[0]}, 3: {4: elements[3]}},
        1: {2: {2: elements[1]}},
        2: {0: {0: elements[2]}},
    }


def test_add_weighted_edges():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    four_cycle = Permutation(0, 1, 2, 3)
    added = gain_graph.add_weighted_edges(
        [(0, 1, G.identity, 2), (1, 2, four_cycle, 3)]
    )
    assert added == [(0, 1, 0), (1, 2, 0)]
    assert list(gain_graph.edges.data(keys=True)) == [
        (0, 1, 0, {"weight": 2}),
        (1, 2, 0, {"weight": 3}),
    ]


def test_add_weighted_edges_weight():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    [edge] = gain_graph.add_weighted_edges([(0, 1, G.identity, 2)], weight="mass")
    assert list(gain_graph.edges.data(keys=True)) == [(*edge, {"mass": 2})]


def test_add_weighted_edges_attr():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    [edge] = gain_graph.add_weighted_edges([(0, 1, G.identity, 2)], label="abc")
    assert list(gain_graph.edges.data(keys=True)) == [
        (*edge, {"weight": 2, "label": "abc"})
    ]


def test_add_weighted_edges_from():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    four_cycle = Permutation(0, 1, 2, 3)
    added = gain_graph.add_weighted_edges_from(
        [(0, 1, G.identity, 2), (1, 2, four_cycle, 3)]
    )
    assert added == [(0, 1, 0), (1, 2, 0)]
    assert list(gain_graph.edges.data(keys=True)) == [
        (0, 1, 0, {"weight": 2}),
        (1, 2, 0, {"weight": 3}),
    ]


def test_delete_edge():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edge(0, 1, G.identity, 2)
    gain_graph.delete_edge(0, 1, 2)
    assert gain_graph.gain_function == {0: {1: {}}}


def test_remove_edge():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    gain_graph.add_edge(0, 1, G.identity, 2)
    gain_graph.remove_edge(0, 1, 2)
    assert gain_graph.gain_function == {0: {1: {}}}


def test_delete_edges():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    four_cycle = Permutation(0, 1, 2, 3)
    gain_graph.add_edges(
        [
            (0, 1, G.identity, 2),
            (1, 0, four_cycle, 3),
        ]
    )
    gain_graph.delete_edges([(0, 1, 2), (3, 4, 5)])
    assert gain_graph.gain_function == {0: {1: {}}, 1: {0: {3: four_cycle}}}


def test_remove_edges_from():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G)
    four_cycle = Permutation(0, 1, 2, 3)
    gain_graph.add_edges(
        [
            (0, 1, G.identity, 2),
            (1, 0, four_cycle, 3),
        ]
    )
    gain_graph.remove_edges_from([(0, 1, 2), (3, 4, 5)])
    assert gain_graph.gain_function == {0: {1: {}}, 1: {0: {3: four_cycle}}}


def test_clear():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G, label="abc")
    gain_graph.add_edge(0, 1, G.identity, 2)
    gain_graph.clear()
    assert gain_graph.gain_function == {}
    assert list(gain_graph.vertices) == []
    assert gain_graph.graph == {}


def test_clear_edges():
    G = DihedralGroup(4)
    gain_graph = GainGraphBase(G, label="abc")
    gain_graph.add_edge(0, 1, G.identity, 2)
    gain_graph.clear_edges()
    assert gain_graph.gain_function == {}
    assert list(gain_graph.vertices) == [0, 1]
    assert gain_graph.graph == {"label": "abc"}
