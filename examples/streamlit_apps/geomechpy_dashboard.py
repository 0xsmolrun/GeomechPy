"""GeomechPy Dashboard - interactive 1D Mechanical Earth Model explorer.

A six-tab Streamlit dashboard built entirely on the geomechpy public API:

* the physics runs through `MechanicalEarthModel` and the calculation classes,
* the charts come from `geomechpy.plotting` with ``backend="plotly"``,
* units are handled by `UnitConverter` (field or metric display).

Highlights
----------
* Load the built-in synthetic well, or upload your own **CSV or LAS** logs.
* Toggle **borehole deviation & azimuth** on/off and drive them with sliders to see
  how the well trajectory reshapes the mud weight window (the far-field MEM - Pp, Sv,
  Shmin, SHmax - is trajectory-independent; only the *near-wellbore* response changes).
* A **stress polygon** tab that identifies the faulting regime.
* A **near-wellbore stresses** teaching tab: the Kirsch hoop / axial / radial stresses
  around the borehole wall, driven live by deviation, azimuth and mud weight sliders,
  marking where breakouts and drilling-induced tensile fractures initiate.

No calculation or plotting logic is duplicated here - this file is only UI.

Run from the repository root:

    pip install -e ".[streamlit,plotly,las]"
    streamlit run examples/streamlit_apps/geomechpy_dashboard.py
"""

import io
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make the geomechpy package importable when this example is launched directly
# (e.g. on Streamlit Community Cloud). The repository root is three levels up.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Optional dependencies - fail with actionable instructions, not a traceback
# ---------------------------------------------------------------------------
try:
    import streamlit as st
except ImportError:
    sys.exit(
        "This dashboard requires Streamlit.\n"
        "Install the extras from the repository root with:\n\n"
        "    pip install -e \".[streamlit,plotly,las]\"\n"
    )
try:
    import plotly.graph_objects as go
    import pandas as pd
except ImportError as error:
    sys.exit(
        f"Missing optional dependency: {error.name}.\n"
        "Install the dashboard extras from the repository root with:\n\n"
        "    pip install -e \".[streamlit,plotly,las]\"\n"
    )

import numpy as np

from geomechpy import (
    BoreholeWallStresses,
    HorizontalStressesCalculation,
    MechanicalEarthModel,
    MudWeightWindow,
    NearWellboreStressesCalculation,
    UnitConverter,
    WellboreStabilityCalculation,
    plot_borehole_wall_stresses,
    plot_mem_profile,
    plot_mud_weight_window,
    plot_stress_polygon,
)

st.set_page_config(page_title="GeomechPy Dashboard", page_icon="🪨", layout="wide")

# Display unit systems: the model computes in field units; display converts on the fly
UNIT_SYSTEMS = {
    "Field (ft, psi, ppg)": {"depth": "ft", "pressure": "psi", "mud_weight": "ppg"},
    "Metric (m, MPa, SG)": {"depth": "m", "pressure": "MPa", "mud_weight": "SG"},
}

# Candidate log mnemonics for auto-mapping uploaded files
COLUMN_CANDIDATES = {
    "tvd": ["TVD", "TVDSS", "DEPT", "DEPTH", "MD"],
    "dtco": ["DTCO", "DTC", "DTCOMP", "DT"],
    "dtsh": ["DTSH", "DTS", "DTSM", "DTSHEAR"],
    "rhob": ["RHOB", "RHOZ", "DEN", "DENS", "RHO"],
}


# ---------------------------------------------------------------------------
# Data loading (synthetic, CSV or LAS)
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


@st.cache_data
def read_uploaded_file(name: str, content: bytes) -> pd.DataFrame:
    """Parse an uploaded CSV or LAS file into a raw DataFrame of curves."""
    if name.lower().endswith(".las"):
        try:
            import lasio
        except ImportError as error:
            raise ImportError("Reading LAS files requires 'lasio'. Install it with 'pip install lasio' (or the 'las' extra).") from error
        las = lasio.read(io.StringIO(content.decode("utf-8", errors="replace")))
        return las.df().reset_index()  # the depth curve becomes a regular column
    return pd.read_csv(io.BytesIO(content))


