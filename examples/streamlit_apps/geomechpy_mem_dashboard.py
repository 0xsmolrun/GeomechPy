"""GeomechPy - 1D Mechanical Earth Model Dashboard.

Interactive Streamlit dashboard demonstrating the GeomechPy library: from well logs
(synthetic or manually entered) through dynamic/static elastic properties, rock
strength, pore pressure, overburden and horizontal stresses to the mud weight window,
with parameter sensitivity in real time.

Run from the repository root:

    pip install -e ".[streamlit,plotly]"
    streamlit run examples/streamlit_apps/geomechpy_mem_dashboard.py

All calculations are performed by the geomechpy package; this app only handles the
user interface and the interactive Plotly charts."""

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from geomechpy import (
    DynamicElasticPropertiesCalculation,
    HorizontalStressesCalculation,
    OverburdenStressCalculation,
    PorePressureCalculation,
    RockStrengthPropertiesConverter,
    StaticElasticPropertiesConverter,
    UnitConverter,
    WellboreStabilityCalculation,
    add_results_to_dataframe,
)

st.set_page_config(page_title="GeomechPy MEM Dashboard", page_icon="🪨", layout="wide")

CURVE_COLORS = {
    "pore_pressure": "#1f77b4", "shmin": "#7f7f7f", "shmax": "#ff7f0e", "overburden": "#2ca02c",
    "kick": "#1f77b4", "breakout": "#d62728", "loss": "#7f7f7f", "breakdown": "#9467bd",
}

STATIC_CALIBRATIONS = {
    "Najibi (carbonates)": lambda values: StaticElasticPropertiesConverter.dyn2sta_yme_najib_array(values),
    "Bradford (North Sea sandstones)": lambda values: StaticElasticPropertiesConverter.dyn2sta_yme_bradord_array(values),
    "Fuller (sandstone/shale)": lambda values: StaticElasticPropertiesConverter.dyn2sta_yme_fuller_array(values, modulus_unit="Mpsi"),
}


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------
@st.cache_data
def generate_synthetic_logs(top_tvd: float, bottom_tvd: float, step: float, seed: int) -> pd.DataFrame:
    """Generate a synthetic shaly-sand section with compaction trends and correlated noise."""
    rng = np.random.default_rng(seed)
    tvd = np.arange(top_tvd, bottom_tvd + step, step)
    trend = (tvd - tvd[0]) / max(tvd[-1] - tvd[0], 1.0)
    noise = rng.normal(0.0, 1.0, len(tvd)).cumsum() / np.sqrt(len(tvd))
    return pd.DataFrame(
        {
            "tvd": tvd,
            "dtco": 88.0 - 14.0 * trend + 1.2 * noise,
            "dtsh": 158.0 - 28.0 * trend + 2.0 * noise,
            "rhob": 2480.0 + 130.0 * trend - 6.0 * noise,
        }
    )


DEFAULT_MANUAL_LOGS = pd.DataFrame(
    {
        "tvd": [8000.0, 8500.0, 9000.0, 9500.0, 10000.0],
        "dtco": [86.0, 83.0, 80.0, 77.5, 75.0],
        "dtsh": [152.0, 145.0, 139.0, 134.0, 130.0],
        "rhob": [2490.0, 2520.0, 2550.0, 2580.0, 2610.0],
    }
)


