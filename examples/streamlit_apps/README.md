# GeomechPy Streamlit Apps

Interactive dashboards built on the `geomechpy` package. The apps contain **no
calculation logic of their own** — every number comes from the library; Streamlit and
Plotly only provide the interface.

## GeomechPy Dashboard (recommended starting point)

`geomechpy_dashboard.py` — a six-tab dashboard built entirely on the high-level API:
the physics runs through `MechanicalEarthModel` and the calculation classes, and every
chart comes from `geomechpy.plotting` with `backend="plotly"`.

- **Data Input** — the synthetic example well **or upload your own CSV / LAS logs**
  (with automatic column mapping to TVD / DTCO / DTSH / RHOB); table and CSV download.
- **Stress Model** — Pp / Shmin / SHmax / Sv metrics at TD and the interactive stress profile.
- **Stress Polygon** — the Zoback frictional-limit polygon at a chosen depth with the
  **faulting-regime identification** (normal / strike-slip / reverse) and q-factor.
- **Wellbore Stability** — the interactive mud weight window; toggle **borehole
  deviation & azimuth** on to overlay the deviated-well window and see it narrow or
  close relative to the vertical one.
- **Near-Wellbore Stresses** — the Kirsch **hoop / axial / radial** stresses around the
  borehole wall, driven live by deviation, azimuth and mud-weight sliders, marking where
  breakouts and drilling-induced tensile fractures initiate (teaching tool; the forward
  model behind LWD image interpretation).
- **Summary** — the multi-track MEM overview and full results CSV.

Sidebar: data source (example / upload), **unit system selector (field ft/psi/ppg or
metric m/MPa/SG)**, pore pressure gradient, Poisson's ratio multiplier, Biot
coefficient, Eaton vs poroelastic stress method, **well-trajectory toggle + deviation /
azimuth / SHmax-azimuth sliders**, planned mud weight.

> The far-field earth stresses (Pp, Sv, Shmin, SHmax) are trajectory-independent — only
> the near-wellbore response and the mud weight window change with deviation and azimuth.

## GeomechPy — 1D Mechanical Earth Model Dashboard (advanced)

`geomechpy_mem_dashboard.py` builds a complete 1D MEM interactively:

- **Data** — a synthetic well (configurable depth range and seed) or a manually
  editable log table (TVD, DTCO, DTSH, RHOB), with CSV download.
- **MEM Profile** — interactive multi-track depth plot (pressures & stresses, rock
  strength, elastic properties, input logs); pick tracks and toggle curves via the
  legend.
- **Mud Weight Window** — the kick / breakout / loss / breakdown limits in equivalent
  mud weight with the safe window shaded and your planned mud overlaid, plus status
  metrics.
- **Stability & Stress Polygon** — mud window vs borehole deviation at a chosen depth
  (including window closure in weak rock) and the Zoback stress polygon with a
  friction-coefficient slider.
- **Results** — the full computed model as a table with CSV download.

Sensitivity parameters (sidebar, live updates): pore pressure gradient (ppg),
dynamic→static calibration, Poisson's ratio multiplier, Shmin method
(Eaton / calibrated K0 / poroelastic with tectonic strains), Biot coefficient, SHmax
multiplier, tensile strength ratio, planned mud weight, borehole deviation/azimuth
and SHmax azimuth.

## Running

From the repository root:

```bash
pip install -e ".[streamlit,plotly,las]"
streamlit run examples/streamlit_apps/geomechpy_dashboard.py        # start here
streamlit run examples/streamlit_apps/geomechpy_mem_dashboard.py    # advanced version
```

Requires Python 3.10+ and Streamlit >= 1.40.
