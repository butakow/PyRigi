import pytest

from pyrigi.gain_graph.base import GainGraphBase
from pyrigi.gain_graph._algorithms import switching

from sympy.combinatorics.free_groups import free_group


def test_switching_operation():
    S, a, b = free_group("a, b")
    gain_graph = GainGraphBase(S)
    gain_graph.add_edges([(1, 1, a), (1, 2, a**2), (3, 1, a**3), (2, 3, a**4)])
    switching.switching_operation(gain_graph, 1, b)
    assert gain_graph.gain_function == {
        1: {1: {0: b * a * b**-1}, 2: {0: b * a**2}},
        3: {1: {0: a**3 * b**-1}},
        2: {3: {0: a**4}},
    }


def test_switching_operation_gain_function():
    S, a, b = free_group("a, b")
    X, c, d = free_group("c, d")
    gain_graph = GainGraphBase(S)
    gain_graph.add_edges(
        [(1, 1, a, 0), (1, 2, a**2, 1), (3, 1, a**3, 2), (2, 3, a**4, 3)]
    )
    gain_function = {
        1: {1: {0: c**-1}, 2: {1: c**-2}},
        3: {1: {2: c**-3}},
        2: {3: {3: c**-4}},
    }
    switching.switching_operation(gain_graph, 1, d, gain_function, X)
    assert gain_function == {
        1: {1: {0: d * c**-1 * d**-1}, 2: {1: d * c**-2}},
        3: {1: {2: c**-3 * d**-1}},
        2: {3: {3: c**-4}},
    }


def test_equivalent_gain_function():
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
    forest = [edges[i - 1] for i in [2, 3, 5, 7, 8]]
    gain_function = switching.equivalent_gain_function(gain_graph, forest)
    for u, v, k in forest:
        assert gain_function[u][v][k] == ident

    # multiple trees
    forest = [edges[i - 1] for i in [2, 3, 7, 8]]
    gain_function = switching.equivalent_gain_function(gain_graph, forest)
    for u, v, k in forest:
        assert gain_function[u][v][k] == ident

    # disconnected graph, multi-edges, loops
    gain_graph = GainGraphBase(S)
    ident = S.identity
    edges = gain_graph.add_edges(
        [
            (0, 1, a),
            (1, 2, b),
            (2, 0, a * b * a),
            (3, 4, b**-1),
            (4, 5, a**-1),
            (5, 3, b * a * b),
            (5, 3, a**2 * b**2),
            (3, 5, b**3),
            (3, 3, a**2),
        ]
    )
    forest = [edges[i - 1] for i in [1, 2, 4, 7]]
    gain_function = switching.equivalent_gain_function(gain_graph, forest)
    for u, v, k in forest:
        assert gain_function[u][v][k] == ident


def test_equivalent_gain_function_gain_function():
    S, a, b = free_group("a, b")
    X, c, d = free_group("c, d")
    gain_graph = GainGraphBase(S)
    S_id = S.identity
    X_id = X.identity
    edges = gain_graph.add_edges(
        [
            (2, 1, S_id, 1),
            (1, 3, S_id, 2),
            (2, 3, a, 3),
            (1, 5, b**2, 4),
            (3, 4, b**-1, 5),
            (6, 2, S_id, 6),
            (4, 5, a**3, 7),
            (4, 6, S_id, 8),
            (5, 6, a, 9),
        ]
    )
    forest = [edges[i - 1] for i in [2, 3, 5, 7, 8]]
    gain_function = {
        2: {1: {1: X_id}, 3: {3: c}},
        1: {3: {2: d}, 5: {4: X_id}},
        3: {4: {5: c**2}},
        6: {2: {6: X_id}},
        4: {5: {7: d**2}, 6: {8: c * d}},
        5: {6: {9: X_id}},
    }
    equivalent = switching.equivalent_gain_function(
        gain_graph, forest, gain_function, X
    )
    for u, v, k in forest:
        assert equivalent[u][v][k] == X_id


def test_equivalent_gain_function_error():
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
            (5, 6, b),
        ]
    )
    forest = [edges[i - 1] for i in [1, 2, 3]]
    with pytest.raises(ValueError):
        switching.equivalent_gain_function(gain_graph, forest)

    with pytest.raises(ValueError):
        switching.equivalent_gain_function(gain_graph, [edges[-1], edges[-2]])