# ---------------------------------------------------------------------------
# The MEM computation - everything here is geomechpy, no local physics
# ---------------------------------------------------------------------------
@st.cache_data
def compute_mem(logs: pd.DataFrame, pp_gradient_ppg: float, calibration: str, pr_multiplier: float,
                shmin_method: str, biot: float, strain_x: float, strain_y: float, k0: float,
                shmax_multiplier: float, tstr_multiplier: float) -> pd.DataFrame:
    """Run the full 1D MEM chain on the input logs and return one tidy DataFrame."""
    mem = logs.copy().reset_index(drop=True)
    tvd = mem["tvd"].tolist()

    dynamic = DynamicElasticPropertiesCalculation.calculate_from_slowness_array(
        mem["dtco"].tolist(), mem["dtsh"].tolist(), mem["rhob"].tolist(), modulus_unit="Mpsi"
    )
    mem = add_results_to_dataframe(mem, dynamic, prefix="dyn_")

    mem["sta_youngs_modulus"] = STATIC_CALIBRATIONS[calibration](mem["dyn_youngs_modulus"].tolist())
    mem["sta_poissons_ratio"] = StaticElasticPropertiesConverter.dyn2sta_poissons_ratio_array(
        mem["dyn_poissons_ratio"].tolist(), multiplier=pr_multiplier
    )

    mem["ucs"] = RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb_array(mem["sta_youngs_modulus"].tolist())
    mem["tstr"] = RockStrengthPropertiesConverter.convert_ucs_to_tstr_array(mem["ucs"].tolist(), multiplier=tstr_multiplier)
    mem["fang"] = RockStrengthPropertiesConverter.convert_friction_angle_lal_array(mem["dtco"].tolist())

    mem["pore_pressure"] = PorePressureCalculation.calculate_pore_pressure_onshore_array(
        tvd=tvd, formation_pore_pressure_gradient=pp_gradient_ppg, gradient_unit="ppg"
    )
    mem["overburden"] = OverburdenStressCalculation.calculate_overburden_stress_from_density_array(
        tvd=tvd, density=mem["rhob"].tolist()
    )

    if shmin_method == "Poroelastic (Thiercelin & Plumb)":
        stresses = HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses_array(
            overburden_stress=mem["overburden"].tolist(), pore_pressure=mem["pore_pressure"].tolist(),
            poisson_ratio=mem["sta_poissons_ratio"].tolist(), youngs_modulus=mem["sta_youngs_modulus"].tolist(),
            biot_coefficient=[biot] * len(mem), EX=strain_x, EY=strain_y,
        )
        mem["shmin"] = [entry.shmin for entry in stresses]
        mem["shmax"] = [entry.shmax for entry in stresses]
    else:
        if shmin_method == "Eaton (uniaxial strain)":
            mem["shmin"] = HorizontalStressesCalculation.calculate_shmin_eaton_array(
                overburden_stress=mem["overburden"].tolist(), pore_pressure=mem["pore_pressure"].tolist(),
                poisson_ratio=mem["sta_poissons_ratio"].tolist(), biot_coefficient=biot,
            )
        else:  # calibrated K0
            mem["shmin"] = HorizontalStressesCalculation.calculate_shmin_effective_stress_ratio_array(
                overburden_stress=mem["overburden"].tolist(), pore_pressure=mem["pore_pressure"].tolist(),
                effective_stress_ratio=k0, biot_coefficient=biot,
            )
        mem["shmax"] = HorizontalStressesCalculation.calculate_shmax_multiplier_array(
            shmin=mem["shmin"].tolist(), shmax_multiplier=shmax_multiplier
        )

    windows = WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well_array(
        shmax=mem["shmax"].tolist(), shmin=mem["shmin"].tolist(), pprs=mem["pore_pressure"].tolist(),
        overburden_stress=mem["overburden"].tolist(), ucs=mem["ucs"].tolist(), fang=mem["fang"].tolist(),
        pr_sta=mem["sta_poissons_ratio"].tolist(), tstr=mem["tstr"].tolist(),
    )
    mem = add_results_to_dataframe(mem, windows)

    for column, source in [("emw_kick", "kick_pressure"), ("emw_breakout", "breakout_pressure"),
                           ("emw_loss", "loss_pressure"), ("emw_breakdown", "breakdown_pressure")]:
        mem[column] = UnitConverter.convert_pressure_to_mud_weight_array(mem[source].tolist(), tvd)
    mem["emw_lower"] = mem[["emw_kick", "emw_breakout"]].max(axis=1)
    mem["emw_upper"] = mem[["emw_loss", "emw_breakdown"]].min(axis=1)

    return mem


