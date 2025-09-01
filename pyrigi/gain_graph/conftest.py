"""
This file automatically imports the gain graph class into the docstring example sections
in this module.
"""

import pytest

from pyrigi import GainGraph


@pytest.fixture(autouse=True)
def add_GainGraph(doctest_namespace):
    doctest_namespace["GainGraph"] = GainGraph
