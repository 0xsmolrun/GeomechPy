# GeomechPy — Capabilities Overview

GeomechPy is a Python library for building **1D geomechanics workflows** (Mechanical Earth Models), from raw log measurements to wellbore stability limits. This document summarizes what the library can do today, what it does well, and what is still on the roadmap.

---

## Current Capabilities

### Units (`geomechpy.units`)

| Capability | Class / Function | Notes |
|---|---|---|
| Pressure / modulus conversion | `UnitConverter.convert_pressure` | Pa, kPa, MPa, GPa, psi, psia, kpsi, Mpsi, bar, atm |
| Depth / length conversion | `UnitConverter.convert_depth` | m, km, ft |
| Density conversion | `UnitConverter.convert_density` | kg/m³, g/cm³, lb/ft³, ppg, SG |
| Velocity / slowness conversion | `UnitConverter.convert_velocity`, `convert_slowness` | m/s, km/s, ft/s; s/m, µs/m, µs/ft |
| Pressure gradient conversion | `UnitConverter.convert_pressure_gradient` | Any `<pressure>/<depth>` combination (psi/ft, kPa/m, ...) plus mud weight units (ppg, SG, g/cm³) |
| Density → hydrostatic gradient | `UnitConverter.convert_density_to_pressure_gradient` | Under standard gravity |
| Mud weight ↔ downhole pressure | `UnitConverter.convert_mud_weight_to_pressure`, `convert_pressure_to_mud_weight` | Equivalent mud weight at a given TVD |

In addition, calculations are unit-flexible: unit-agnostic methods (elastic moduli conversions, wellbore stability, near-wellbore stresses) accept any consistent pressure unit, while unit-bound methods (pore pressure, overburden, dynamic moduli, strength/static correlations, poroelastic stresses) take optional unit arguments (`pressure_unit`, `depth_unit`, `velocity_unit`, `slowness_unit`, `density_unit`, `modulus_unit`) and convert internally.

### Elastic Properties (`geomechpy.elastic_properties`)

| Capability | Class / Function | Notes |
|---|---|---|
| Convert any pair of elastic moduli into all others | `ElasticPropertiesConverter.convert_from_*` | All 15 pair combinations of bulk modulus, Young's modulus, Lamé parameter, shear modulus, Poisson's ratio and P-wave modulus |
| Velocity → dynamic elastic moduli | `ElasticPropertiesConverter.convert_dynamic_elastic_properties_from_velocity` | Vp, Vs [m/s] + bulk density [kg/m³] → moduli in Pa |
| Slowness → dynamic elastic moduli | `ElasticPropertiesConverter.convert_dynamic_elastic_properties_from_slowness` | DTCO, DTSH [µs/ft] + bulk density [kg/m³] → moduli in Pa |
| Result container | `ElasticProperties` (frozen dataclass) | Bulk, Young's, Lamé, shear, Poisson's ratio, P-wave modulus |

### Dynamic Elastic Properties (`geomechpy.dynamic_elastic_properties`)

| Capability | Class / Function | Notes |
|---|---|---|
| Vp + Vs + density → dynamic moduli | `DynamicElasticPropertiesCalculation.calculate_from_velocity` | Returns moduli plus Vp/Vs ratio |
| DTCO + DTSH + density → dynamic moduli | `DynamicElasticPropertiesCalculation.calculate_from_slowness` | Sonic log (µs/ft) workflow |
| Slowness ↔ velocity conversion | `DynamicElasticPropertiesCalculation.convert_slowness_to_velocity` / `convert_velocity_to_slowness` | µs/ft ↔ m/s |
| Result container | `DynamicElasticProperties` (frozen dataclass) | Includes velocities, Vp/Vs ratio and all dynamic moduli |

### Dynamic-to-Static Conversion (`geomechpy.static_elastic_properties`)

| Capability | Class / Function | Notes |
|---|---|---|
| Bradford correlation | `StaticElasticPropertiesConverter.dyn2sta_yme_bradord` | Turbiditic sandstones (North Sea) |
| Najibi correlation | `StaticElasticPropertiesConverter.dyn2sta_yme_najib` | Carbonates (Asmari/Sarvak) |
| Fuller correlation | `StaticElasticPropertiesConverter.dyn2sta_yme_fuller` | Sandstone/shale |
| Morales correlation | `StaticElasticPropertiesConverter.dyn2sta_yme_morales` | Porosity-dependent, sandstones |
| Custom power / linear laws | `convert_dyn2sta_yme_custom_power_law`, `dyn2sta_yme_custom_linear_law` | Calibrate to your own core data |
| Static Poisson's ratio | `dyn2sta_poissons_ratio` | Constant multiplier |
| Biot coefficient | `biot_coefficient_constant_law` | Constant law |

