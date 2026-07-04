[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)

# GeomechPy

**GeomechPy** is a Python library for building **1D geomechanics workflows** (Mechanical Earth Models) — from raw log measurements to wellbore stability limits.

Every calculation is available in a single-value form and an `_array` form for depth-indexed data, results are returned as immutable dataclasses, and each method documents its expected units and literature reference.

👉 For a detailed capabilities overview (including current gaps and the roadmap), see [skills.md](./skills.md).

## Features

- **Elastic properties** — convert any pair of elastic moduli (K, E, λ, G, ν, M) into the full set.
- **Dynamic elastic properties** — compute dynamic moduli from sonic velocities (Vp/Vs) or slownesses (DTCO/DTSH) plus bulk density.
- **Dynamic-to-static conversion** — published correlations (Bradford, Najibi, Fuller, Morales) and custom power/linear laws.
- **Pore pressure** — gradient-based pore pressure profiles for onshore and offshore settings.
- **Overburden stress** — lithostatic-gradient-based vertical stress profiles for onshore and offshore settings.
- **Horizontal stresses** — poroelastic (tectonic strain) Shmin/SHmax, SHmax multiplier method, stress regime q-factor.
- **Rock strength** — UCS (Plumb), tensile strength, friction angle (Lal) correlations.
- **Near-wellbore stresses** — Kirsch borehole wall stresses for arbitrary well orientation, principal stresses and tortuosity.
- **Wellbore stability** — breakout (Mohr-Coulomb shear failure) and breakdown (fracture initiation) pressures for vertical wells.

## Installation

GeomechPy is not yet published to PyPI. Install it from source:

```bash
git clone https://github.com/0xsmolrun/GeomechPy.git
cd GeomechPy
pip install .
```

For development (with tests):

```bash
pip install -e .
pip install pytest
pytest
```

Requires Python 3.10+.

## Quick Start

### 1. Dynamic elastic properties from sonic logs

```python
from geomechpy import DynamicElasticPropertiesCalculation

# Single depth point: Vp = 4000 m/s, Vs = 2400 m/s, density = 2650 kg/m3
props = DynamicElasticPropertiesCalculation.calculate_from_velocity(
    p_wave_velocity=4000.0,
    s_wave_velocity=2400.0,
    density=2650.0,
)
print(f"Dynamic Young's modulus: {props.youngs_modulus / 1e9:.1f} GPa")
print(f"Poisson's ratio:         {props.poissons_ratio:.3f}")
print(f"Vp/Vs ratio:             {props.vp_vs_ratio:.2f}")

# Or straight from sonic slowness logs (us/ft) along the whole well
dtco = [76.2, 80.0, 85.3]   # compressional slowness, us/ft
dtsh = [127.0, 135.5, 142.1]  # shear slowness, us/ft
rhob = [2650.0, 2600.0, 2550.0]  # bulk density, kg/m3
log = DynamicElasticPropertiesCalculation.calculate_from_slowness_array(dtco, dtsh, rhob)
```

### 2. Pore pressure and overburden stress profiles

```python
from geomechpy import PorePressureCalculation, OverburdenStressCalculation

tvd = [1000.0, 2000.0, 3000.0]  # ft

pore_pressure = PorePressureCalculation.calculate_pore_pressure_offshore_array(
    tvd=tvd,
    formation_pore_pressure_gradient=0.47,  # psi/ft
    air_gap=80.0,      # ft
    water_depth=500.0,  # ft
)

overburden = OverburdenStressCalculation.calculate_overburden_stress_offshore_array(
    tvd=tvd,
    lithostatic_gradient=1.0,  # psi/ft
    air_gap=80.0,
    water_depth=500.0,
)
```

### 3. Horizontal stresses and wellbore stability

```python
from geomechpy import HorizontalStressesCalculation, WellboreStabilityCalculation

# Poroelastic horizontal stresses at one depth
stresses = HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses(
    overburden_stress=3000.0,  # psi
    pore_pressure=1400.0,      # psi
    poisson_ratio=0.25,
    youngs_modulus=2.0,        # Mpsi
    biot_coefficient=1.0,
)

# Mud pressure limits for a vertical well
breakout = WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(
    shmax=stresses.shmax,
    shmin=stresses.shmin,
    pprs=1400.0,
    overburden_stress=3000.0,
    ucs=5000.0,   # psi
    fang=30.0,    # deg
    pr_sta=0.25,
)
breakdown = WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical(
    shmax=stresses.shmax,
    shmin=stresses.shmin,
    pprs=1400.0,
    tstr=750.0,   # psi
)
print(f"Safe mud pressure window: {breakout:.0f} - {breakdown:.0f} psi")
```

## Documentation

- [skills.md](./skills.md) — full capabilities overview, strengths, and planned features.
- Docstrings — every public method documents its inputs, outputs, units, and literature reference.

## Contributing

Contributions are welcome. Please keep new code consistent with the existing style:

- Static methods grouped in `*Calculation` / `*Converter` classes.
- Frozen dataclasses for multi-valued results.
- A scalar version and an `_array` version (`list[float]` inputs) of each calculation.
- Docstrings with units and literature references.
- Unit tests under `tests/`.

## License

This project is licensed under the terms of the **GNU Lesser General Public License v3.0**.
See the [LICENSE](./LICENSE) file for details.
