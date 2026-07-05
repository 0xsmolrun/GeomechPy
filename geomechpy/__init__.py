"""GeomechPy - a Python library for building 1D geomechanics workflows.

Quick start
-----------
The fastest route from well logs to a mud weight window is the high-level workflow
class::

    from geomechpy import MechanicalEarthModel

    mem = MechanicalEarthModel(tvd=..., dtco=..., dtsh=..., rhob=...)
    mem.calculate_all(pore_pressure_gradient=9.0, gradient_unit="ppg")
    mem.mud_weight_window       # kick / breakout / loss / breakdown per depth
    mem.to_dataframe()          # everything as a depth-indexed DataFrame

For finer control, use the individual calculation classes directly::

    from geomechpy import DynamicElasticPropertiesCalculation, PorePressureCalculation

Public API map
--------------
Workflow
    MechanicalEarthModel - orchestrates the full log-to-mud-window chain

Elastic properties
    ElasticPropertiesConverter (alias ElasticConverter) - all pairwise moduli conversions
    DynamicElasticPropertiesCalculation (alias DynamicElastic) - velocities/slownesses to dynamic moduli
    StaticElasticPropertiesConverter (alias StaticElastic) - dynamic-to-static calibrations
    ElasticProperties, DynamicElasticProperties - result dataclasses

Pressures & stresses
    PorePressureCalculation (alias PorePressure) - gradient/EMW pore pressure profiles
    OverburdenStressCalculation (alias Overburden) - gradient or density-integrated overburden
    HorizontalStressesCalculation (alias HorizontalStress) - Eaton, K0, poroelastic Shmin/SHmax
    FractureGradientCalculation (alias FractureGradient) - Hubbert & Willis, Matthews & Kelly, Eaton
    HorizontalStresses - result dataclass

Rock strength
    RockStrengthPropertiesConverter (alias RockStrength) - UCS, tensile strength, friction angle

Wellbore stability
    WellboreStabilityCalculation (alias WellboreStability) - breakout/breakdown limits, mud weight window
    NearWellboreStressesCalculation (alias NearWellboreStresses) - Kirsch wall stresses, any trajectory
    MudWeightWindow, BoreholeWallStresses, PrincipalStresses - result dataclasses

Units
    UnitConverter (alias Units) - pressure, depth, density, velocity, slowness, gradient and mud weight conversions

pandas & plotting helpers (optional extras)
    results_to_dataframe, add_results_to_dataframe
    plot_mud_weight_window, plot_mem_profile, plot_stress_polygon, plot_elastic_properties
"""

# --- Workflow -------------------------------------------------------------
from geomechpy.mem import MechanicalEarthModel

# --- Elastic properties ---------------------------------------------------
from geomechpy.elastic_properties import ElasticProperties, ElasticPropertiesConverter
from geomechpy.dynamic_elastic_properties import DynamicElasticProperties, DynamicElasticPropertiesCalculation
from geomechpy.static_elastic_properties import StaticElasticPropertiesConverter

# --- Pressures & stresses -------------------------------------------------
from geomechpy.pore_pressure import PorePressureCalculation
from geomechpy.overburden_stress import OverburdenStressCalculation
from geomechpy.stress_calculations import HorizontalStresses, HorizontalStressesCalculation
from geomechpy.fracture_gradient import FractureGradientCalculation

# --- Rock strength ----------------------------------------------------------
from geomechpy.rock_strength import RockStrengthPropertiesConverter

# --- Wellbore stability -----------------------------------------------------
from geomechpy.wellbore_stability import MudWeightWindow, WellboreStabilityCalculation
from geomechpy.near_wellbore_stresses import BoreholeWallStresses, NearWellboreStressesCalculation, PrincipalStresses

# --- Units ------------------------------------------------------------------
from geomechpy.units import UnitConverter

# --- pandas & plotting helpers (dependencies imported lazily on call) --------
from geomechpy.dataframe_tools import add_results_to_dataframe, results_to_dataframe
from geomechpy.plotting import plot_elastic_properties, plot_mem_profile, plot_mud_weight_window, plot_stress_polygon

# --- Short aliases (the long names remain the canonical ones) ----------------
DynamicElastic = DynamicElasticPropertiesCalculation
ElasticConverter = ElasticPropertiesConverter
FractureGradient = FractureGradientCalculation
HorizontalStress = HorizontalStressesCalculation
NearWellboreStresses = NearWellboreStressesCalculation
Overburden = OverburdenStressCalculation
PorePressure = PorePressureCalculation
RockStrength = RockStrengthPropertiesConverter
StaticElastic = StaticElasticPropertiesConverter
Units = UnitConverter
WellboreStability = WellboreStabilityCalculation

__version__ = "0.0.1"

__all__ = [
    # workflow
    "MechanicalEarthModel",
    # elastic properties
    "DynamicElasticProperties",
    "DynamicElasticPropertiesCalculation",
    "ElasticProperties",
    "ElasticPropertiesConverter",
    "StaticElasticPropertiesConverter",
    # pressures & stresses
    "FractureGradientCalculation",
    "HorizontalStresses",
    "HorizontalStressesCalculation",
    "OverburdenStressCalculation",
    "PorePressureCalculation",
    # rock strength
    "RockStrengthPropertiesConverter",
    # wellbore stability
    "BoreholeWallStresses",
    "MudWeightWindow",
    "NearWellboreStressesCalculation",
    "PrincipalStresses",
    "WellboreStabilityCalculation",
    # units
    "UnitConverter",
    # pandas & plotting helpers
    "add_results_to_dataframe",
    "results_to_dataframe",
    "plot_elastic_properties",
    "plot_mem_profile",
    "plot_mud_weight_window",
    "plot_stress_polygon",
    # short aliases
    "DynamicElastic",
    "ElasticConverter",
    "FractureGradient",
    "HorizontalStress",
    "NearWellboreStresses",
    "Overburden",
    "PorePressure",
    "RockStrength",
    "StaticElastic",
    "Units",
    "WellboreStability",
]
