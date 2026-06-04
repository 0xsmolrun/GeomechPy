"""GeomechPy example - run this file to produce charts.

HOW TO RUN (no coding needed):
  * In VS Code, open this file and press the green "Run and Debug" button
    (or F5). Charts are written to the `examples/outputs` folder.
  * You can drop a red breakpoint dot in the left margin next to any line
    below and press F5 to pause there and inspect the numbers.

Everything is hardcoded - there are no settings to pass in. The script just
calls a handful of geomechpy functions in order and saves the charts.
"""

import os
import sys

# Make sure the geomechpy package (one folder up) can be imported when this
# file is run directly with the VS Code "Run" button.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import matplotlib

matplotlib.use("Agg")  # save charts to files instead of opening a window
import matplotlib.pyplot as plt
import numpy as np

from geomechpy.elastic_properties import ElasticPropertiesConverter
from geomechpy.overburden_stress import OverburdenStressCalculation
from geomechpy.pore_pressure import PorePressureCalculation
from geomechpy.rock_strength import RockStrengthPropertiesConverter
from geomechpy.static_elastic_properties import StaticElasticPropertiesConverter
from geomechpy.stress_calculations import HorizontalStressesCalculation
from geomechpy.wellbore_stability import WellboreStabilityCalculation

# Where the charts are saved.
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")

# 1 Pascal expressed in Mpsi (used to convert dynamic Young's modulus units).
PA_TO_MPSI = 1.0 / (6894.757293 * 1.0e6)


def make_well_log():
    """Build a simple, hardcoded well log (depth + sonic + density + porosity).

    Returns a dictionary of numpy arrays. Units follow geomechpy conventions:
    depth [ft], slowness [us/ft], density [kg/m3], porosity [fraction].
    """
    # Depth from 6,000 ft to 12,000 ft, every 50 ft.
    tvd = np.arange(6000.0, 12001.0, 50.0)
    z = (tvd - tvd[0]) / (tvd[-1] - tvd[0])  # 0 at top, 1 at bottom

    # Simple compaction trends with a fixed, repeatable wobble so the charts
    # look realistic but are always identical.
    wobble = np.sin(tvd / 350.0)
    dtco = 95.0 - 33.0 * z + 2.0 * wobble          # compressional slowness
    dtsm = dtco * 1.9 + 3.0 * wobble               # shear slowness
    rhob = 2150.0 + 480.0 * z + 20.0 * wobble      # bulk density
    porosity = 0.32 - 0.24 * z + 0.01 * wobble     # porosity fraction

    return {
        "tvd": tvd,
        "dtco": dtco,
        "dtsm": dtsm,
        "rhob": rhob,
        "porosity": porosity,
        "air_gap": 80.0,       # ft, drill floor to sea level
        "water_depth": 450.0,  # ft, sea level to mudline
    }


def run_geomechanics(log):
    """Call the geomechpy functions step by step and collect the results.

    Good place to set breakpoints: pause on any `print(...)` line and hover
    over the variables to see the calculated arrays.
    """
    tvd = log["tvd"]

    # STEP 1 - Overburden (vertical) stress from depth.
    overburden = np.array(
        OverburdenStressCalculation.calculate_overburden_stress_offshore_array(
            tvd=tvd.tolist(),
            lithostatic_gradient=1.0,
            air_gap=log["air_gap"],
            water_depth=log["water_depth"],
            sea_water_pressure_gradient=0.45,
        )
    )
    print(f"STEP 1  overburden stress : {overburden[0]:.0f} -> {overburden[-1]:.0f} psi")

    # STEP 2 - Pore pressure from depth.
    pore_pressure = np.array(
        PorePressureCalculation.calculate_pore_pressure_offshore_array(
            tvd=tvd.tolist(),
            formation_pore_pressure_gradient=0.45,
            air_gap=log["air_gap"],
            water_depth=log["water_depth"],
            sea_water_pressure_gradient=0.45,
        )
    )
    print(f"STEP 2  pore pressure     : {pore_pressure[0]:.0f} -> {pore_pressure[-1]:.0f} psi")

    # STEP 3 - Dynamic elastic properties from sonic slowness.
    props = ElasticPropertiesConverter.convert_dynamic_elastic_properties_from_slowness_array(
        p_wave_slowness=log["dtco"].tolist(),
        s_wave_slowness=log["dtsm"].tolist(),
        density=log["rhob"].tolist(),
    )
    yme_dyn = np.array([p.youngs_modulus * PA_TO_MPSI for p in props])  # Mpsi
    pr_dyn = np.array([p.poissons_ratio for p in props])
    print(f"STEP 3  dynamic YME       : {yme_dyn.min():.2f} -> {yme_dyn.max():.2f} Mpsi")

    # STEP 4 - Static elastic properties (Bradford correlation + PR scaling).
    yme_sta = np.array(
        StaticElasticPropertiesConverter.dyn2sta_yme_bradord_array(yme_dyn=yme_dyn.tolist())
    )
    pr_sta = np.array(
        StaticElasticPropertiesConverter.dyn2sta_poissons_ratio_array(
            pr_dyn=pr_dyn.tolist(), multiplier=0.8
        )
    )
    print(f"STEP 4  static YME        : {yme_sta.min():.2f} -> {yme_sta.max():.2f} Mpsi")

    # STEP 5 - Rock strength (UCS, tensile strength, friction angle).
    ucs = np.array(
        RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb_array(yme_sta=yme_sta.tolist())
    )
    tstr = np.array(RockStrengthPropertiesConverter.convert_ucs_to_tstr_array(ucs=ucs.tolist()))
    fang = np.array(
        RockStrengthPropertiesConverter.convert_friction_angle_lal_array(dtco=log["dtco"].tolist())
    )
    print(f"STEP 5  friction angle    : {fang.min():.1f} -> {fang.max():.1f} deg")

    # STEP 6 - Horizontal stresses (poroelastic Shmin / Shmax).
    horiz = HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses_array(
        overburden_stress=overburden.tolist(),
        pore_pressure=pore_pressure.tolist(),
        poisson_ratio=pr_sta.tolist(),
        youngs_modulus=yme_sta.tolist(),
        biot_coefficient=[1.0] * tvd.size,
        EX=0.0005,
        EY=0.0012,
    )
    shmin = np.array([h.shmin for h in horiz])
    shmax = np.array([h.shmax for h in horiz])
    print(f"STEP 6  Shmin / Shmax     : {shmin.min():.0f} / {shmax.max():.0f} psi")

    # STEP 7 - Wellbore stability (collapse and fracture mud pressures).
    breakout = np.array(
        WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical_array(
            shmax=shmax.tolist(),
            shmin=shmin.tolist(),
            pprs=pore_pressure.tolist(),
            overburden_stress=overburden.tolist(),
            ucs=ucs.tolist(),
            fang=fang.tolist(),
            pr_sta=pr_sta.tolist(),
        )
    )
    breakdown = np.array(
        WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical_array(
            shmax=shmax.tolist(),
            shmin=shmin.tolist(),
            pprs=pore_pressure.tolist(),
            tstr=tstr.tolist(),
        )
    )
    print(f"STEP 7  breakout/breakdown: {breakout.min():.0f} / {breakdown.max():.0f} psi")

    return {
        "tvd": tvd,
        "dtco": log["dtco"],
        "dtsm": log["dtsm"],
        "rhob": log["rhob"],
        "porosity": log["porosity"],
        "overburden": overburden,
        "pore_pressure": pore_pressure,
        "yme_dyn": yme_dyn,
        "yme_sta": yme_sta,
        "ucs": ucs,
        "shmin": shmin,
        "shmax": shmax,
        "breakout": breakout,
        "breakdown": breakdown,
    }


