"""
A module for gain graphs.
"""

import networkx as nx
from pyrigi.data_type import Vertex
from typing import Any, Optional
from collections.abc import Container, Hashable
from sympy.combinatorics import Permutation
from sympy.combinatorics.named_groups import CyclicGroup, DihedralGroup

Group = CyclicGroup | DihedralGroup
GainFunction = dict[Vertex, dict[Vertex, dict[Hashable, Permutation]]]
MultiEdge = tuple[Vertex, Vertex, Hashable]


class GainGraph(nx.MultiDiGraph):
    """
    A class representing a gain graph whose group is cyclic or dihedral.

    Attempting to instantiate the class with ``group = None`` will raise an exception.

    Parameters
    ----------
    group:
        A cyclic or dihedral group.
    gain_function:
        A dict-of-dict-of-dict ``F`` that associates the edge from ``u`` to ``v`` with
        key ``k`` with ``F[u][v][k]``, an element of the standard permutation
        representation of the group.

    METHODS

    Notes
    -----
    This class inherits the class :class:`networkx.MultiDiGraph`, and retains its
    structure for graph, vertex, and edge attributes. However, many of its methods are
    overridden to maintain the properties of the gain function, and so it is not
    guaranteed to be compatible with functions of :doc:`NetworkX <networkx:index>`
    graphs, nor can NetworkX graph views be created using this class. All applicable
    functionality from the parent class methods is available except for the creation of
    graph views (note that :meth:`~networkx.MultiDiGraph.to_directed` and
    :meth:`~networkx.MultiDiGraph.to_undirected` create views using the
    :class:`~networkx.MultiDiGraph` and :class:`~networkx.MultiGraph` classes,
    respectively, which is supported).
    """

    def __init__(
        self, group: Group = None, gain_function: GainFunction = dict(), *args, **kwargs
    ) -> None:
        """
        Set up the gain graph.
        """
        if group is None:
            raise ValueError(
                (
                    "A group must be specified. This error may be reached by attempting to "
                    "create a NetworkX graph view of a gain graph, which is not supported."
                )
            )
        super().__init__(*args, **kwargs)

        self._check_gain_function(group, gain_function)
        self._group = group
        self._gain_function = gain_function

    def _check_gain_function(self, group: Group, gain_function: GainFunction) -> None:
        """
        Raise an exception unless the gain function has the edge set of the graph as its
        domain and the standard permutation representation of ``group`` as its codomain.
        """
        edge_set = set(self.edges(keys=True))

        for u, neighbors in gain_function.items():
            for v, edges in neighbors.items():
                for key, value in edges.items():
                    if value not in group:
                        raise ValueError(
                            (
                                f"The value {value} of the gain function is not in the "
                                "standard permutation representation of the group."
                            )
                        )

                    edge = (u, v, key)
                    try:
                        edge_set.remove(edge)
                    except KeyError as err:
                        raise ValueError(
                            (
                                f"The edge {edge} is in the domain of the gain function but "
                                "not the graph."
                            )
                        ) from err

        if len(edge_set) > 0:
            raise ValueError(
                "Not all edges in the graph are in the domain of the gain function."
            )

    @property
    def group(self) -> Group:
        """
        Return the group.
        """
        return self._group

    @group.setter
    def group(self, value: Group) -> None:
        """
        Set the group.

        Attempting to set a group incompatible with the gain function will raise an
        exception.

        Parameters
        ----------
        group: A cyclic or dihedral group.
        """
        self._check_gain_function(value, self.gain_function)
        self._group = value

    @property
    def gain_function(self) -> GainFunction:
        """
        Return the gain function.
        """
        return self._gain_function

    @gain_function.setter
    def gain_function(self, value: GainFunction) -> None:
        """
        Set the gain function.

        Attempting to set a gain function incompatible with the group will raise an
        exception.

        Parameters
        ----------
        gain_function:
            A dict-of-dict-of-dict ``F`` that associates the edge from ``u`` to ``v``
            with key ``k`` with ``F[u][v][k]``, an element of the standard permutation
            representation of the group.
        """
        self._check_gain_function(self.group, value)
        self._gain_function = value

    def remove_node(self, node: Vertex) -> None:
        """
        Remove a vertex from the gain graph.

        Parameters
        ----------
        node: A vertex in the gain graph.
        """
        try:
            del self.gain_function[node]
            for predecessor in self.predecessors(node):
                del self.gain_function[predecessor][node]
        except KeyError as err:
            raise ValueError(f"The vertex {node} is not in the gain graph.") from err

        super().remove_node(node)

    def remove_nodes_from(self, nodes: Container[Vertex]) -> None:
        """
        Remove multiple vertices from the gain graph.

        Parameters
        ----------
        nodes:
            A container of vertices in the gain graph. If a vertex in the container is
            not in the gain graph, it is silently ignored.
        """
        for node in nodes:
            try:
                self.remove_node(node)
            except ValueError:
                pass

    def add_edge(
        self, u: Vertex, v: Vertex, element: Permutation, key: Hashable = None, **attr
    ) -> Hashable:
        """
        Add an edge to the gain graph. If the edge is already in the gain graph, its
        associated group element and attributes will be updated.

        Returns the key assigned to the edge.

        Attempting to associate an edge with an element outside the standard permutation
        representation of the group will raise an exception.

        Parameters
        ----------
        u:
            The head of the edge. If it is not in the gain graph, it will be added.
        v:
            The tail of the edge. If it is not in the gain graph, it will be added.
        element:
            The element of the group associated with the edge by the gain function.
        key:
            The key used to distinguish multiedges. By default, it is set by
            :meth:`networkx.MultiDiGraph.new_edge_key`.
        attr:
            Edge attributes.
        """
        if element not in self.group:
            raise ValueError(
                (
                    f"The element {element} is not in the standard permutation "
                    "representation of the group."
                )
            )

        key = super().add_edge(u, v, key, **attr)

        if u not in self.gain_function:
            self.gain_function[u] = {v: {key: element}}
        elif v not in self.gain_function[u]:
            self.gain_function[u][v] = {key: element}
        else:
            self.gain_function[u][v][key] = element

        return key

    def add_edges_from(self, edges: Container[tuple], **attr) -> list[Hashable]:
        """
        Add multiple edges to the gain graph. If an edge is already in the gain graph,
        its associated group element and attributes will be updated.

        Returns a list of the keys assigned to the edges in the iteration order of the
        container of edges.

        Attempting to associate an edge with an element outside the standard permutation
        representation of the group will raise an exception.

        Parameters
        ----------
        edges:
            A container of edges, where each edge is represented in one of the forms
            * ``(u, v, g)``,
            * ``(u, v, g, k)``, or
            * ``(u, v, g, k, d)``,
            such that the edge is from vertex ``u`` to vertex ``v`` and associated with
            the group element ``g``. ``k`` sets the edge key used to distinguish
            multiedges. By default, it is set by
            :meth:`networkx.MultiDiGraph.new_edge_key`. ``d`` sets edge attributes. To
            add an edge with attributes but no key, specify ``None`` for ``k``.
            (``None`` is not a valid key.)
        attr:
            Attributes set for each edge. Attributes specified in ``edges`` override
            override these attributes.
        """
        keylist = []
        for edge in edges:
            match edge:
                case (u, v, element, key, data):
                    edge_attr = dict(attr)
                    edge_attr.update(data)
                    keylist.append(self.add_edge(u, v, element, key, **edge_attr))
                case (u, v, element, key):
                    keylist.append(self.add_edge(u, v, element, key, **attr))
                case (u, v, element):
                    keylist.append(self.add_edge(u, v, element, **attr))
                case _:
                    raise ValueError(
                        f"{edge} does not match a pattern accepted by add_edges_from.",
                        edge,
                    )
        return keylist

    def add_weighted_edges_from(
        self,
        edges: Container[tuple[Vertex, Vertex, Permutation, Any]],
        weight: str = "weight",
        **attr,
    ) -> list[Hashable]:
        """
        Add multiple edges to the gain graph with specified weight attributes. If an edge
        is already in the gain graph, its associated group element and attributes
        will be updated.

        Returns a list of the keys assigned to the edges in the iteration order of the
        container of edges.

        Attempting to associate an edge with an element outside the standard permutation
        representation of the group will raise an exception.

        Parameters
        ----------
        edges:
            A container of edges, where each edge is represented as a tuple
            ``(u, v, g, w)`` such that the edge is from vertex ``u`` to vertex ``v``,
            associated with the group element ``g``, and has weight attribute ``w``.
        weight:
            The name of the weight attributes to be set.
        attr:
            Attributes set for each edge.
        """
        return self.add_edges_from(
            ((u, v, g, None, {weight: w}) for u, v, g, w in edges), **attr
        )

    def remove_edge(self, u: Vertex, v: Vertex, key: Hashable = None) -> None:
        """
        Remove an edge from the gain graph.

        Attempting to remove a nonexistent edge will raise an exception. Attempting to
        remove an edge without specifying the key will raise an exception if there are
        multiple candidates.

        Parameters
        ----------
        u: The head of the edge.
        v: The tail of the edge.
        key: The key used to distinguish multiedges.
        """
        try:
            edges = self.gain_function[u][v]
        except KeyError as err:
            raise ValueError(f"There are no {u}-{v} edges in the gain graph.") from err

        if key is not None:
            try:
                del edges[key]
            except KeyError as err:
                raise ValueError(
                    f"The edge {(u, v, key)} is not in the gain graph."
                ) from err
        else:
            if len(edges) == 1:
                del self.gain_function[u][v]
            else:
                raise ValueError(f"There is no unique {u}-{v} edge in the gain graph.")

        super().remove_edge(u, v, key)

    def remove_edges_from(self, edges: Container[tuple]) -> None:
        """
        Remove multiple edges from the gain graph.

        Parameters
        ----------
        edges:
            A container of edges, where each edge is represented in either the form
            * ``(u, v)`` or
            * ``(u, v, k, ...)``,
            such that the edge is from vertex ``u`` to vertex ``v``. Attempting to remove
            an edge without specifying the key ``k`` will raise an exception if there are
            multiple candidates. All other tuple entries will be ignored. If an edge in
            this container is not in the gain graph, it is silently ignored.
        """
        for edge in edges:
            try:
                self.remove_edge(*edge[:3])
            except ValueError:
                pass

    def update(
        self, edges: GainGraph | Container[tuple] = None, nodes: Container = None
    ) -> None:
        """
        Update the gain graph using another gain graph or containers of edges and/or
        vertices as input.

        Attempting to call this method with ``edges = None`` and ``nodes = None`` will
        raise an exception.

        Parameters
        ----------
        edges:
            If this parameter is another gain graph, then its nodes, edges, and graph
            attributes will be used to update the gain graph, with all edges treated
            as new. Otherwise, this parameter can be any container accepted by
            :meth:`~GainGraph.add_edges_from`.
        nodes:
            Any container accepted by :meth:`networkx.MultiDiGraph.add_nodes_from`. If
            ``edges`` is a gain graph, then this parameter is ignored.
        """
        if isinstance(edges, GainGraph):
            graph_nodes = edges.nodes
            graph_edges = edges.edges
            graph_attrs = edges.graph
            gain_function = edges.gain_function

            self.add_nodes_from(graph_nodes.data())
            self.add_edges_from(
                (u, v, gain_function[u][v][k], None, d)
                for u, v, k, d in graph_edges.data(keys=True)
            )
            self.graph.update(graph_attrs)
        else:
            if (edges is None) and (nodes is None):
                raise ValueError("Nothing was given to update.")
            if edges is not None:
                self.add_edges_from(edges)
            if nodes is not None:
                self.add_nodes_from(nodes)

    def clear(self) -> None:
        """
        Remove all vertices and attributes from the gain graph.
        """
        super().clear()
        self.gain_function.clear()

    def clear_edges(self) -> None:
        """
        Remove all edges from the gain graph.
        """
        super().clear()
        self.gain_function.clear()

    def copy(self) -> GainGraph:
        """
        Return a copy of the gain graph with deep copies of everything except graph,
        node, and edge attributes, which are shallow-copied.
        """
        graph = GainGraph(deepcopy(self.group))
        graph.graph.update(self.graph)
        graph.add_nodes_from((deepcopy(n), d.copy()) for n, d in self.nodes(data=True))
        graph.add_edges_from(
            (
                deepcopy(u),
                deepcopy(v),
                deepcopy(self.gain_function[u][v][k]),
                deepcopy(k),
                d.copy(),
            )
            for u, v, k, d in self.edges(keys=True, data=True)
        )
        return graph

    def reverse(self) -> GainGraph:
        """
        Return a deep copy of the gain graph with its edge directions reversed.
        """
        graph = GainGraph(deepcopy(self.group))
        graph.graph.update(deepcopy(self.graph))
        graph.add_nodes_from(deepcopy((n, d)) for n, d in self.nodes(data=True))
        graph.add_edges_from(
            deepcopy((v, u, self.gain_function[u][v][k], k, d))
            for u, v, k, d in self.edges(keys=True, data=True)
        )
        return graph
