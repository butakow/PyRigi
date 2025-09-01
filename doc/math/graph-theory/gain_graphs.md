# Gain Graphs

:::{prf:definition} Gain graph
:label: def-gain-graph

Let $G$ be a directed multigraph (i.e. multi-edges and loops are permitted). Given a
group $\Gamma$, a _gain function_ on $G$ is a function $\psi: E(G) \to \Gamma$ that
labels each edge in $G$ with an element of $\Gamma$. The pair $(G, \psi)$ is called a
_$\Gamma$-gain graph_.

{{pyrigi_crossref}} {class}`~.GainGraph`
:::

:::{prf:definition} Switching operation
:label: def-switching-operation

Let $(G, \psi)$ be a $\Gamma$-{prf:ref}`gain graph <def-gain-graph>`. For $v \in V(G)$
and $g \in \Gamma$, the _switching operation at $v$ with $g$_ on $\psi$ maps $\psi$ to the
following gain function on $G$:
\begin{equation*}
    \psi'(e) = \begin{cases}
        g \cdot \psi(e) \cdot g^{-1} &\text{if } e \text{ is a loop on } v \\
        g \cdot \psi(e) &\text{if } e \text{ is a non-loop edge directed from } v \\
        \psi(e) \cdot g^{-1} &\text{if } e \text{ is a non-loop edge directed to } v \\
        \psi(e) &\text{otherwise.}
    \end{cases}
\end{equation*}
A gain function $\psi'$ on $G$ is _equivalent_ to another gain function $\psi$ on $G$ if
there exists a sequence of switching operations that transforms $\psi$ to $\psi'$.

{{pyrigi_crossref}} {meth}`~.GainGraph.switching_operation`
:::

:::{prf:algorithm}
:label: alg-equivalent-gain-function

**Input:** A group $\Gamma$ with identity $\mathrm{id}$, a
$\Gamma$-{prf:ref}`gain graph <def-gain-graph>` $(G, \psi)$, and some $F \subseteq E(G)$
that forms a forest if its edge directions are ignored

**Output:** A gain function $\psi'$ on $G$
{prf:ref}`equivalent <def-switching-operation>` to $\psi$ such that
$\psi(e) = \mathrm{id}$ for each $e \in F$

1. Let $\psi' = \psi$.
2. Choose an unvisited vertex $r \in G$ if one exists. Otherwise, return $\psi'$.
3. Initialize the maps $P_\mathrm{in}$ and $P_\mathrm{out}$, let $v = r$, and skip to
step 7.
4. Choose a vertex $v$ as follows:
    * If $P_\mathrm{in}$ is nonempty, choose $v$ from its domain and let
    $e = P_\mathrm{in}(v)$. If $v \in \operatorname{dom} P_\mathrm{out}$, remove its
    entry in $P_\mathrm{out}$.
    * Otherwise, if $P_\mathrm{out}$ is nonempty, choose $v$ from its domain and let
    $e = P_\mathrm{out}(v)$.
    * If both maps are empty, return to step 2.
5. If $e$ is directed toward $v$, let $g = \psi'(e)$. Otherwise, let
$g = \psi'(e)^{-1}$.
6. Perform the switching operation at $v$ with $g$ on $\psi'$.
7. Loop over all the unvisited neighbors (predecessors and successors) of $v$. For each
unvisited neighbor $w$:
    * If there is an edge $e' \in F$ connecting $v$ and $w$, set $P_\mathrm{in}(w) = e'$.
    * Otherwise, choose some edge $e'$ connecting $v$ and $w$ and set
    $P_\mathrm{out}(w) = e'$.
8. Mark $v$ as visited and return to step 4.

{{pyrigi_crossref}} {meth}`~.GainGraph.equivalent_gain_function`

{{references}} {cite:p}`JordanKaszanitzkyTanigawa2012{Prop 2.3}`
:::