def guess_column(columns: list[str], candidates: list[str]) -> str:
    """Best-effort match of a target curve to one of the DataFrame columns."""
    upper = {column.upper().strip(): column for column in columns}
    for candidate in candidates:               # exact mnemonic match first
        if candidate in upper:
            return upper[candidate]
    for candidate in candidates:               # then substring match
        for key, original in upper.items():
            if candidate in key:
                return original
    return columns[0]


# ---------------------------------------------------------------------------
# The model - all physics comes from MechanicalEarthModel / the library
# ---------------------------------------------------------------------------
@st.cache_data
def run_far_field(logs: pd.DataFrame, pp_gradient_ppg: float, pr_multiplier: float, biot: float,
                  stress_method: str, tectonic_strain: float, shmax_multiplier: float):
    """Run the trajectory-independent MEM (dynamic/static moduli, strength, Pp, Sv, Shmin, SHmax, vertical window)."""
    mem = MechanicalEarthModel(
        tvd=logs["tvd"].tolist(), dtco=logs["dtco"].tolist(),
        dtsh=logs["dtsh"].tolist(), rhob=logs["rhob"].tolist(),
    )
    mem.calculate_elastic_properties(poissons_ratio_multiplier=pr_multiplier)
    mem.calculate_rock_strength()
    mem.calculate_pore_pressure(gradient=pp_gradient_ppg, gradient_unit="ppg")
    mem.calculate_overburden()
    if stress_method == "Poroelastic":
        mem.calculate_stresses(method="poroelastic", biot_coefficient=biot,
                               strain_x=tectonic_strain / 4.0, strain_y=tectonic_strain)
    else:
        mem.calculate_stresses(method="eaton", biot_coefficient=biot, shmax_multiplier=shmax_multiplier)
    mem.calculate_wellbore_stability()
    return mem.to_dataframe(), mem.mud_weight_window


@st.cache_data
def run_deviated_window(results: pd.DataFrame, deviation: float, azimuth: float, shmax_azimuth: float,
                        n_points: int = 40, n_theta: int = 72):
    """Deviated-well mud weight window on a subsampled depth grid (equivalent mud weight, ppg).

    The deviated calculation is numerical and per-depth, so a coarse grid keeps the
    sliders responsive. Depths where no stable mud weight exists (the window closes)
    are returned as NaN so the chart shows a gap there."""
    indices = np.unique(np.linspace(0, len(results) - 1, min(n_points, len(results))).astype(int))
    sub_tvd, lower_ppg, upper_ppg, closed = [], [], [], 0
    for index in indices:
        depth = float(results.index[index])
        row = results.iloc[index]
        sub_tvd.append(depth)
        try:
            window = WellboreStabilityCalculation.calculate_mud_weight_window_deviated_well(
                shmax=row["shmax"], shmin=row["shmin"], pprs=row["pore_pressure"],
                overburden_stress=row["overburden"], ucs=row["ucs"], fang=row["fang"],
                pr_sta=row["sta_poissons_ratio"], tstr=row["tstr"],
                borehole_deviation=deviation, borehole_azimuth=azimuth, shmax_azimuth=shmax_azimuth, n_theta=n_theta,
            )
            lower = UnitConverter.convert_pressure_to_mud_weight(max(window.kick_pressure, window.breakout_pressure), depth)
            upper = UnitConverter.convert_pressure_to_mud_weight(min(window.loss_pressure, window.breakdown_pressure), depth)
            if upper <= lower:
                lower, upper = np.nan, np.nan
                closed += 1
        except ValueError:  # borehole wall shears at any mud pressure - window fully closed
            lower, upper = np.nan, np.nan
            closed += 1
        lower_ppg.append(lower)
        upper_ppg.append(upper)
    return sub_tvd, lower_ppg, upper_ppg, closed