def make_charts(r):
    """Create the charts and save them as PNG files in the outputs folder."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    tvd = r["tvd"]

    # CHART 1 - the input well logs.
    fig, axes = plt.subplots(1, 3, figsize=(10, 8), sharey=True)
    fig.suptitle("1. Input well logs", fontweight="bold")
    axes[0].plot(r["dtco"], tvd, color="tab:blue", label="DTCO")
    axes[0].plot(r["dtsm"], tvd, color="tab:red", label="DTSM")
    axes[0].set_xlabel("Slowness [us/ft]")
    axes[0].set_ylabel("Depth [ft]")
    axes[0].legend()
    axes[1].plot(r["rhob"], tvd, color="tab:green")
    axes[1].set_xlabel("Density [kg/m3]")
    axes[2].plot(r["porosity"] * 100.0, tvd, color="tab:purple")
    axes[2].set_xlabel("Porosity [%]")
    for ax in axes:
        ax.invert_yaxis()
        ax.grid(alpha=0.3)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    _save(fig, "01_input_logs.png")

    # CHART 2 - rock properties (elastic moduli and strength).
    fig, axes = plt.subplots(1, 2, figsize=(8, 8), sharey=True)
    fig.suptitle("2. Rock properties", fontweight="bold")
    axes[0].plot(r["yme_dyn"], tvd, color="tab:blue", label="Young's (dynamic)")
    axes[0].plot(r["yme_sta"], tvd, color="tab:red", label="Young's (static)")
    axes[0].set_xlabel("Young's modulus [Mpsi]")
    axes[0].set_ylabel("Depth [ft]")
    axes[0].legend()
    axes[1].plot(r["ucs"], tvd, color="tab:brown")
    axes[1].set_xlabel("UCS [psi]")
    for ax in axes:
        ax.invert_yaxis()
        ax.grid(alpha=0.3)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    _save(fig, "02_rock_properties.png")

    # CHART 3 - the safe mud-weight window.
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.suptitle("3. Mud-weight window", fontweight="bold")
    ax.plot(r["pore_pressure"], tvd, color="tab:cyan", label="Pore pressure")
    ax.plot(r["breakout"], tvd, color="tab:orange", label="Breakout (collapse)")
    ax.plot(r["breakdown"], tvd, color="tab:red", label="Breakdown (fracture)")
    ax.plot(r["overburden"], tvd, color="black", linestyle="--", label="Overburden")
    lower = np.maximum(r["breakout"], r["pore_pressure"])
    upper = np.minimum(r["breakdown"], r["overburden"])
    ax.fill_betweenx(tvd, lower, upper, where=upper > lower, color="tab:green", alpha=0.2, label="Safe window")
    ax.set_xlabel("Pressure [psi]")
    ax.set_ylabel("Depth [ft]")
    ax.legend()
    ax.invert_yaxis()
    ax.grid(alpha=0.3)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    _save(fig, "03_mud_weight_window.png")


def _save(fig, filename):
    """Save one figure to the outputs folder and close it."""
    path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"        saved chart -> {path}")


def main():
    print("Running GeomechPy example...")
    log = make_well_log()
    results = run_geomechanics(log)
    make_charts(results)
    print(f"Done. Open the charts in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
