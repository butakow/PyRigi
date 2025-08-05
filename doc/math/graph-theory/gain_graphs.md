# Gain graphs

:::{prf:definition} Gain graph
:label: def-gain-graph

Let $\Gamma$ be a group. A _$\Gamma$-gain graph_ is a pair $(G, \psi)$ consisting of a directed
multigraph $G = (V, E)$ (i.e. multi-edges and loops are permitted) and a _gain function_
$\psi: E \to \Gamma$ that labels each edge in $G$ with an element of $\Gamma$.

{{pyrigi_crossref}} {class}`~pyrigi.GainGraph`
:::