def convert_windows(windows: list[MudWeightWindow], pressure_unit: str) -> list[MudWeightWindow]:
    """Convert the window limits (computed in psi) into the display pressure unit."""
    return [
        MudWeightWindow(
            kick_pressure=UnitConverter.convert_pressure(w.kick_pressure, "psi", pressure_unit),
            breakout_pressure=UnitConverter.convert_pressure(w.breakout_pressure, "psi", pressure_unit),
            loss_pressure=UnitConverter.convert_pressure(w.loss_pressure, "psi", pressure_unit),
            breakdown_pressure=UnitConverter.convert_pressure(w.breakdown_pressure, "psi", pressure_unit),
        )
        for w in windows
    ]


def ppg_to_mud_unit(value: float, mud_weight_unit: str) -> float:
    """Convert an equivalent mud weight in ppg to the display mud-weight unit."""
    if mud_weight_unit == "ppg" or value != value:  # NaN passes through
        return value
    return UnitConverter.convert_density(value, "ppg", mud_weight_unit)


def nearest_row(results: pd.DataFrame, depth_ft: float):
    """Return the results row nearest a depth given in ft."""
    return results.iloc[int(np.abs(results.index.to_numpy() - depth_ft).argmin())]


# ---------------------------------------------------------------------------
# Sidebar - data source, model parameters, well trajectory
# ---------------------------------------------------------------------------
st.sidebar.title("🪨 GeomechPy Dashboard")
st.sidebar.caption("Physics: `MechanicalEarthModel` · Charts: `geomechpy.plotting` (plotly)")

data_source = st.sidebar.radio("Well data", ["Example well", "Upload CSV / LAS"], horizontal=True)

if data_source == "Example well":
    if st.sidebar.button("Reload example well data") or "logs" not in st.session_state:
        st.session_state["logs"] = generate_example_logs(
            st.session_state.get("top_tvd", 8000.0), st.session_state.get("section_length", 2000.0)
        )
else:
    upload = st.sidebar.file_uploader("Upload a CSV or LAS file", type=["csv", "las"])
    if upload is not None:
        try:
            st.session_state["raw_upload"] = read_uploaded_file(upload.name, upload.getvalue())
        except Exception as error:  # surfaced in the Data tab
            st.session_state["raw_upload"] = None
            st.session_state["upload_error"] = str(error)
        else:
            st.session_state.pop("upload_error", None)

unit_system = st.sidebar.selectbox("Unit system (display)", list(UNIT_SYSTEMS))
units = UNIT_SYSTEMS[unit_system]

st.sidebar.subheader("Model parameters")
pp_gradient_ppg = st.sidebar.slider("Pore pressure gradient [ppg EMW]", 8.0, 14.0, 9.0, 0.1)
pr_multiplier = st.sidebar.slider("Poisson's ratio (static/dynamic multiplier)", 0.7, 1.2, 1.0, 0.05)
biot = st.sidebar.slider("Biot coefficient", 0.5, 1.0, 1.0, 0.05)

stress_method = st.sidebar.radio("Horizontal stress method", ["Eaton", "Poroelastic"], horizontal=True)
tectonic_strain, shmax_multiplier = 0.0004, 1.05
if stress_method == "Poroelastic":
    tectonic_strain = st.sidebar.slider("Tectonic strain factor [×10⁻⁴]", 0.0, 10.0, 4.0, 0.5) * 1e-4
else:
    shmax_multiplier = st.sidebar.slider("SHmax / Shmin multiplier", 1.0, 1.5, 1.05, 0.01)

st.sidebar.subheader("Well trajectory")
apply_deviation = st.sidebar.toggle("Apply deviation & azimuth to the mud weight window", value=False)
deviation = st.sidebar.slider("Borehole deviation [°]", 0, 90, 30, 5)
azimuth = st.sidebar.slider("Borehole azimuth [° from North]", 0, 360, 90, 15)
shmax_azimuth = st.sidebar.slider("SHmax azimuth [° from North]", 0, 180, 0, 15)
st.sidebar.caption("The sliders always drive the Near-Wellbore Stresses tab; the toggle also applies them to the Wellbore Stability window.")

