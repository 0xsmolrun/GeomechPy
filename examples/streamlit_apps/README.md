# GeomechPy Streamlit Apps

Interactive dashboards built on the `geomechpy` package. The apps contain **no
calculation logic of their own** — every number comes from the library; Streamlit and
Plotly only provide the interface.

## GeomechPy — 1D Mechanical Earth Model Dashboard

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
pip install -e ".[streamlit,plotly]"
streamlit run examples/streamlit_apps/geomechpy_mem_dashboard.py
```

Requires Python 3.10+ and Streamlit >= 1.30.
