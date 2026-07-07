"""GeomechPy Dashboard - interactive 1D Mechanical Earth Model explorer.

A four-tab Streamlit dashboard built entirely on the geomechpy public API:

* the physics runs through `MechanicalEarthModel` (one orchestrated call),
* the charts come from `geomechpy.plotting` with ``backend="plotly"``,
* units are handled by `UnitConverter` (field or metric display).

No calculation or plotting logic is duplicated here - this file is only UI.

Run from the repository root:

    pip install -e ".[streamlit,plotly]"
    streamlit run examples/streamlit_apps/geomechpy_dashboard.py
"""

import sys

# ---------------------------------------------------------------------------
# Optional dependencies - fail with actionable instructions, not a traceback
# ---------------------------------------------------------------------------
try:
    import streamlit as st
except ImportError:
    sys.exit(
        "This dashboard requires Streamlit.\n"
        "Install the optional extras from the repository root with:\n\n"
        "    pip install -e \".[streamlit,plotly]\"\n"
    )
try:
    import plotly  # noqa: F401  (used by geomechpy.plotting's plotly backend)
    import pandas as pd
except ImportError as error:
    sys.exit(
        f"Missing optional dependency: {error.name}.\n"
        "Install the dashboard extras from the repository root with:\n\n"
        "    pip install -e \".[streamlit,plotly]\"\n"
    )

import numpy as np

from geomechpy import (
    MechanicalEarthModel,
    MudWeightWindow,
    UnitConverter,
    plot_mem_profile,
    plot_mud_weight_window,
)

st.set_page_config(page_title="GeomechPy Dashboard", page_icon="🪨", layout="wide")

# Display unit systems: the model computes in field units; display converts on the fly
UNIT_SYSTEMS = {
    "Field (ft, psi, ppg)": {"depth": "ft", "pressure": "psi", "mud_weight": "ppg"},
    "Metric (m, MPa, SG)": {"depth": "m", "pressure": "MPa", "mud_weight": "SG"},
}


# ---------------------------------------------------------------------------
# Example data
# ---------------------------------------------------------------------------
@st.cache_data
def generate_example_logs(top_tvd: float, section_length: float, seed: int = 42) -> pd.DataFrame:
    """Synthetic shaly-sand well section: compaction trends plus correlated noise."""
    rng = np.random.default_rng(seed)
    tvd = np.arange(top_tvd, top_tvd + section_length + 10.0, 10.0)
    trend = (tvd - tvd[0]) / max(tvd[-1] - tvd[0], 1.0)
    noise = rng.normal(0.0, 1.0, len(tvd)).cumsum() / np.sqrt(len(tvd))
    return pd.DataFrame(
        {
            "tvd": tvd,                                   # ft
            "dtco": 88.0 - 14.0 * trend + 1.2 * noise,    # us/ft
            "dtsh": 158.0 - 28.0 * trend + 2.0 * noise,   # us/ft
            "rhob": 2480.0 + 130.0 * trend - 6.0 * noise, # kg/m3
        }
    )


# ---------------------------------------------------------------------------
# The model run - a single cached call into the geomechpy workflow class
# ---------------------------------------------------------------------------
@st.cache_data
def run_model(logs: pd.DataFrame, stress_method: str, pr_multiplier: float, biot: float,
              tectonic_strain: float, shmax_multiplier: float, pp_gradient_ppg: float):
    """Run the full MEM chain via MechanicalEarthModel; returns (results df, windows)."""
    mem = MechanicalEarthModel(
        tvd=logs["tvd"].tolist(),
        dtco=logs["dtco"].tolist(),
        dtsh=logs["dtsh"].tolist(),
        rhob=logs["rhob"].tolist(),
    )
    mem.calculate_elastic_properties(poissons_ratio_multiplier=pr_multiplier)
    mem.calculate_rock_strength()
    mem.calculate_pore_pressure(gradient=pp_gradient_ppg, gradient_unit="ppg")
    mem.calculate_overburden()
    if stress_method == "Poroelastic":
        # One "tectonic strain factor" drives the anisotropy: strain_y in the SHmax
        # direction, with a quarter of it in the Shmin direction
        mem.calculate_stresses(method="poroelastic", biot_coefficient=biot,
                               strain_x=tectonic_strain / 4.0, strain_y=tectonic_strain)
    else:
        mem.calculate_stresses(method="eaton", biot_coefficient=biot, shmax_multiplier=shmax_multiplier)
    mem.calculate_wellbore_stability()
    return mem.to_dataframe(), mem.mud_weight_window