mud_weight_plan = st.sidebar.slider(
    f"Planned mud weight [{units['mud_weight']}]",
    *((8.0, 18.0, 10.5, 0.1) if units["mud_weight"] == "ppg" else (1.0, 2.2, 1.26, 0.02)),
)


# ---------------------------------------------------------------------------
# Assemble the input logs (from example or upload) - needed before the tabs
# ---------------------------------------------------------------------------
st.title("GeomechPy Dashboard")
st.caption("An interactive 1D Mechanical Earth Model — adjust the sidebar and every tab updates live.")

tab_data, tab_stress, tab_polygon, tab_stability, tab_nearwell, tab_summary = st.tabs(
    ["📋 Data Input", "📈 Stress Model", "🔺 Stress Polygon", "🟢 Wellbore Stability",
     "🧭 Near-Wellbore Stresses", "📊 Summary"]
)

with tab_data:
    if data_source == "Upload CSV / LAS":
        st.subheader("Upload well logs (CSV or LAS)")
        if st.session_state.get("upload_error"):
            st.error(f"Could not read the file: {st.session_state['upload_error']}")
        raw = st.session_state.get("raw_upload")
        if raw is None:
            st.info("Upload a CSV or LAS file in the sidebar. It needs depth (TVD), compressional and shear slowness (DTCO, DTSH) and bulk density (RHOB) curves.")
            st.stop()
        st.caption("Map your file's columns to the curves GeomechPy needs (auto-detected from common mnemonics).")
        columns = list(raw.columns)
        map_cols = st.columns(4)
        mapping = {}
        for map_col, (target, candidates) in zip(map_cols, COLUMN_CANDIDATES.items()):
            default = guess_column(columns, candidates)
            mapping[target] = map_col.selectbox(target.upper(), columns, index=columns.index(default))
        logs = pd.DataFrame({target: pd.to_numeric(raw[source], errors="coerce") for target, source in mapping.items()})
        st.dataframe(raw.head(20), width="stretch", height=280)
    else:
        left, right = st.columns([1, 2])
        with left:
            st.subheader("Example well")
            st.session_state["top_tvd"] = st.number_input("Top TVD [ft]", 1000.0, 20000.0, st.session_state.get("top_tvd", 8000.0), 500.0)
            st.session_state["section_length"] = st.number_input("Section length [ft]", 500.0, 10000.0, st.session_state.get("section_length", 2000.0), 250.0)
            if st.button("Regenerate example well"):
                st.session_state["logs"] = generate_example_logs(st.session_state["top_tvd"], st.session_state["section_length"])
                st.rerun()
            st.caption("Synthetic compaction trends (slowness decreases, density increases with depth) with correlated noise.")
        with right:
            st.subheader("Input logs")
            st.dataframe(st.session_state["logs"], width="stretch", height=340)
        logs = st.session_state["logs"]

    st.download_button("Download input logs (CSV)", logs.to_csv(index=False).encode(), "geomechpy_input_logs.csv", "text/csv")

# Clean, validate and run the far-field model
logs = logs.dropna().sort_values("tvd").reset_index(drop=True)
if len(logs) < 2:
    st.error("Need at least two valid log rows with TVD, DTCO, DTSH and RHOB. Check the column mapping.")
    st.stop()
try:
    results, vertical_windows = run_far_field(
        logs, pp_gradient_ppg, pr_multiplier, biot, stress_method, tectonic_strain, shmax_multiplier
    )
except (ValueError, RuntimeError) as error:
    st.error(f"Could not build the model from these logs: {error}")
    st.stop()

st.session_state["results"] = results
st.session_state["windows"] = vertical_windows

# Display-unit helpers (the model computes in ft / psi / ppg)
tvd_display = UnitConverter.convert_depth_array(results.index.tolist(), "ft", units["depth"])
def pressure_display(column: str) -> list[float]:
    return UnitConverter.convert_pressure_array(results[column].tolist(), "psi", units["pressure"])
depth_options = [round(value, 1) for value in tvd_display]

