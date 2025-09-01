"""
The base module for gain graphs.
"""

from __future__ import annotations

import networkx as nx

from copy import deepcopy
from sympy import Basic

from pyrigi._utils import _input_check
from pyrigi._utils._doc import doc_category, generate_category_tables
from pyrigi.graph import _general as graph_general

from typing import Any
from collections.abc import Container, Hashable
from pyrigi.data_type import (
    Vertex,
    DirectedMultiEdge,
    Group,
    GroupElement,
    GainFunction,
)


class GainGraphBase(nx.MultiDiGraph):
    """
    The base class for :class:`.GainGraph`.

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
    >>> G = GainGraphBase(CyclicGroup(4), {0: {1: {2: Permutation(0, 2)(1, 3)}}})
    >>> print(G)
    GainGraphBase with vertices [0, 1] and gains {(0, 1, 2): (0 2)(1 3)}

    >>> G = GainGraphBase(CyclicGroup(2), name="Michael")
    >>> G.add_vertices([0, 'a'])
    >>> G.add_edges([(0, 7, Permutation(1)), (0, 7, Permutation(0, 1))])
    [(0, 7, 0), (0, 7, 1)]
    >>> print(G)
    GainGraphBase with vertices [0, 'a', 7] and gains {(0, 7, 0): (1), (0, 7, 1): (0 1)}
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

    def __init__(
        self,
        group: Group = None,
        gain_function: GainFunction = None,
        incoming_graph_data: Any = None,
        multigraph_input: bool = None,
        **attr,
    ) -> None:
        """
        Initialize the gain graph.
        """
        if group is None:
            raise TypeError(
                (
                    "A group must be specified. This error may be reached by attempting "
                    "to create a NetworkX graph view of a gain graph, which is not "
                    "supported."
                )
            )
        _input_check.group(group)
        self._group = group

        if gain_function is None:
            gain_function = {}
        self._gain_function = gain_function

        super().__init__(incoming_graph_data, multigraph_input, **attr)

        self._input_check_gain_function(group, gain_function, add_missing=True)

    def __deepcopy__(self, memo: dict) -> GainGraphBase:
        """
        An implementation of :meth:`object.__deepcopy__` that manually instantiates the
        group's attributes if necessary.

        Parameters
        ----------
        memo:
            See :meth:`object.__deepcopy__`.

        Examples
        --------
        >>> from copy import deepcopy
        >>> from sympy.combinatorics import CyclicGroup, Permutation
        >>> G = GainGraph(CyclicGroup(4), {0: {1: {2: Permutation(3)}}}, names=["Alice"])
        >>> print(G)
        GainGraph with vertices [0, 1] and gains {(0, 1, 2): (3)}
        >>> H = deepcopy(G)
        >>> print(H)
        GainGraph with vertices [0, 1] and gains {(0, 1, 2): (3)}
        >>> H.graph["names"].append("Bob")
        >>> G.graph["names"], H.graph["names"]
        (['Alice'], ['Alice', 'Bob'])
        """
        group = self.group
        copy = self.__class__(group)  # distinguish between GainGraph and GainGraphBase
        # Since GainGraph does not accept list or dictionary items from the iterators
        # that a reductor could return, and has no __slots__, copy.deepcopy can be
        # reduced to this:
        copy.__dict__.update(deepcopy(self.__dict__, memo))
        if isinstance(group, Basic):
            copy.group.__init__()
        return copy

    def __str__(self) -> str:
        """
        Return a human-readable summary of the gain graph.
        """
        gain_gen = (f"{e}: {self.gain(*e)}" for e in self.edges(keys=True))
        return (
            f"{self.__class__.__name__} "  # distinguish GainGraph from GainGraphBase
            f"with vertices {graph_general.vertex_list(self)} and gains "
            f"{{{", ".join(gain_gen)}}}"
        )

    def _input_check_group_element(
        self, element: GroupElement, group: Group = None
    ) -> None:
        """
        Check whether an input parameter ``element`` is an element of a group and raise a
        :exc:`ValueError` otherwise.

        Parameters
        ----------
        element:
        group:
            A group. If ``group is None``, the group of the gain graph will be used.
        """
        if group is None:
            group = self.group
        try:
            if element not in group:
                raise ValueError(f"{element} is not in the group {group}.")
        except TypeError as err:
            raise ValueError(f"{element} is not in the group {group}.") from err

    def _input_check_gain_function(
        self, group: Group, gain_function: GainFunction, add_missing: bool = False
    ) -> None:
        """
        Check whether an input parameter ``gain_function`` is a gain function on the
        graph with the input parameter ``group`` as its codomain and raise an exception
        otherwise.

        If ``gain_function`` is not a dict-of-dict-of-dict, this method will raise a
        :exc:`TypeError`. If ``gain_function[u][v][k] not in group`` holds for some
        ``u``, ``v``, and ``k``, or if the condition ``k in gain_function[u][v]`` does
        not hold if the graph has an edge from ``u`` to ``v`` with key ``k``, this method
        will raise a :exc:`ValueError`.

        Parameters
        ----------
        group:
        gain_function:
        add_missing:
            If ``add_missing = True``, then edges in the domain of the gain function will
            be added to the graph if they are absent. Otherwise, if an edge in the domain
            of the gain function is not in the graph, this method will raise a
            :exc:`ValueError`.
        """
        edge_set = set(self.edges(keys=True))

        try:
            for u, neighbors in gain_function.items():
                for v, edges in neighbors.items():
                    for key, value in edges.items():
                        self._input_check_group_element(value, group)
                        edge = (u, v, key)
                        try:
                            edge_set.remove(edge)
                        except KeyError as err:
                            if not add_missing:
                                raise ValueError(
                                    (
                                        f"{edge} is in the domain of the gain function "
                                        "but not the graph."
                                    )
                                ) from err
                            else:
                                self.add_edge(u, v, value, key)
        except AttributeError as err:
            raise TypeError(
                "The gain function does not have dict-of-dict-of-dict structure."
            ) from err

        if len(edge_set) > 0:
            raise ValueError(
                "Not all edges in the graph are in the domain of the gain function."
            )

    def _input_check_edge(self, u: Vertex, v: Vertex, key: Hashable) -> None:
        """
        Check whether a potential edge is in the gain graph, and raise a
        :exc:`ValueError` otherwise.

        Parameters
        ----------
        u:
            The head of the potential edge.
        v:
            The tail of the potential edge.
        key:
            The key used to distinguish multi-edges.
        """
        if not self.has_edge(u, v, key):
            raise ValueError(f"{(u, v, key)} is not an edge in the graph.")

    def _input_check_vertex(self, vertex: Vertex) -> None:
        """
        Check whether a potential vertex is in the graph and raise a :exc:`ValueError`
        otherwise.

        Parameters
        ----------
        vertex:
            The potential vertex.
        """
        if vertex not in self:
            raise ValueError(f"{vertex} is not a vertex in the graph.")

    # The type hints for the group and gain_function properties are displayed as
    # unrendered RST since they are substituted as such by autodoc_type_aliases.
    # It seems like this issue is avoided for method return types since
    # autodoc_typehints == "description", but there does not appear to be an equivalent
    # option to render properties' type hints outside their "signatures". The current
    # autodoc_type_aliases substitution may not be needed at all once the fix for this
    # issue is released: https://github.com/sphinx-doc/sphinx/issues/10785

    @property
    def group(self) -> Group:
        """
        Return the group.

        Examples
        --------
        >>> from sympy.combinatorics import free_group
        >>> S, a, b = free_group("a, b")
        >>> G = GainGraph(S)
        >>> G.group
        <free group on the generators (a, b)>
        """
        return self._group

    @group.setter
    def group(self, value: Group) -> None:
        """
        Set the group to a supported group compatible with the gain function.
        """
        _input_check.group(value)
        self._input_check_gain_function(value, self._gain_function)
        self._group = value

    @property
    def gain_function(self) -> GainFunction:
        """
        Return a shallow copy of the gain function.

        Examples
        --------
        >>> from sympy.combinatorics import DihedralGroup, Permutation
        >>> G = GainGraph(DihedralGroup(4))
        >>> G.add_edge(0, 1, Permutation(0, 3)(1, 2))
        (0, 1, 0)
        >>> G.gain_function
        {0: {1: {0: Permutation(0, 3)(1, 2)}}}
        """
        result = {}
        for u, neighbors in self._gain_function.items():
            result[u] = {}
            for v, edges in neighbors.items():
                result[u][v] = {}
                for key, value in edges.items():
                    result[u][v][key] = value
        return result

    @property
    def vertices(self) -> nx.reportviews.NodeView:
        """
        Alias for :attr:`networkx.MultiDiGraph.nodes`.
        """
        return self.nodes

    @doc_category("Attribute getters")
    def gain(self, u: Vertex, v: Vertex, key: Hashable) -> GroupElement:
        """
        Return the gain of an edge in the graph.

        Parameters
        ----------
        u:
            The head of the edge.
        v:
            The tail of the edge.
        key:
            The key used to distinguish multi-edges.

        Examples
        --------
        >>> from sympy.combinatorics import SymmetricGroup, Permutation
        >>> G = GainGraph(SymmetricGroup(3), {0: {1: {2: Permutation(1, 2)}}})
        >>> G.gain(0, 1, 2)
        Permutation(1, 2)
        """
        self._input_check_edge(u, v, key)
        return self._gain_function[u][v][key]

    @doc_category("Gain graph manipulation")
    def set_gain(self, u: Vertex, v: Vertex, key: Hashable, gain: GroupElement) -> None:
        """
        Set the gain of an edge in the graph.

        Parameters
        ----------
        u:
            The head of the edge.
        v:
            The tail of the edge.
        key:
            The key used to distinguish multi-edges.
        gain:
            An element of the group.

        Examples
        --------
        >>> from sympy.combinatorics import SymmetricGroup, Permutation
        >>> G = GainGraph(SymmetricGroup(3), {0: {1: {2: Permutation(1, 2)}}})
        >>> G.set_gain(0, 1, 2, Permutation(0, 2))
        >>> G.gain(0, 1, 2)
        Permutation(0, 2)
        """
        self._input_check_group_element(gain)
        self._input_check_edge(u, v, key)
        self._gain_function[u][v][key] = gain

    @doc_category("Gain graph manipulation")
    def set_gain_function(
        self, gain_function: GainFunction, group: Group = None
    ) -> None:
        """
        Set the gain function and group to compatible values.

        Parameters
        ----------
        gain_function:
            A gain function on the graph compatible with the group.
        group:
            A supported group. If ``group is None``, the group of the gain graph will be
            used.

        Examples
        --------
        >>> from sympy.combinatorics import CyclicGroup, AlternatingGroup, Permutation
        >>> G = GainGraph(AlternatingGroup(4), {0: {1: {2: Permutation(1, 2, 3)}}})
        >>> G.set_gain_function({0: {1: {2: Permutation(1, 3, 2)}}})
        >>> G.gain(0, 1, 2)
        Permutation(1, 3, 2)
        >>> G.set_gain_function({0: {1: {2: Permutation(0, 1, 2, 3)}}}, CyclicGroup(4))
        >>> G.gain(0, 1, 2)
        Permutation(0, 1, 2, 3)
        """
        if group is None:
            group = self.group
        else:
            _input_check.group(group)
        self._input_check_gain_function(group, gain_function)
        self._gain_function = gain_function
        self._group = group

    @doc_category("Gain graph manipulation")
    def add_vertex(self, vertex: Vertex, **attr) -> None:
        """
        Add a vertex to (or update a vertex in) the graph.

        Parameters
        ----------
        vertex:
            The vertex to add or update.
        attr:
            Attributes to set for the vertex.

        Examples
        --------
        >>> from sympy.combinatorics import CyclicGroup
        >>> G = GainGraph(CyclicGroup(2))
        >>> G.add_vertex("Alice", best_friend="Bob")
        >>> dict(G.vertices(data=True))
        {'Alice': {'best_friend': 'Bob'}}

        If a vertex is already in the graph, its attributes will be updated:

        >>> G.add_vertex("Alice", best_friend="Charlie", archenemy="Bob")
        >>> G.vertices["Alice"]
        {'best_friend': 'Charlie', 'archenemy': 'Bob'}
        """
        self.add_node(vertex, **attr)

    @doc_category("Gain graph manipulation")
    def add_vertices(
        self, vertices: Container[Vertex | tuple[Vertex, dict]], **attr
    ) -> None:
        """
        Add/update multiple vertices to/in the graph.

        Parameters
        ----------
        vertices:
            A container where each item is either a vertex ``v`` or tuple ``(v, d)``,
            where ``v`` is a vertex and ``d`` is a dictionary of vertex attributes.
        attr:
            Attributes to set for each vertex. Attributes specified in ``vertices``
            override these attributes.

        Examples
        --------
        >>> from sympy.combinatorics import CyclicGroup
        >>> G = GainGraph(CyclicGroup(2))
        >>> G.add_vertices("PyRigi", size=10)
        >>> list(G.vertices)
        ['P', 'y', 'R', 'i', 'g']
        >>> all(data == {"size": 10} for _, data in G.vertices(data=True))
        True

        If a vertex is already in the graph, its attributes will be updated:

        >>> G.add_vertices(["P"], size=9)
        >>> G.vertices["P"]
        {'size': 9}

        ``vertices`` can contain ``(v, d)`` tuples, which override ``attr``:

        >>> G.add_vertices([(1, dict(size=7, rank=1))], size=8, weight=0.5)
        >>> G.vertices[1]
        {'size': 7, 'weight': 0.5, 'rank': 1}
        """
        for vertex in vertices:
            match vertex:
                case (vertex, data) if isinstance(data, dict):
                    vertex_attr = dict(attr)
                    vertex_attr.update(data)
                    self.add_vertex(vertex, **vertex_attr)
                case vertex:
                    self.add_vertex(vertex, **attr)

    def add_nodes_from(
        self, vertices: Container[Vertex | tuple[Vertex, dict]], **attr
    ) -> None:
        """
        Alias for :meth:`.add_vertices`.

        Parameters
        ----------
        vertices:
        attr:
        """
        self.add_vertices(vertices, **attr)

    @doc_category("Gain graph manipulation")
    def delete_vertex(self, vertex: Vertex) -> None:
        """
        Remove a vertex from the gain graph.

        Parameters
        ----------
        vertex:
            A vertex in the graph.

        Examples
        --------
        >>> from sympy.combinatorics import CyclicGroup, Permutation
        >>> G = GainGraph(CyclicGroup(2))
        >>> G.add_edges([(0, 1, Permutation(1)), (1, 0, Permutation(0, 1))])
        [(0, 1, 0), (1, 0, 0)]
        >>> G.delete_vertex(1)
        >>> list(G.edges)
        []
        """
        self._input_check_vertex(vertex)

        if vertex in self._gain_function:
            del self._gain_function[vertex]
        for predecessor in self.predecessors(vertex):
            del self._gain_function[predecessor][vertex]

        super().remove_node(vertex)

    def remove_node(self, vertex: Vertex) -> None:
        """
        Alias for :meth:`.delete_vertex`.

        Parameters
        ----------
        vertex:
        """
        self.delete_vertex(vertex)

    @doc_category("Gain graph manipulation")
    def delete_vertices(self, vertices: Container[Vertex]) -> None:
        """
        Remove multiple vertices from the gain graph.

        Parameters
        ----------
        vertices:
            A container of vertices to remove. If a vertex in the container is not in the
            graph, it will be silently ignored.

        Examples
        --------
        >>> from sympy.combinatorics import CyclicGroup
        >>> G = GainGraph(CyclicGroup(2))
        >>> G.add_vertices([0, 1, 2])
        >>> G.delete_vertices([0, 2, 3])
        >>> list(G.vertices)
        [1]
        """
        for vertex in vertices:
            try:
                self.delete_vertex(vertex)
            except ValueError:
                pass

    def remove_nodes_from(self, vertices: Container[Vertex]) -> None:
        """
        Alias for :meth:`.delete_vertices`.

        Parameters
        ----------
        vertices:
        """
        self.delete_vertices(vertices)

    @doc_category("Gain graph manipulation")
    def add_edge(
        self, u: Vertex, v: Vertex, gain: GroupElement, key: Hashable = None, **attr
    ) -> DirectedMultiEdge:
        """
        Add an edge to (or update an edge in) the gain graph.

        This method returns the added or updated edge.

        Parameters
        ----------
        u:
            The head of the edge. If it is not in the graph, it will be added.
        v:
            The tail of the edge. If it is not in the graph, it will be added.
        gain:
            The group element to be associated with the edge by the gain function.
        key:
            The key used to distinguish multi-edges. If ``key is None``, it will be set
            by :meth:`networkx.MultiDiGraph.new_edge_key`.
        attr:
            Attributes to set for the edge.

        Examples
        --------
        >>> from sympy.combinatorics import DihedralGroup, Permutation
        >>> G = GainGraph(DihedralGroup(3))
        >>> G.add_edge(0, 1, Permutation(0, 2), weight=3)
        (0, 1, 0)
        >>> G.gain(0, 1, 0)
        Permutation(0, 2)
        >>> G.edges[0, 1, 0]
        {'weight': 3}

        If the edge is already in the graph, its gain and attributes will be updated:

        >>> edge = G.add_edge(0, 1, Permutation(1, 2), 0, weight=4, height=0.5)
        >>> G.gain(*edge)
        Permutation(1, 2)
        >>> G.edges[*edge]
        {'weight': 4, 'height': 0.5}
        """
        self._input_check_group_element(gain)

        key = super().add_edge(u, v, key, **attr)

        # Set gain_function[u][v][k], initializing dicts if they don't exist
        self._gain_function.setdefault(u, {}).setdefault(v, {})[key] = gain

        return (u, v, key)

    @doc_category("Gain graph manipulation")
    def add_edges(
        self,
        edges: Container[
            tuple[Vertex, Vertex, GroupElement]
            | tuple[Vertex, Vertex, GroupElement, Hashable]
            | tuple[Vertex, Vertex, GroupElement, Hashable, dict]
        ],
        **attr,
    ) -> list[DirectedMultiEdge]:
        """
        Add/update multiple edges to/in the gain graph.

        This method returns a list of the added and/or updated edges.

        Parameters
        ----------
        edges:
            A container of tuples, each of one of the following forms:

            * ``(u, v, g)``
            * ``(u, v, g, k)``
            * ``(u, v, g, k, d)``.

            Each tuple represents an edge from ``u`` to ``v`` whose gain is ``g``. If
            ``k`` is given and ``k is not None``, it will be the key used to distinguish
            multi-edges. Otherwise, this key will be set by
            :meth:`networkx.MultiDiGraph.new_edge_key`. ``d`` is an optional dictionary
            of edge attributes. The list returned by this method will be in the iteration
            order of this container.
        attr:
            Attributes to set for each edge. Attributes specified in ``edges`` override
            these attributes.

        Examples
        --------
        >>> from sympy.combinatorics import SymmetricGroup, Permutation
        >>> G = GainGraph(SymmetricGroup(4))
        >>> G.add_edges([(0, 1, Permutation(0, 3)), (1, 2, Permutation(3)(1, 2), 4)])
        [(0, 1, 0), (1, 2, 4)]
        >>> G.gain_function
        {0: {1: {0: Permutation(0, 3)}}, 1: {2: {4: Permutation(3)(1, 2)}}}

        ``edges`` can contain ``(u, v, g, k, d)`` tuples, which override ``attr``:

        >>> G.add_edges([(0, 2, Permutation(3)(0, 1), None, dict(a=1, c=3))], a=0, b=2)
        [(0, 2, 0)]
        >>> G.gain(0, 2, 0)
        Permutation(3)(0, 1)
        >>> G.edges[0, 2, 0]
        {'a': 1, 'b': 2, 'c': 3}

        If an edge is already in the graph, its gain and attributes will be updated:

        >>> [e] = G.add_edges([(0, 2, Permutation(2, 3), 0, dict(a=3, e=-1))], c=1, d=0)
        >>> G.gain(*e)
        Permutation(2, 3)
        >>> G.edges[*e]
        {'a': 3, 'b': 2, 'c': 1, 'd': 0, 'e': -1}
        """
        added = []
        for edge in edges:
            match edge:
                case (u, v, gain, key, data):
                    edge_attr = dict(attr)
                    edge_attr.update(data)
                    added.append(self.add_edge(u, v, gain, key, **edge_attr))
                case (u, v, gain, key):
                    added.append(self.add_edge(u, v, gain, key, **attr))
                case (u, v, gain):
                    added.append(self.add_edge(u, v, gain, None, **attr))
                case _:
                    raise TypeError(
                        f"{edge} does not match a pattern accepted by add_edges."
                    )
        return added

    def add_edges_from(
        self,
        edges: Container[
            tuple[Vertex, Vertex, GroupElement]
            | tuple[Vertex, Vertex, GroupElement, Hashable]
            | tuple[Vertex, Vertex, GroupElement, Hashable, dict]
        ],
        **attr,
    ) -> list[DirectedMultiEdge]:
        """
        Alias for :meth:`.add_edges`.

        Parameters
        ----------
        edges:
        attr:
        """
        return self.add_edges(edges, **attr)

    @doc_category("Gain graph manipulation")
    def add_weighted_edges(
        self,
        edges: Container[tuple[Vertex, Vertex, GroupElement, Any]],
        weight: Hashable = "weight",
        **attr,
    ) -> list[DirectedMultiEdge]:
        """
        Add multiple edges with specified weight attributes to the gain graph.

        This method returns a list of the added edges.

        Parameters
        ----------
        edges:
            A container of tuples ``(u, v, g, w)``, each representing an edge from ``u``
            to ``v`` with gain ``g`` and weight attribute ``w``. The list returned by
            this method will be in the iteration order of this container.
        weight:
            The key of the weight attributes to be set.
        attr:
            Other attributes to set for each edge.

        Examples
        --------
        >>> from sympy.combinatorics import free_group
        >>> S, a, b = free_group("a, b")
        >>> G = GainGraph(S)
        >>> G.add_weighted_edges([(0, 1, a, 2.0), (1, 2, b, 3.0)], height=4.0)
        [(0, 1, 0), (1, 2, 0)]
        >>> G.gain_function
        {0: {1: {0: a}}, 1: {2: {0: b}}}
        >>> G.edges[0, 1, 0], G.edges[1, 2, 0]
        ({'height': 4.0, 'weight': 2.0}, {'height': 4.0, 'weight': 3.0})

        The ``weight`` parameter can set the weight attribute key:

        >>> [edge] = G.add_weighted_edges([(0, 2, a * b, 2.5)], weight="length")
        >>> G.gain(*edge)
        a*b
        >>> G.edges[*edge]
        {'length': 2.5}
        """
        return self.add_edges(
            ((u, v, g, None, {weight: w}) for u, v, g, w in edges), **attr
        )

    def add_weighted_edges_from(
        self,
        edges: Container[tuple[Vertex, Vertex, GroupElement, Any]],
        weight: Hashable = "weight",
        **attr,
    ) -> list[DirectedMultiEdge]:
        """
        Alias for :meth:`.add_weighted_edges`.

        Parameters
        ----------
        edges:
        weight:
        attr:
        """
        return self.add_weighted_edges(edges, weight, **attr)

    @doc_category("Gain graph manipulation")
    def delete_edge(self, u: Vertex, v: Vertex, key: Hashable) -> None:
        """
        Remove an edge from the gain graph.

        Parameters
        ----------
        u:
            The head of the edge.
        v:
            The tail of the edge.
        key:
            The key used to distinguish multi-edges.

        Examples
        --------
        >>> from sympy.combinatorics import CyclicGroup, Permutation
        >>> G = GainGraph(CyclicGroup(2))
        >>> G.add_edges([(0, 1, Permutation(1)), (0, 1, Permutation(0, 1))])
        [(0, 1, 0), (0, 1, 1)]
        >>> G.delete_edge(0, 1, 0)
        >>> list(G.edges)
        [(0, 1, 1)]
        """
        self._input_check_edge(u, v, key)
        del self._gain_function[u][v][key]
        super().remove_edge(u, v, key)

    def remove_edge(self, u: Vertex, v: Vertex, key: Hashable) -> None:
        """
        Alias for :meth:`.delete_edge`.

        Parameters
        ----------
        u:
        v:
        key:
        """
        self.delete_edge(u, v, key)

    @doc_category("Gain graph manipulation")
    def delete_edges(self, edges: Container[DirectedMultiEdge]) -> None:
        """
        Remove multiple edges from the gain graph.

        Parameters
        ----------
        edges:
            A container of edges to remove. If an edge in the container is not in the
            graph, it will be silently ignored.

        Examples
        --------
        >>> from sympy.combinatorics import CyclicGroup, Permutation
        >>> G = GainGraph(CyclicGroup(2))
        >>> G.add_edges([(0, 1, Permutation(1)), (0, 1, Permutation(0, 1))])
        [(0, 1, 0), (0, 1, 1)]
        >>> G.delete_edges([(0, 1, 0), (1, 2, 3)])
        >>> list(G.edges)
        [(0, 1, 1)]
        """
        for edge in edges:
            try:
                self.delete_edge(*edge)
            except ValueError:
                pass

    def remove_edges_from(self, edges: Container[DirectedMultiEdge]) -> None:
        """
        Alias for :meth:`.delete_edges`.

        Parameters
        ----------
        edges:
        """
        self.delete_edges(edges)

    @doc_category("Gain graph manipulation")
    def clear(self) -> None:
        """
        Remove all vertices and attributes from the gain graph.

        Examples
        --------
        >>> from sympy.combinatorics import DihedralGroup, Permutation
        >>> G = GainGraph(DihedralGroup(4), {0: {1: {2: Permutation(3)}}}, cool=True)
        >>> G.clear()
        >>> G.graph
        {}
        >>> list(G.vertices)
        []
        >>> list(G.edges)
        []
        """
        super().clear()
        self._gain_function.clear()

    @doc_category("Gain graph manipulation")
    def clear_edges(self) -> None:
        """
        Remove all edges from the gain graph.

        Examples
        --------
        >>> from sympy.combinatorics import DihedralGroup, Permutation
        >>> G = GainGraph(DihedralGroup(4), {0: {1: {2: Permutation(3)}}}, cool=True)
        >>> G.clear_edges()
        >>> G.graph
        {'cool': True}
        >>> list(G.vertices)
        [0, 1]
        >>> list(G.edges)
        []
        """
        super().clear_edges()
        self._gain_function.clear()


GainGraphBase.__doc__ = GainGraphBase.__doc__.replace(
    "METHODS",
    generate_category_tables(
        GainGraphBase,
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