# ---------------------------------------------------------------------------
# Sidebar - data source and model parameters
# ---------------------------------------------------------------------------
st.sidebar.title("🪨 GeomechPy MEM")
st.sidebar.caption("All physics computed by the `geomechpy` package")

data_source = st.sidebar.radio("Well data", ["Synthetic well", "Manual input"], horizontal=True)

if data_source == "Synthetic well":
    with st.sidebar.expander("Synthetic well controls", expanded=False):
        top_tvd = st.number_input("Top TVD [ft]", 1000.0, 20000.0, 8000.0, 500.0)
        section_length = st.number_input("Section length [ft]", 500.0, 10000.0, 2000.0, 250.0)
        seed = st.number_input("Random seed", 0, 9999, 42, 1)
    logs = generate_synthetic_logs(top_tvd, top_tvd + section_length, 10.0, int(seed))
else:
    st.sidebar.info("Edit the log table in the **Data** tab (add or remove rows as needed).")
    if "manual_logs" not in st.session_state:
        st.session_state["manual_logs"] = DEFAULT_MANUAL_LOGS.copy()
    logs = st.session_state["manual_logs"]

st.sidebar.subheader("Pore pressure")
pp_gradient_ppg = st.sidebar.slider("Pore pressure gradient [ppg EMW]", 8.0, 16.0, 9.0, 0.1)

st.sidebar.subheader("Elastic calibration")
calibration = st.sidebar.selectbox("Dynamic → static Young's modulus", list(STATIC_CALIBRATIONS))
pr_multiplier = st.sidebar.slider("Static / dynamic Poisson's ratio", 0.7, 1.2, 1.0, 0.05)

st.sidebar.subheader("Horizontal stresses")
shmin_method = st.sidebar.selectbox(
    "Shmin method", ["Eaton (uniaxial strain)", "Calibrated K0", "Poroelastic (Thiercelin & Plumb)"]
)
biot = st.sidebar.slider("Biot coefficient", 0.5, 1.0, 1.0, 0.05)
strain_x = strain_y = 0.0
k0 = 0.75
shmax_multiplier = 1.05
if shmin_method == "Poroelastic (Thiercelin & Plumb)":
    strain_x = st.sidebar.slider("Tectonic strain εx (Shmin direction) [×10⁻⁴]", 0.0, 10.0, 1.0, 0.5) * 1e-4
    strain_y = st.sidebar.slider("Tectonic strain εy (SHmax direction) [×10⁻⁴]", 0.0, 10.0, 4.0, 0.5) * 1e-4
elif shmin_method == "Calibrated K0":
    k0 = st.sidebar.slider("Effective stress ratio K0", 0.4, 1.0, 0.75, 0.01)
if shmin_method != "Poroelastic (Thiercelin & Plumb)":
    shmax_multiplier = st.sidebar.slider("SHmax / Shmin multiplier", 1.0, 1.5, 1.05, 0.01)

st.sidebar.subheader("Rock strength")
tstr_multiplier = st.sidebar.slider("Tensile strength / UCS", 0.05, 0.25, 0.15, 0.01)

st.sidebar.subheader("Drilling")
mud_weight_plan = st.sidebar.slider("Planned mud weight [ppg]", 8.0, 18.0, 10.5, 0.1)


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------
st.title("GeomechPy — 1D Mechanical Earth Model Dashboard")
st.caption(
    "Well logs → dynamic & static elastic properties → rock strength → pore pressure & overburden "
    "→ horizontal stresses → mud weight window. Adjust parameters in the sidebar; everything updates live."
)

tab_data, tab_profile, tab_window, tab_stability, tab_results = st.tabs(
    ["📋 Data", "📊 MEM Profile", "🟢 Mud Weight Window", "🧭 Stability & Stress Polygon", "⬇️ Results"]
)