# ---------------------------------------------------------------------------
# Tab 2 - Stress Model (far-field; trajectory-independent)
# ---------------------------------------------------------------------------
with tab_stress:
    st.subheader(f"Stress profiles ({stress_method} horizontal stresses)")
    st.caption("The far-field earth stresses are properties of the formation — they do **not** depend on the well trajectory. Deviation only changes the near-wellbore response (see the Wellbore Stability and Near-Wellbore tabs).")
    at_td = results.iloc[-1]
    metric_columns = st.columns(4)
    for metric_column, (label, column) in zip(metric_columns, [
        ("Pore pressure @ TD", "pore_pressure"), ("Shmin @ TD", "shmin"),
        ("SHmax @ TD", "shmax"), ("Overburden @ TD", "overburden"),
    ]):
        value = UnitConverter.convert_pressure(at_td[column], "psi", units["pressure"])
        metric_column.metric(label, f"{value:,.1f} {units['pressure']}")

    figure = plot_mem_profile(
        tvd_display,
        tracks={"Pressures & Stresses": {
            "Pp": pressure_display("pore_pressure"), "Shmin": pressure_display("shmin"),
            "SHmax": pressure_display("shmax"), "Sv": pressure_display("overburden"),
        }},
        track_units={"Pressures & Stresses": units["pressure"]},
        depth_unit=units["depth"], title="Stress model", figsize=(8.0, 8.0), backend="plotly",
    )
    st.plotly_chart(figure, width="stretch")

# ---------------------------------------------------------------------------
# Tab 3 - Stress Polygon and faulting regime
# ---------------------------------------------------------------------------
with tab_polygon:
    st.subheader("Stress polygon & faulting regime")
    left, right = st.columns([1, 2])
    with left:
        analysis_depth = st.select_slider("Analysis depth", options=depth_options, value=depth_options[-1], key="polygon_depth")
        friction = st.slider("Fault friction coefficient µ", 0.4, 1.0, 0.6, 0.05, key="polygon_friction")
        row = nearest_row(results, UnitConverter.convert_depth(analysis_depth, units["depth"], "ft"))
        regime = HorizontalStressesCalculation.classify_stress_regime(row["overburden"], row["shmax"], row["shmin"])
        q_factor = HorizontalStressesCalculation.calculate_stress_regime_q_factor(row["overburden"], row["shmax"], row["shmin"])
        st.metric("Faulting regime", regime)
        st.metric("Stress-regime q-factor", f"{q_factor:.2f}", help="0–1 normal · 1–2 strike-slip · 2–3 reverse")
        for label, column in [("Sv", "overburden"), ("SHmax", "shmax"), ("Shmin", "shmin"), ("Pp", "pore_pressure")]:
            st.write(f"**{label}**: {UnitConverter.convert_pressure(row[column], 'psi', units['pressure']):,.0f} {units['pressure']}")
    with right:
        figure = plot_stress_polygon(
            shmin=UnitConverter.convert_pressure(row["shmin"], "psi", units["pressure"]),
            shmax=UnitConverter.convert_pressure(row["shmax"], "psi", units["pressure"]),
            overburden_stress=UnitConverter.convert_pressure(row["overburden"], "psi", units["pressure"]),
            pore_pressure=UnitConverter.convert_pressure(row["pore_pressure"], "psi", units["pressure"]),
            friction_coefficient=friction, pressure_unit=units["pressure"],
            title=f"Stress polygon at {analysis_depth:.0f} {units['depth']}", figsize=(7.0, 7.0), backend="plotly",
        )
        st.plotly_chart(figure, width="stretch")
    st.caption("The polygon bounds the horizontal stresses allowed by frictional equilibrium (mu). NF/SS/RF label the normal, strike-slip and reverse regions; the star is the current stress state.")