### Pore Pressure (`geomechpy.pore_pressure`)

| Capability | Class / Function | Notes |
|---|---|---|
| Onshore pore pressure from gradient | `PorePressureCalculation.calculate_pore_pressure_onshore` | Handles air gap (KB elevation) |
| Offshore pore pressure from gradient | `PorePressureCalculation.calculate_pore_pressure_offshore` | Handles air gap + water column |

### Overburden Stress (`geomechpy.overburden_stress`)

| Capability | Class / Function | Notes |
|---|---|---|
| Onshore overburden from lithostatic gradient | `OverburdenStressCalculation.calculate_overburden_stress_onshore` | Handles air gap |
| Offshore overburden from lithostatic gradient | `OverburdenStressCalculation.calculate_overburden_stress_offshore` | Handles air gap + water column |
| Depth-integrated overburden from a density log | `calculate_overburden_stress_from_density_array` | Trapezoidal integration of rho(z)g; handles air gap + water column |

### Horizontal Stresses (`geomechpy.stress_calculations`)

| Capability | Class / Function | Notes |
|---|---|---|
| Poroelastic horizontal stresses | `HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses` | Thiercelin & Plumb (1994) with tectonic strain terms |
| Eaton's method (uniaxial strain) | `calculate_shmin_eaton` | Shmin from Sv, Pp, Poisson's ratio; optional Biot and additive tectonic stress |
| Calibrated effective stress ratio | `calculate_shmin_effective_stress_ratio` | Shmin = K0(Sv - Pp) + Pp with K0 from LOT/minifrac calibration |
| SHmax from multiplier | `calculate_shmax_multiplier` | Simple anisotropy multiplier on Shmin |
| Stress regime q-factor | `calculate_stress_regime_q_factor` | Normal / strike-slip / reverse indicator (Prats, 1981) |
| SHmax/Shmin ratio | `calculate_horizontal_stress_ratio` | Anisotropy measure |

### Rock Strength (`geomechpy.rock_strength`)

| Capability | Class / Function | Notes |
|---|---|---|
| UCS from static Young's modulus | `RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb` | Plumb (1994) generic correlation |
| Tensile strength from UCS | `convert_ucs_to_tstr` | Constant multiplier (default 0.15) |
| Friction angle from DTCO | `convert_friction_angle_lal` | Lal (1999), shale |

### Near-Wellbore Stresses (`geomechpy.near_wellbore_stresses`)

| Capability | Class / Function | Notes |
|---|---|---|
| Kirsch borehole wall stresses | `NearWellboreStressesCalculation.calculate_kirsch_borehole_wall_stresses` | Any borehole orientation (deviation + azimuth), Fjaer et al. (2008) |
| Principal stresses at the wall | `calculate_principal_stresses_analytical` | Includes tortuosity angle |
| Stress tensor rotations | `toolbox.rotate_stress_to_shmax`, `toolbox.rotate_nev_to_toh` | Principal → NEV → top-of-hole frames |

### DataFrame Tools (`geomechpy.dataframe_tools`)

| Capability | Class / Function | Notes |
|---|---|---|
| Results → DataFrame | `results_to_dataframe` | Turn any list of result dataclasses into a DataFrame, optionally indexed by TVD |
| Append results to logs | `add_results_to_dataframe` | Add result fields as columns next to the input log curves (optional prefix) |

pandas is an optional dependency (`pip install geomechpy[pandas]`); the `_array` methods accept plain `list[float]`, so `df["col"].tolist()` feeds any calculation directly.

### Wellbore Stability (`geomechpy.wellbore_stability`)

| Capability | Class / Function | Notes |
|---|---|---|
| Breakdown pressure (vertical well) | `WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical` | Hubbert & Willis tensile fracture initiation |
| Breakout pressure (vertical well) | `calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical` | Mohr-Coulomb, three borehole-wall stress orderings |
| Breakout pressure (deviated/inclined well) | `calculate_breakout_pressure_deviated_well_mohr_coulomb` | Numerical Mohr-Coulomb on the borehole wall for any well trajectory |
| Breakdown pressure (deviated/inclined well) | `calculate_breakdown_pressure_deviated_well` | Numerical tensile failure limit for any well trajectory |
| Full mud weight window | `calculate_mud_weight_window_vertical_well`, `calculate_mud_weight_window_deviated_well` | Kick / breakout / loss / breakdown limits in one `MudWeightWindow` result |

