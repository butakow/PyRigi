from pyrigi import GainGraph

from sympy.combinatorics.named_groups import DihedralGroup

from copy import deepcopy


def test___str__():
    gain_graph = GainGraph(DihedralGroup(4))
    assert str(gain_graph) == "GainGraph with vertices [] and gains {}"


def test___deepcopy__():
    gain_graph = GainGraph(DihedralGroup(4))
    copy = deepcopy(gain_graph)
    assert copy.__class__ == GainGraph


def test_copy():
    gain_graph = GainGraph(DihedralGroup(4))
    copy = gain_graph.copy()
    assert copy.__class__ == GainGraph


def test_reverse():
    gain_graph = GainGraph(DihedralGroup(4))
    copy = gain_graph.reverse()
    assert copy.__class__ == GainGraph