def convert_windows(windows: list[MudWeightWindow], pressure_unit: str) -> list[MudWeightWindow]:
    """Convert the window limits (computed in psi) into the display pressure unit."""
    return [
        MudWeightWindow(
            kick_pressure=UnitConverter.convert_pressure(window.kick_pressure, "psi", pressure_unit),
            breakout_pressure=UnitConverter.convert_pressure(window.breakout_pressure, "psi", pressure_unit),
            loss_pressure=UnitConverter.convert_pressure(window.loss_pressure, "psi", pressure_unit),
            breakdown_pressure=UnitConverter.convert_pressure(window.breakdown_pressure, "psi", pressure_unit),
        )
        for window in windows
    ]


# ---------------------------------------------------------------------------
# Sidebar - data loading and the live model parameters
# ---------------------------------------------------------------------------
st.sidebar.title("🪨 GeomechPy Dashboard")
st.sidebar.caption("Physics: `MechanicalEarthModel` · Charts: `geomechpy.plotting` (plotly)")

if st.sidebar.button("Load example well data", type="primary") or "logs" not in st.session_state:
    top = st.session_state.get("top_tvd", 8000.0)
    length = st.session_state.get("section_length", 2000.0)
    st.session_state["logs"] = generate_example_logs(top, length)

unit_system = st.sidebar.selectbox("Unit system (display)", list(UNIT_SYSTEMS))
units = UNIT_SYSTEMS[unit_system]

st.sidebar.subheader("Model parameters")
pp_gradient_ppg = st.sidebar.slider("Pore pressure gradient [ppg EMW]", 8.0, 14.0, 9.0, 0.1)
pr_multiplier = st.sidebar.slider("Poisson's ratio (static/dynamic multiplier)", 0.7, 1.2, 1.0, 0.05)
biot = st.sidebar.slider("Biot coefficient", 0.5, 1.0, 1.0, 0.05)

stress_method = st.sidebar.radio("Horizontal stress method", ["Eaton", "Poroelastic"], horizontal=True)
tectonic_strain = 0.0004
shmax_multiplier = 1.05
if stress_method == "Poroelastic":
    tectonic_strain = st.sidebar.slider("Tectonic strain factor [×10⁻⁴]", 0.0, 10.0, 4.0, 0.5) * 1e-4
else:
    shmax_multiplier = st.sidebar.slider("SHmax / Shmin multiplier", 1.0, 1.5, 1.05, 0.01)

mud_weight_plan = st.sidebar.slider(
    f"Planned mud weight [{units['mud_weight']}]",
    *((8.0, 18.0, 10.5, 0.1) if units["mud_weight"] == "ppg" else (1.0, 2.2, 1.26, 0.02)),
)

# ---------------------------------------------------------------------------
# Run the model (cached) and stash the results in session state
# ---------------------------------------------------------------------------
logs = st.session_state["logs"]
results, windows = run_model(
    logs, stress_method, pr_multiplier, biot, tectonic_strain, shmax_multiplier, pp_gradient_ppg
)
st.session_state["results"] = results
st.session_state["windows"] = windows

# Display-unit conversions (the model computes in ft / psi / ppg)
tvd_display = UnitConverter.convert_depth_array(results.index.tolist(), "ft", units["depth"])
def pressure_display(column: str) -> list[float]:
    return UnitConverter.convert_pressure_array(results[column].tolist(), "psi", units["pressure"])

st.title("GeomechPy Dashboard")
st.caption("An interactive 1D Mechanical Earth Model — adjust the sidebar and every tab updates live.")

tab_data, tab_stress, tab_stability, tab_summary = st.tabs(
    ["📋 Data Input", "📈 Stress Model", "🟢 Wellbore Stability", "📊 Summary"]
)

# ---------------------------------------------------------------------------
# Tab 1 - Data Input
# ---------------------------------------------------------------------------
with tab_data:
    left, right = st.columns([1, 2])
    with left:
        st.subheader("Example well")
        st.session_state["top_tvd"] = st.number_input("Top TVD [ft]", 1000.0, 20000.0, st.session_state.get("top_tvd", 8000.0), 500.0)
        st.session_state["section_length"] = st.number_input("Section length [ft]", 500.0, 10000.0, st.session_state.get("section_length", 2000.0), 250.0)
        if st.button("Regenerate example well"):
            st.session_state["logs"] = generate_example_logs(st.session_state["top_tvd"], st.session_state["section_length"])
            st.rerun()
        st.caption("The synthetic section follows compaction trends (slowness decreases, density increases with depth) with correlated noise.")
    with right:
        st.subheader("Input logs")
        st.dataframe(logs, width="stretch", height=340)
        st.download_button("Download input logs (CSV)", logs.to_csv(index=False).encode(), "geomechpy_input_logs.csv", "text/csv")