with tab_data:
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Input well logs")
        if data_source == "Manual input":
            st.session_state["manual_logs"] = st.data_editor(
                st.session_state["manual_logs"], num_rows="dynamic", width="stretch",
                column_config={
                    "tvd": st.column_config.NumberColumn("TVD [ft]", min_value=0.0),
                    "dtco": st.column_config.NumberColumn("DTCO [µs/ft]", min_value=40.0, max_value=200.0),
                    "dtsh": st.column_config.NumberColumn("DTSH [µs/ft]", min_value=60.0, max_value=400.0),
                    "rhob": st.column_config.NumberColumn("RHOB [kg/m³]", min_value=1500.0, max_value=3200.0),
                },
            )
            logs = st.session_state["manual_logs"]
        else:
            st.dataframe(logs, width="stretch", height=320)
    with right:
        st.subheader("Curve summary")
        st.dataframe(logs.describe().loc[["min", "mean", "max"]].round(1), width="stretch")
        st.download_button(
            "Download input logs (CSV)", logs.to_csv(index=False).encode(), "geomechpy_input_logs.csv", "text/csv"
        )

# Validate and compute
logs = logs.dropna().sort_values("tvd").reset_index(drop=True)
if len(logs) < 2:
    st.error("Provide at least two valid log rows (TVD, DTCO, DTSH, RHOB).")
    st.stop()

mem = compute_mem(
    logs, pp_gradient_ppg, calibration, pr_multiplier, shmin_method,
    biot, strain_x, strain_y, k0, shmax_multiplier, tstr_multiplier,
)
tvd = mem["tvd"].tolist()

with tab_profile:
    st.subheader("Multi-track MEM profile")
    available_tracks = {
        "Pressures & Stresses [psi]": {
            "Pp": ("pore_pressure", CURVE_COLORS["pore_pressure"]), "Shmin": ("shmin", CURVE_COLORS["shmin"]),
            "SHmax": ("shmax", CURVE_COLORS["shmax"]), "Sv": ("overburden", CURVE_COLORS["overburden"]),
        },
        "Rock strength [psi]": {"UCS": ("ucs", "#d62728"), "Tensile": ("tstr", "#e377c2")},
        "Young's modulus [Mpsi]": {"E dynamic": ("dyn_youngs_modulus", "#17becf"), "E static": ("sta_youngs_modulus", "#1f77b4")},
        "Poisson's ratio [-]": {"PR dynamic": ("dyn_poissons_ratio", "#17becf"), "PR static": ("sta_poissons_ratio", "#1f77b4")},
        "Sonic [µs/ft]": {"DTCO": ("dtco", "#8c564b"), "DTSH": ("dtsh", "#bcbd22")},
        "Density [kg/m³]": {"RHOB": ("rhob", "#2ca02c")},
    }
    selected = st.multiselect(
        "Tracks to display (toggle individual curves via the chart legend)",
        list(available_tracks), default=list(available_tracks)[:4],
    )
    if selected:
        figure = make_subplots(rows=1, cols=len(selected), shared_yaxes=True, subplot_titles=selected, horizontal_spacing=0.04)
        for column_index, track in enumerate(selected, start=1):
            for label, (column, color) in available_tracks[track].items():
                figure.add_trace(
                    go.Scatter(x=mem[column], y=tvd, name=label, legendgroup=label, mode="lines", line={"color": color}),
                    row=1, col=column_index,
                )
        figure.update_yaxes(autorange="reversed", title_text="TVD [ft]", row=1, col=1)
        figure.update_layout(height=650, legend={"orientation": "h", "y": -0.08}, margin={"t": 60, "b": 20})
        st.plotly_chart(figure, width="stretch")
    else:
        st.info("Select at least one track.")

