"""Run the >>> examples embedded in the docstrings as doctests."""

import doctest

import pytest

import geomechpy.dynamic_elastic_properties
import geomechpy.mem
import geomechpy.overburden_stress
import geomechpy.pore_pressure
import geomechpy.stress_calculations
import geomechpy.units
import geomechpy.wellbore_stability

MODULES_WITH_DOCTESTS = [
    geomechpy.dynamic_elastic_properties,
    geomechpy.mem,
    geomechpy.overburden_stress,
    geomechpy.pore_pressure,
    geomechpy.stress_calculations,
    geomechpy.units,
    geomechpy.wellbore_stability,
]


@pytest.mark.parametrize("module", MODULES_WITH_DOCTESTS, ids=lambda module: module.__name__)
def test_docstring_examples(module) -> None:
    results = doctest.testmod(module, verbose=False)
    assert results.attempted > 0, f"{module.__name__} should contain doctest examples"
    assert results.failed == 0