# ---------------------------------------------------------------------------
# Tab 4 - Wellbore Stability (mud weight window, vertical vs deviated)
# ---------------------------------------------------------------------------
with tab_stability:
    st.subheader("Mud weight window")

    # Vertical recommended range (whole-section)
    vertical_lower = ppg_to_mud_unit(max(results["emw_lower"]), units["mud_weight"])
    vertical_upper = ppg_to_mud_unit(min(results["emw_upper"]), units["mud_weight"])

    figure = plot_mud_weight_window(
        tvd_display, convert_windows(vertical_windows, units["pressure"]),
        depth_unit=units["depth"], pressure_unit=units["pressure"],
        as_mud_weight=True, mud_weight_unit=units["mud_weight"],
        mud_pressure=[UnitConverter.convert_mud_weight_to_pressure(mud_weight_plan, d, units["mud_weight"], units["pressure"], units["depth"]) for d in tvd_display],
        title="Mud weight window", figsize=(8.5, 9.0), backend="plotly",
    )

    metric_columns = st.columns(3)
    if apply_deviation:
        sub_tvd_ft, dev_lower_ppg, dev_upper_ppg, closed = run_deviated_window(results, float(deviation), float(azimuth), float(shmax_azimuth))
        sub_tvd_disp = UnitConverter.convert_depth_array(sub_tvd_ft, "ft", units["depth"])
        dev_lower = [ppg_to_mud_unit(v, units["mud_weight"]) for v in dev_lower_ppg]
        dev_upper = [ppg_to_mud_unit(v, units["mud_weight"]) for v in dev_upper_ppg]
        figure.add_trace(go.Scatter(x=dev_lower, y=sub_tvd_disp, name=f"Deviated lower ({deviation}°/{azimuth}°)", line={"color": "#d62728", "dash": "dash"}, connectgaps=False))
        figure.add_trace(go.Scatter(x=dev_upper, y=sub_tvd_disp, name="Deviated upper", line={"color": "#9467bd", "dash": "dash"}, connectgaps=False))
        valid = [(lo, hi) for lo, hi in zip(dev_lower, dev_upper) if lo == lo and hi == hi]
        if valid:
            dev_reco_lower = max(lo for lo, _ in valid)
            dev_reco_upper = min(hi for _, hi in valid)
            metric_columns[0].metric(f"Deviated window ({deviation}°)", f"{dev_reco_lower:.2f} – {dev_reco_upper:.2f} {units['mud_weight']}" if dev_reco_upper > dev_reco_lower else "closed")
        else:
            metric_columns[0].metric(f"Deviated window ({deviation}°)", "closed")
        metric_columns[1].metric("Vertical window", f"{vertical_lower:.2f} – {vertical_upper:.2f} {units['mud_weight']}")
        metric_columns[2].metric("Depths with no window", f"{closed} / {len(sub_tvd_ft)}")
        if closed:
            st.warning(f"At {deviation}° / {azimuth}° azimuth, **{closed} of {len(sub_tvd_ft)}** sampled depths have no stable mud weight (the wall shears at any pressure) — shown as gaps in the dashed curves.")
    else:
        metric_columns[0].metric("Recommended window (vertical)", f"{vertical_lower:.2f} – {vertical_upper:.2f} {units['mud_weight']}")
        plan_safe = vertical_lower < mud_weight_plan < vertical_upper
        metric_columns[1].metric("Planned mud", f"{mud_weight_plan:.2f} {units['mud_weight']}")
        metric_columns[2].metric("Plan status", "✅ inside window" if plan_safe else "⚠️ outside window")

    st.plotly_chart(figure, width="stretch")
    st.caption("Green band: vertical-well safe window (max(kick, breakout) → min(losses, breakdown)). Turn on the trajectory toggle to overlay the deviated-well window on a coarse depth grid.")