with tab_window:
    st.subheader("Mud weight window (equivalent mud weight)")
    window_open = (mem["emw_upper"] > mem["emw_lower"]).all()
    mud_ok = ((mem["emw_lower"] < mud_weight_plan) & (mud_weight_plan < mem["emw_upper"])).all()

    metric_columns = st.columns(4)
    metric_columns[0].metric("Safe window at TD [ppg]", f"{mem['emw_lower'].iloc[-1]:.2f} – {mem['emw_upper'].iloc[-1]:.2f}")
    tightest_index = (mem["emw_upper"] - mem["emw_lower"]).idxmin()
    metric_columns[1].metric("Tightest window [ppg]", f"{mem['emw_upper'][tightest_index] - mem['emw_lower'][tightest_index]:.2f}",
                             f"at {mem['tvd'][tightest_index]:.0f} ft", delta_color="off")
    metric_columns[2].metric("Planned mud [ppg]", f"{mud_weight_plan:.1f}")
    metric_columns[3].metric("Mud plan status", "✅ safe" if mud_ok else "⚠️ outside window")

    figure = go.Figure()
    figure.add_trace(go.Scatter(x=mem["emw_lower"], y=tvd, name="Window lower bound", line={"width": 0}, showlegend=False, hoverinfo="skip"))
    figure.add_trace(go.Scatter(x=mem["emw_upper"], y=tvd, name="Safe window", fill="tonextx", fillcolor="rgba(120, 200, 120, 0.35)", line={"width": 0}))
    for label, column, color, dash in [
        ("Pore pressure (kick)", "emw_kick", CURVE_COLORS["kick"], "solid"),
        ("Breakout", "emw_breakout", CURVE_COLORS["breakout"], "solid"),
        ("Shmin (losses)", "emw_loss", CURVE_COLORS["loss"], "dash"),
        ("Breakdown", "emw_breakdown", CURVE_COLORS["breakdown"], "solid"),
    ]:
        figure.add_trace(go.Scatter(x=mem[column], y=tvd, name=label, line={"color": color, "dash": dash}))
    figure.add_trace(go.Scatter(x=[mud_weight_plan] * len(tvd), y=tvd, name="Planned mud", line={"color": "black", "dash": "dot", "width": 3}))
    figure.update_yaxes(autorange="reversed", title_text="TVD [ft]")
    figure.update_xaxes(title_text="Equivalent mud weight [ppg]")
    figure.update_layout(height=650, legend={"orientation": "h", "y": -0.12}, margin={"t": 30})
    st.plotly_chart(figure, width="stretch")

    if not window_open:
        st.warning("The mud weight window is **closed** over part of the section — the mud needed to prevent breakouts exceeds the loss/breakdown limit there.")
    elif not mud_ok:
        st.warning("The planned mud weight falls **outside** the safe window over part of the section.")

