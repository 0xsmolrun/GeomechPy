# GeomechPy example

A tiny, self-contained demo that runs a few `geomechpy` functions on a
hardcoded well log and saves charts. No coding or inputs required.

## Run it

1. Install the chart library once:

   ```bash
   pip install -r examples/requirements.txt
   ```

2. In VS Code, open `examples/main.py` and press **Run and Debug** (F5),
   choosing **"Run GeomechPy example (make charts)"**.

   (Or from a terminal at the repo root: `python examples/main.py`.)

## What you get

Three charts are written to `examples/outputs/`:

- `01_input_logs.png` — the input well logs (sonic, density, porosity)
- `02_rock_properties.png` — Young's modulus (dynamic vs static) and UCS
- `03_mud_weight_window.png` — the safe drilling mud-weight window

## Want to pause and look at the numbers?

Click in the left margin of `examples/main.py` next to any `STEP ...` line to
add a red breakpoint, then press F5. Execution pauses there so you can hover
over variables (e.g. `overburden`, `shmin`) to inspect the values.