# ---------------------------------------------------------------------------
# Tab 5 - Near-Wellbore Stresses (Kirsch hoop / axial / radial around the wall)
# ---------------------------------------------------------------------------
with tab_nearwell:
    st.subheader("Near-wellbore stresses on the borehole wall")
    st.caption("The Kirsch solution gives the effective stresses around the borehole wall for the current trajectory (deviation, azimuth, SHmax azimuth in the sidebar). Breakouts initiate where the **hoop** stress is highest; drilling-induced tensile fractures where it is lowest.")

    controls = st.columns([1, 1, 2])
    nw_depth = controls[0].select_slider("Analysis depth", options=depth_options, value=depth_options[-1], key="nw_depth")
    nw_mud = controls[1].slider(f"Mud weight [{units['mud_weight']}]", *((8.0, 18.0, float(round(mud_weight_plan, 1)), 0.1) if units["mud_weight"] == "ppg" else (1.0, 2.2, float(round(mud_weight_plan, 2)), 0.02)), key="nw_mud")
    controls[2].caption(f"Trajectory: **{deviation}° deviation**, **{azimuth}° azimuth**, SHmax at **{shmax_azimuth}°**. Adjust these in the sidebar.")

    depth_ft = UnitConverter.convert_depth(nw_depth, units["depth"], "ft")
    row = nearest_row(results, depth_ft)
    mud_pressure_psi = UnitConverter.convert_mud_weight_to_pressure(nw_mud, depth_ft, units["mud_weight"], "psi", "ft")

    theta = np.linspace(0.0, 360.0, 181)
    wall = NearWellboreStressesCalculation.calculate_kirsch_borehole_wall_stresses(
        shmin=row["shmin"], shmax=row["shmax"], svert=row["overburden"], pore_pressure=row["pore_pressure"],
        shmax_azimuth=float(shmax_azimuth), mud_pressure=mud_pressure_psi, theta=theta,
        poisson_ratio_static=row["sta_poissons_ratio"], borehole_deviation=float(deviation), borehole_azimuth=float(azimuth),
    )
    principal = NearWellboreStressesCalculation.calculate_principal_stresses_analytical(wall.sigma_tt, wall.sigma_zz, wall.sigma_tz)

    # Convert effective stresses to the display pressure unit (linear scaling)
    factor = UnitConverter.convert_pressure(1.0, "psi", units["pressure"])
    wall_display = BoreholeWallStresses(
        sigma_rr=wall.sigma_rr * factor, sigma_tt=wall.sigma_tt * factor, sigma_zz=wall.sigma_zz * factor,
        sigma_tz=wall.sigma_tz * factor, sigma_rt=wall.sigma_rt * factor, sigma_rz=wall.sigma_rz * factor,
    )
    ucs_display = UnitConverter.convert_pressure(row["ucs"], "psi", units["pressure"])
    tstr_display = UnitConverter.convert_pressure(row["tstr"], "psi", units["pressure"])

    max_hoop = float(np.max(wall.sigma_tt))
    min_hoop = float(np.min(wall.sigma_tt))
    tensile_predicted = min_hoop <= -row["tstr"]

    metric_columns = st.columns(4)
    metric_columns[0].metric("Max hoop stress", f"{max_hoop * factor:,.0f} {units['pressure']}", help="Highest where breakouts initiate")
    metric_columns[1].metric("Min hoop stress", f"{min_hoop * factor:,.0f} {units['pressure']}")
    metric_columns[2].metric("Max σ₁ at wall", f"{float(np.max(principal.sigma_1)) * factor:,.0f} {units['pressure']}", help="Governs shear (breakout) failure")
    metric_columns[3].metric("Tensile fracture", "⚠️ predicted" if tensile_predicted else "none", help="When min hoop stress ≤ −tensile strength")

    figure = plot_borehole_wall_stresses(
        theta, wall_display, ucs=ucs_display, tensile_strength=tstr_display,
        pressure_unit=units["pressure"], title=f"Borehole wall stresses at {nw_depth:.0f} {units['depth']}",
        figsize=(10.0, 6.0), backend="plotly",
    )
    st.plotly_chart(figure, width="stretch")
    st.caption("Raise the mud weight and watch the hoop stress drop (less breakout, more tensile-fracture risk). Increase deviation/azimuth in the sidebar to see the curves shift and the breakout azimuth rotate.")

# ---------------------------------------------------------------------------
# Tab 6 - Summary (multi-track MEM + download)
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
        depth_unit=units["depth"], title="1D Mechanical Earth Model", figsize=(13.0, 8.0), backend="plotly",
    )
    st.plotly_chart(figure, width="stretch")
    st.download_button(
        "Download full MEM results (CSV)", results.round(3).to_csv().encode(), "geomechpy_mem_results.csv", "text/csv"
    )