### Fracture Gradient (`geomechpy.fracture_gradient`)

| Capability | Class / Function | Notes |
|---|---|---|
| Hubbert & Willis (1957) | `FractureGradientCalculation.calculate_fracture_pressure_hubbert_willis_min` / `_max` | Lower/upper bound fracture pressure |
| Matthews & Kelly (1967) | `calculate_fracture_pressure_matthews_kelly` | Calibrated matrix stress coefficient Ki |
| Eaton (1969) | `calculate_fracture_pressure_eaton` | Poisson's ratio based; equals Eaton Shmin |

---

## Key Features & Strengths

- **Complete pairwise elastic moduli conversion** — any two known moduli can be converted into the full set.
- **Scalar and array APIs** — every calculation has a single-value form and an `_array` form (`list[float]` in, `list` out) for depth-indexed logs.
- **Immutable result objects** — multi-valued results are returned as frozen dataclasses (`ElasticProperties`, `HorizontalStresses`, `BoreholeWallStresses`, ...).
- **Literature-backed** — methods cite their sources (Zhang 2019, Jaeger, Cook & Zimmerman 2009, Fjaer et al. 2008, SPE papers) directly in docstrings.
- **Explicit units** — every docstring states the expected input and output units.
- **Unit flexibility** — a built-in `UnitConverter` plus optional unit arguments on unit-bound calculations (field or SI units, mud weight units, arbitrary gradient combinations).
- **Arbitrary borehole orientation** for near-wellbore stress analysis via full stress tensor rotation.
- **Lightweight** — only depends on NumPy (used by the near-wellbore module); everything else is standard library.

---

## Supported Calculations (Summary)

- **Unit conversions**: pressure/modulus, depth, density, velocity, slowness, pressure gradient (including ppg/SG mud weight units), and mud weight ↔ downhole pressure.
- **DataFrame tools**: convert result dataclasses to pandas DataFrames and append them to depth-indexed logs.
- **Elastic moduli conversions**: 15 pairwise conversions between K, E, λ, G, ν and M.
- **Dynamic moduli from logs**: sonic velocity or slowness plus bulk density to dynamic K, E, λ, G, ν, M and Vp/Vs.
- **Dynamic → static calibration**: 4 published Young's modulus correlations plus custom power/linear laws.
- **Pore pressure**: hydrostatic/gradient-based profiles for onshore and offshore wells, including air gap and water depth handling.
- **Overburden stress**: lithostatic-gradient-based profiles and depth-integrated density-log profiles for onshore and offshore wells.
- **Horizontal stresses**: poroelastic (tectonic strain) Shmin/SHmax, Eaton's method, calibrated effective stress ratio, SHmax multiplier method, stress regime classification.
- **Rock strength**: UCS (Plumb), tensile strength (UCS multiplier), friction angle (Lal).
- **Near-wellbore stresses**: Kirsch solution on the borehole wall for arbitrary well orientation, principal stresses and tortuosity.
- **Wellbore stability**: breakdown and breakout mud pressures for vertical wells (analytical) and deviated/inclined wells (numerical), plus the full kick/breakout/loss/breakdown mud weight window.
- **Fracture gradient**: Hubbert & Willis, Matthews & Kelly, and Eaton fracture pressure estimates.

---

## Planned / Missing Features

Being a young library (v0.0.1), several standard geomechanics workflows are not implemented yet:

- **Pore pressure prediction methods** — Eaton's resistivity/sonic method, Bowers method, equivalent depth method (only gradient-based pore pressure is available today).
- **Additional failure criteria** — Mogi-Coulomb, Drucker-Prager, modified Lade.
- **More rock strength correlations** — sonic- and porosity-based UCS correlations (McNally, Chang et al. compilation).
- **Thermal and poroelastic time-dependent wellbore effects.**
- **Anisotropic rock physics** (TI media, Thomsen parameters).

---

## Intended Use Cases

- Building **1D Mechanical Earth Models (MEM)** from wireline log data (sonic, density) for a well.
- **Pre-drill pore pressure and stress profiling** with simple gradient assumptions.
- **Mud weight design**: estimating breakout and breakdown pressure limits for vertical wells.
- **Log-based rock property estimation**: dynamic moduli from sonic logs, static calibration against core, strength correlations.
- **Near-wellbore stress analysis** for arbitrary well trajectories (input to image-log breakout interpretation and sanding studies).
- **Teaching and prototyping**: transparent, literature-referenced implementations that are easy to inspect and validate.