with tab_stability:
    st.subheader("Well trajectory sensitivity")
    left, right = st.columns(2)

    with left:
        analysis_tvd = st.select_slider("Analysis depth [ft TVD]", options=[round(v, 1) for v in tvd], value=round(tvd[-1], 1))
        azimuth = st.slider("Borehole azimuth [° from North]", 0, 180, 90, 5)
        shmax_azimuth = st.slider("SHmax azimuth [° from North]", 0, 180, 0, 5)
        at_depth = mem.iloc[(mem["tvd"] - analysis_tvd).abs().idxmin()]

        deviations = list(range(0, 91, 10))
        lower_bounds, upper_bounds, open_deviations = [], [], []
        for deviation in deviations:
            try:
                window = WellboreStabilityCalculation.calculate_mud_weight_window_deviated_well(
                    shmax=at_depth["shmax"], shmin=at_depth["shmin"], pprs=at_depth["pore_pressure"],
                    overburden_stress=at_depth["overburden"], ucs=at_depth["ucs"], fang=at_depth["fang"],
                    pr_sta=at_depth["sta_poissons_ratio"], tstr=at_depth["tstr"],
                    borehole_deviation=float(deviation), borehole_azimuth=float(azimuth),
                    shmax_azimuth=float(shmax_azimuth), n_theta=91,
                )
            except ValueError:
                break  # wall shears at any mud pressure beyond this deviation
            open_deviations.append(deviation)
            lower_bounds.append(UnitConverter.convert_pressure_to_mud_weight(
                max(window.kick_pressure, window.breakout_pressure), at_depth["tvd"]))
            upper_bounds.append(UnitConverter.convert_pressure_to_mud_weight(
                min(window.loss_pressure, window.breakdown_pressure), at_depth["tvd"]))

        figure = go.Figure()
        figure.add_trace(go.Scatter(x=open_deviations, y=lower_bounds, name="Required mud (breakout/kick)", line={"color": CURVE_COLORS["breakout"]}))
        figure.add_trace(go.Scatter(x=open_deviations, y=upper_bounds, name="Limit (losses/breakdown)", fill="tonexty", fillcolor="rgba(120, 200, 120, 0.35)", line={"color": CURVE_COLORS["loss"]}))
        figure.add_hline(y=mud_weight_plan, line={"color": "black", "dash": "dot"}, annotation_text="planned mud")
        figure.update_xaxes(title_text="Borehole deviation [°]", range=[0, 90])
        figure.update_yaxes(title_text="Equivalent mud weight [ppg]")
        figure.update_layout(height=450, title=f"Mud window vs deviation at {at_depth['tvd']:.0f} ft", legend={"orientation": "h", "y": -0.2}, margin={"t": 40})
        st.plotly_chart(figure, width="stretch")
        if len(open_deviations) < len(deviations):
            last_stable = open_deviations[-1] if open_deviations else 0
            st.warning(f"Beyond **{last_stable}°** deviation the borehole wall shears at any mud pressure — a stable well cannot be drilled at this depth and azimuth.")

    with right:
        friction = st.slider("Fault friction coefficient µ", 0.4, 1.0, 0.6, 0.05)
        q = (math.sqrt(friction**2 + 1) + friction) ** 2
        sv, pp = at_depth["overburden"], at_depth["pore_pressure"]
        shmin_limit = (sv - pp) / q + pp
        shmax_limit = q * (sv - pp) + pp
        polygon_x = [shmin_limit, shmin_limit, sv, shmax_limit, shmin_limit]
        polygon_y = [shmin_limit, sv, shmax_limit, shmax_limit, shmin_limit]

        figure = go.Figure()
        figure.add_trace(go.Scatter(x=polygon_x, y=polygon_y, name=f"Frictional limits (µ={friction})", line={"color": "black"}))
        figure.add_trace(go.Scatter(x=[shmin_limit, sv], y=[sv, sv], mode="lines", line={"color": "gray", "dash": "dash"}, showlegend=False))
        figure.add_trace(go.Scatter(x=[sv, sv], y=[sv, shmax_limit], mode="lines", line={"color": "gray", "dash": "dash"}, showlegend=False))
        figure.add_trace(go.Scatter(x=[at_depth["shmin"]], y=[at_depth["shmax"]], mode="markers", name="Stress state",
                                    marker={"symbol": "star", "size": 18, "color": CURVE_COLORS["breakout"]}))
        for text, x, y in [("NF", (shmin_limit + sv) / 2, (shmin_limit + sv) / 2 + 0.06 * (shmax_limit - shmin_limit)),
                           ("SS", (shmin_limit + sv) / 2, (sv + shmax_limit) / 2),
                           ("RF", (sv + shmax_limit) / 2, (sv + shmax_limit) / 2 + 0.04 * (shmax_limit - shmin_limit))]:
            figure.add_annotation(x=x, y=y, text=text, showarrow=False, font={"color": "gray", "size": 14})
        figure.update_xaxes(title_text="Shmin [psi]")
        figure.update_yaxes(title_text="SHmax [psi]", scaleanchor="x", scaleratio=1)
        figure.update_layout(height=520, title=f"Stress polygon at {at_depth['tvd']:.0f} ft", legend={"orientation": "h", "y": -0.15}, margin={"t": 40})
        st.plotly_chart(figure, width="stretch")

with tab_results:
    st.subheader("Full MEM results")
    st.caption("Every computed curve at every depth — all values from geomechpy calculations.")
    display = mem.round(3)
    st.dataframe(display, width="stretch", height=480)
    st.download_button(
        "Download full MEM results (CSV)", display.to_csv(index=False).encode(), "geomechpy_mem_results.csv", "text/csv"
    )