# ---------------------------------------------------------------------------
# Tab 2 - Stress Model
# ---------------------------------------------------------------------------
with tab_stress:
    st.subheader(f"Stress profiles ({stress_method} horizontal stresses)")
    at_td = results.iloc[-1]
    metric_columns = st.columns(4)
    for metric_column, (label, column) in zip(metric_columns, [
        ("Pore pressure @ TD", "pore_pressure"), ("Shmin @ TD", "shmin"),
        ("SHmax @ TD", "shmax"), ("Overburden @ TD", "overburden"),
    ]):
        value = UnitConverter.convert_pressure(at_td[column], "psi", units["pressure"])
        metric_column.metric(label, f"{value:,.1f} {units['pressure']}")

    # The library's multi-track profile, rendered as an interactive plotly figure
    figure = plot_mem_profile(
        tvd_display,
        tracks={
            "Pressures & Stresses": {
                "Pp": pressure_display("pore_pressure"), "Shmin": pressure_display("shmin"),
                "SHmax": pressure_display("shmax"), "Sv": pressure_display("overburden"),
            },
        },
        track_units={"Pressures & Stresses": units["pressure"]},
        depth_unit=units["depth"],
        title="Stress model",
        figsize=(8.0, 8.0),
        backend="plotly",
    )
    st.plotly_chart(figure, width="stretch")

# ---------------------------------------------------------------------------
# Tab 3 - Wellbore Stability (mud weight window)
# ---------------------------------------------------------------------------
with tab_stability:
    st.subheader("Mud weight window (vertical well)")

    # Recommended range: the mud weight usable over the WHOLE open-hole section
    lower_bound = max(results["emw_lower"])
    upper_bound = min(results["emw_upper"])
    if units["mud_weight"] != "ppg":
        lower_bound = UnitConverter.convert_density(lower_bound, "ppg", units["mud_weight"])
        upper_bound = UnitConverter.convert_density(upper_bound, "ppg", units["mud_weight"])

    metric_columns = st.columns(3)
    if upper_bound > lower_bound:
        metric_columns[0].metric("Recommended mud weight range", f"{lower_bound:.2f} – {upper_bound:.2f} {units['mud_weight']}")
        plan_safe = lower_bound < mud_weight_plan < upper_bound
        metric_columns[1].metric("Planned mud", f"{mud_weight_plan:.2f} {units['mud_weight']}")
        metric_columns[2].metric("Plan status", "✅ inside window" if plan_safe else "⚠️ outside window")
        if not plan_safe:
            st.warning("The planned mud weight is outside the recommended range for at least part of the section.")
    else:
        metric_columns[0].metric("Recommended mud weight range", "none")
        st.error("No single mud weight is safe over the whole section — the window closes; consider an intermediate casing point.")

    # Planned mud as a pressure profile so it can be overlaid on the window chart
    mud_plan_pressure = [
        UnitConverter.convert_mud_weight_to_pressure(mud_weight_plan, depth, units["mud_weight"], units["pressure"], units["depth"])
        for depth in tvd_display
    ]
    figure = plot_mud_weight_window(
        tvd_display,
        convert_windows(windows, units["pressure"]),
        depth_unit=units["depth"],
        pressure_unit=units["pressure"],
        as_mud_weight=True,
        mud_weight_unit=units["mud_weight"],
        mud_pressure=mud_plan_pressure,
        title="Mud weight window",
        figsize=(8.0, 9.0),
        backend="plotly",
    )
    st.plotly_chart(figure, width="stretch")
    st.caption("Green band: safe window between max(kick, breakout) and min(losses, breakdown). Hover for values; click legend entries to toggle curves.")

# ---------------------------------------------------------------------------
# Tab 4 - Summary (multi-track MEM + download)
# ---------------------------------------------------------------------------
with tab_summary:
    st.subheader("Mechanical Earth Model overview")
    figure = plot_mem_profile(
        tvd_display,
        tracks={
            "Pressures & Stresses": {
                "Pp": pressure_display("pore_pressure"), "Shmin": pressure_display("shmin"),
                "SHmax": pressure_display("shmax"), "Sv": pressure_display("overburden"),
            },
            "Rock Strength": {"UCS": pressure_display("ucs"), "Tensile": pressure_display("tstr")},
            "Young's modulus": {"E dyn": results["dyn_youngs_modulus"], "E sta": results["sta_youngs_modulus"]},
            "Sonic": {"DTCO": results["dtco"], "DTSH": results["dtsh"]},
        },
        track_units={
            "Pressures & Stresses": units["pressure"], "Rock Strength": units["pressure"],
            "Young's modulus": "Mpsi", "Sonic": "µs/ft",
        },
        depth_unit=units["depth"],
        title="1D Mechanical Earth Model",
        figsize=(13.0, 8.0),
        backend="plotly",
    )
    st.plotly_chart(figure, width="stretch")

    st.download_button(
        "Download full MEM results (CSV)",
        st.session_state["results"].round(3).to_csv().encode(),
        "geomechpy_mem_results.csv",
        "text/csv",
    )
