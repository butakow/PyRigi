"""

Module for defining data type used for type hinting.

"""

from collections.abc import Sequence
from typing import Hashable, TypeAlias

import sympy as sp
from sympy.combinatorics import PermutationGroup, Permutation
from sympy.combinatorics.free_groups import FreeGroup, FreeGroupElement
from sympy.combinatorics.fp_groups import FpGroup

Vertex: TypeAlias = Hashable
"""
Any hashable type can be used for a :obj:`pyrigi.data_type.Vertex`.
"""

Edge: TypeAlias = set[Vertex] | tuple[Vertex, Vertex] | list[Vertex]
"""
An unordered pair of :obj:`Vertices <pyrigi.data_type.Vertex>`.
"""

DirectedEdge: TypeAlias = tuple[Vertex, Vertex] | list[Vertex]
"""
An ordered pair of :obj:`Vertices <pyrigi.data_type.Vertex>`.
"""

DirectedMultiEdge: TypeAlias = tuple[Vertex, Vertex, Hashable] | list[Vertex | Hashable]
"""
An ordered triple composed of two :obj:`Vertices <pyrigi.data_type.Vertex>` followed by
a hashable key used to distinguish multi-edges.
"""

Number: TypeAlias = int | float | str
"""
An integer, float or a string interpretable by :func:`~sympy.core.sympify.sympify`.
"""

Point: TypeAlias = Sequence[Number]
"""
A :obj:`~collections.abc.Sequence` of :obj:`Numbers <pyrigi.data_type.Number>`
whose length is the dimension of its affine space.
"""

InfFlex: TypeAlias = Sequence[Number] | dict[Vertex, Sequence[Number]]
"""
Given a framework in dimension ``dim`` with ``n`` vertices,
an infinitesimal flex is either given by a :obj:`~collections.abc.Sequence`
of :obj:`Numbers <pyrigi.data_type.Number>`
whose length is ``dim*n`` or by a dictionary from the set of vertices
to a :obj:`~collections.abc.Sequence` of :obj:`Numbers <pyrigi.data_type.Number>`
of length ``dim``.
"""

Stress: TypeAlias = Sequence[Number] | dict[Edge, Number]
"""
Given a framework with ``m`` edges, an equilibrium stress is either
given by a :obj:`~collections.abc.Sequence` of :obj:`Numbers <pyrigi.data_type.Number>`
whose length is ``m`` or by a dictionary from the set of edges
to a :obj:`~collections.abc.Sequence` of :obj:`Numbers <pyrigi.data_type.Number>`.
"""

Inf: TypeAlias = sp.core.numbers.Infinity
"""
Provides a data type that can become infinite.
"""

Group: TypeAlias = PermutationGroup | FreeGroup | FpGroup
"""
A finitely presented group, represented as a
:class:`~sympy.combinatorics.perm_groups.PermutationGroup` or
:external+sympy:doc:`FreeGroup or FpGroup <modules/combinatorics/fp_groups>`.
"""

GroupElement: TypeAlias = Permutation | FreeGroupElement
r"""
A :class:`~sympy.combinatorics.permutations.Permutation` or a
:external+sympy:doc:`FreeGroupElement <modules/combinatorics/fp_groups>`.
"""

GainFunction: TypeAlias = dict[Vertex, dict[Vertex, dict[Hashable, GroupElement]]]
"""
Given a directed multigraph and :obj:`~pyrigi.data_type.Group`, a gain function ``F`` is
a dict-of-dict-of-dict that associates each :obj:`~pyrigi.data_type.DirectedMultiEdge`
``(u, v, k)`` in the graph with ``F[u][v][k]``, an element of the group.
"""
