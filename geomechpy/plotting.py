"""Publication-ready plots for 1D geomechanics workflows.

Provides the classic industry displays: the mud weight window, the multi-track
Mechanical Earth Model (MEM) profile, the stress polygon and elastic property logs.
Every function returns the ``Figure`` so plots can be customized further or saved,
and accepts an existing matplotlib ``Axes`` where a single panel is drawn. Passing
``backend="plotly"`` returns an interactive Plotly figure with the same content
(hover values, zooming, legend toggling) instead of a matplotlib one.

Curves may be plain ``list[float]``, numpy arrays or pandas Series - anything
matplotlib can plot. Depth axes are drawn increasing downwards, as is conventional
for well logs.

matplotlib and plotly are optional dependencies, imported only when a plotting
function is called. Install them with ``pip install geomechpy[plotting]`` (matplotlib)
and/or ``pip install geomechpy[plotly]``."""

import math

from geomechpy.units import UnitConverter
from geomechpy.wellbore_stability import MudWeightWindow

SAFE_WINDOW_COLOR = "#8fd18f"
KICK_COLOR = "#1f77b4"
BREAKOUT_COLOR = "#d62728"
LOSS_COLOR = "#7f7f7f"
BREAKDOWN_COLOR = "#9467bd"


def _require_matplotlib():
    """Import matplotlib lazily, raising a descriptive error when it is not installed."""
    try:
        import matplotlib.pyplot as pyplot
    except ImportError as error:
        raise ImportError(
            "matplotlib is required for geomechpy.plotting. Install it with 'pip install matplotlib' or 'pip install geomechpy[plotting]'"
        ) from error
    return pyplot


def _require_plotly():
    """Import plotly lazily, raising a descriptive error when it is not installed."""
    try:
        import plotly.graph_objects as graph_objects
        from plotly.subplots import make_subplots
    except ImportError as error:
        raise ImportError(
            "plotly is required for backend='plotly'. Install it with 'pip install plotly' or 'pip install geomechpy[plotly]'"
        ) from error
    return graph_objects, make_subplots


def _check_backend(backend: str, ax) -> bool:
    """Validate the backend choice; returns True when the plotly path should be taken."""
    if backend == "plotly":
        if ax is not None:
            raise ValueError("the 'ax' argument only applies to the matplotlib backend")
        return True
    if backend != "matplotlib":
        raise ValueError(f"Unsupported backend '{backend}'. Supported backends: matplotlib, plotly")
    return False


def plot_mud_weight_window(tvd: list[float], mud_weight_windows: list[MudWeightWindow], depth_unit: str = "ft", pressure_unit: str = "psi", as_mud_weight: bool = False, mud_weight_unit: str = "ppg", mud_pressure: list[float] | None = None, title: str = "Mud Weight Window", figsize: tuple[float, float] = (7.0, 9.0), ax=None, backend: str = "matplotlib"):
    """Plot the classic mud weight window: the four operational limits vs depth with the safe window shaded.

    The lower bound of the safe window is max(kick, breakout) and the upper bound is
    min(loss, breakdown); the area between them is shaded green. Limits can be shown
    as pressures or converted to equivalent mud weight (EMW) at each depth.

    Args:
        tvd (list[float]): True Vertical Depth values, one per window. Unit: [depth_unit]
        mud_weight_windows (list[MudWeightWindow]): Window limits per depth, e.g. from `WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well_array`. Unit: [pressure_unit]
        depth_unit (str): Unit of the tvd values, used for axis labelling and EMW conversion. Defaults to "ft"
        pressure_unit (str): Unit of the window pressures. Defaults to "psi"
        as_mud_weight (bool): If True, convert all limits to equivalent mud weight at each depth. Defaults to False
        mud_weight_unit (str): EMW unit when as_mud_weight is True (e.g. "ppg", "SG"). Defaults to "ppg"
        mud_pressure (list[float] | None): Optional planned mud pressure per depth to overlay. Unit: [pressure_unit]. Defaults to None
        title (str): Figure title. Defaults to "Mud Weight Window"
        figsize (tuple[float, float]): Figure size in inches when a new figure is created. Defaults to (7, 9)
        ax (matplotlib.axes.Axes | None): Existing axes to draw into (matplotlib backend only). Defaults to None (new figure)
        backend (str): "matplotlib" (default) or "plotly" for an interactive figure.

    Returns:
        matplotlib.figure.Figure | plotly.graph_objects.Figure: The figure containing the plot.

    Example:
        >>> windows = WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well_array(...)
        >>> figure = plot_mud_weight_window(tvd, windows, as_mud_weight=True)
        >>> figure.savefig("mud_weight_window.png", dpi=200)"""
    if len(tvd) != len(mud_weight_windows):
        raise ValueError("tvd and mud_weight_windows must have the same length")

    def _limit(values: list[float]) -> list[float]:
        if not as_mud_weight:
            return values
        return [
            UnitConverter.convert_pressure_to_mud_weight(value, depth, pressure_unit=pressure_unit, depth_unit=depth_unit, mud_weight_unit=mud_weight_unit)
            for value, depth in zip(values, tvd, strict=True)
        ]

    kick = _limit([window.kick_pressure for window in mud_weight_windows])
    breakout = _limit([window.breakout_pressure for window in mud_weight_windows])
    loss = _limit([window.loss_pressure for window in mud_weight_windows])
    breakdown = _limit([window.breakdown_pressure for window in mud_weight_windows])
    lower = [max(k, b) for k, b in zip(kick, breakout, strict=True)]
    upper = [min(lo, bd) for lo, bd in zip(loss, breakdown, strict=True)]

    unit_label = mud_weight_unit if as_mud_weight else pressure_unit
    quantity_label = "Equivalent mud weight" if as_mud_weight else "Pressure"

    if _check_backend(backend, ax):
        return _mud_weight_window_plotly(
            tvd, kick, breakout, loss, breakdown, lower, upper,
            _limit(mud_pressure) if mud_pressure is not None else None,
            quantity_label, unit_label, depth_unit, title, figsize,
        )

    pyplot = _require_matplotlib()
    if ax is None:
        figure, ax = pyplot.subplots(figsize=figsize)
    else:
        figure = ax.figure

    ax.fill_betweenx(tvd, lower, upper, where=[u > lo for lo, u in zip(lower, upper, strict=True)], color=SAFE_WINDOW_COLOR, alpha=0.5, label="Safe window")
    ax.plot(kick, tvd, color=KICK_COLOR, label="Pore pressure (kick)")
    ax.plot(breakout, tvd, color=BREAKOUT_COLOR, label="Breakout")
    ax.plot(loss, tvd, color=LOSS_COLOR, linestyle="--", label="Shmin (losses)")
    ax.plot(breakdown, tvd, color=BREAKDOWN_COLOR, label="Breakdown")
    if mud_pressure is not None:
        ax.plot(_limit(mud_pressure), tvd, color="black", linestyle=":", linewidth=2, label="Mud pressure")

    ax.set_xlabel(f"{quantity_label} [{unit_label}]")
    ax.set_ylabel(f"TVD [{depth_unit}]")
    ax.set_title(title)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.4)
    ax.legend(loc="best", fontsize=9)
    figure.tight_layout()

    return figure


def plot_mem_profile(tvd: list[float], tracks: dict[str, dict[str, list[float]]], track_units: dict[str, str] | None = None, depth_unit: str = "ft", title: str = "1D Mechanical Earth Model", figsize: tuple[float, float] | None = None, backend: str = "matplotlib"):
    """Plot a multi-track Mechanical Earth Model profile, one panel per track sharing the depth axis.

    Each track holds one or more named curves plotted against depth, in the style of
    industry MEM composite displays (pore pressure and stresses, elastic properties,
    rock strength, ...). Curves may be lists, numpy arrays or pandas Series.

    Args:
        tvd (list[float]): True Vertical Depth values shared by all curves. Unit: [depth_unit]
        tracks (dict[str, dict[str, list[float]]]): Mapping of track title to {curve label: values}. Tracks are drawn left to right in insertion order.
        track_units (dict[str, str] | None): Optional mapping of track title to the unit shown on its x-axis label. Defaults to None
        depth_unit (str): Unit of the tvd values. Defaults to "ft"
        title (str): Figure title. Defaults to "1D Mechanical Earth Model"
        figsize (tuple[float, float] | None): Figure size in inches. Defaults to (3 per track, 9)
        backend (str): "matplotlib" (default) or "plotly" for an interactive figure.

    Returns:
        matplotlib.figure.Figure | plotly.graph_objects.Figure: The figure containing one panel per track.

    Example:
        >>> figure = plot_mem_profile(
        ...     tvd,
        ...     tracks={
        ...         "Pressures & Stresses": {"Pp": pore_pressure, "Sv": overburden, "Shmin": shmin},
        ...         "Rock Strength": {"UCS": ucs},
        ...     },
        ...     track_units={"Pressures & Stresses": "psi", "Rock Strength": "psi"},
        ... )"""
    if not tracks:
        raise ValueError("tracks must contain at least one track")
    track_units = track_units or {}
    for track_title, curves in tracks.items():
        for label, values in curves.items():
            if len(values) != len(tvd):
                raise ValueError(f"curve '{label}' in track '{track_title}' does not match the length of tvd")

    n_tracks = len(tracks)
    if figsize is None:
        figsize = (3.0 * n_tracks, 9.0)

    if _check_backend(backend, None):
        return _mem_profile_plotly(tvd, tracks, track_units, depth_unit, title, figsize)

    pyplot = _require_matplotlib()
    figure, axes = pyplot.subplots(1, n_tracks, figsize=figsize, sharey=True)
    if n_tracks == 1:
        axes = [axes]

    for axis, (track_title, curves) in zip(axes, tracks.items(), strict=True):
        for label, values in curves.items():
            axis.plot(values, tvd, label=label)
        unit = track_units.get(track_title)
        axis.set_xlabel(f"{track_title} [{unit}]" if unit else track_title)
        axis.grid(True, alpha=0.4)
        axis.legend(loc="best", fontsize=8)

    axes[0].set_ylabel(f"TVD [{depth_unit}]")
    axes[0].invert_yaxis()
    figure.suptitle(title)
    figure.tight_layout()

    return figure


def plot_stress_polygon(shmin: float, shmax: float, overburden_stress: float, pore_pressure: float, friction_coefficient: float = 0.6, pressure_unit: str = "psi", title: str = "Stress Polygon", figsize: tuple[float, float] = (7.0, 7.0), ax=None, backend: str = "matplotlib"):
    """Plot the Zoback stress polygon and the current stress state relative to the faulting regimes.

    The polygon bounds the horizontal stresses allowed by frictional equilibrium on
    optimally oriented faults with friction coefficient mu: the effective stress ratio
    is limited to q = (sqrt(mu^2 + 1) + mu)^2. Regions for normal (NF), strike-slip
    (SS) and reverse (RF) faulting are separated by the Shmin = Sv and SHmax = Sv
    lines, and the input stress state is marked.

    Reference: Zoback, Mark D. Reservoir geomechanics. Cambridge University Press, 2010; Chapter 4.

    Args:
        shmin (float): Minimum horizontal stress magnitude. Unit: [pressure_unit]
        shmax (float): Maximum horizontal stress magnitude. Unit: [pressure_unit]
        overburden_stress (float): Overburden (vertical) stress magnitude. Unit: [pressure_unit]
        pore_pressure (float): Pore pressure magnitude. Unit: [pressure_unit]
        friction_coefficient (float): Fault friction coefficient mu. Defaults to 0.6 (Byerlee)
        pressure_unit (str): Unit used for the axis labels. Defaults to "psi"
        title (str): Figure title. Defaults to "Stress Polygon"
        figsize (tuple[float, float]): Figure size in inches when a new figure is created. Defaults to (7, 7)
        ax (matplotlib.axes.Axes | None): Existing axes to draw into (matplotlib backend only). Defaults to None (new figure)
        backend (str): "matplotlib" (default) or "plotly" for an interactive figure.

    Returns:
        matplotlib.figure.Figure | plotly.graph_objects.Figure: The figure containing the plot.

    Example:
        >>> figure = plot_stress_polygon(shmin=8000, shmax=9000, overburden_stress=10000, pore_pressure=4500)"""
    q = (math.sqrt(friction_coefficient**2 + 1) + friction_coefficient) ** 2
    shmin_frictional_limit = (overburden_stress - pore_pressure) / q + pore_pressure
    shmax_frictional_limit = q * (overburden_stress - pore_pressure) + pore_pressure

    if _check_backend(backend, ax):
        return _stress_polygon_plotly(
            shmin, shmax, overburden_stress, q, shmin_frictional_limit, shmax_frictional_limit,
            friction_coefficient, pore_pressure, pressure_unit, title, figsize,
        )

    pyplot = _require_matplotlib()
    if ax is None:
        figure, ax = pyplot.subplots(figsize=figsize)
    else:
        figure = ax.figure

    # Polygon vertices: (Sh_low, Sh_low) on the diagonal, up the NF limit to the SS
    # frictional line at (Sh_low, Sv), along the SS line to (Sv, SH_high), across the
    # RF limit to (SH_high, SH_high), and back down the SHmax = Shmin diagonal
    polygon_shmin = [shmin_frictional_limit, shmin_frictional_limit, overburden_stress, shmax_frictional_limit, shmin_frictional_limit]
    polygon_shmax = [shmin_frictional_limit, q * (shmin_frictional_limit - pore_pressure) + pore_pressure, shmax_frictional_limit, shmax_frictional_limit, shmin_frictional_limit]
    ax.plot(polygon_shmin, polygon_shmax, color="black", linewidth=1.5, label=f"Frictional limits (mu = {friction_coefficient})")

    # Regime separators inside the polygon
    ax.plot([shmin_frictional_limit, overburden_stress], [overburden_stress, overburden_stress], color="gray", linestyle="--", linewidth=1)
    ax.plot([overburden_stress, overburden_stress], [overburden_stress, shmax_frictional_limit], color="gray", linestyle="--", linewidth=1)

    # Regime annotations at the centroid of each region
    ax.annotate("NF", ((shmin_frictional_limit + overburden_stress) / 2, (shmin_frictional_limit + overburden_stress) / 2 + 0.08 * (shmax_frictional_limit - shmin_frictional_limit)), color="gray", fontsize=11, ha="center")
    ax.annotate("SS", ((shmin_frictional_limit + overburden_stress) / 2, (overburden_stress + shmax_frictional_limit) / 2), color="gray", fontsize=11, ha="center")
    ax.annotate("RF", ((overburden_stress + shmax_frictional_limit) / 2, (overburden_stress + shmax_frictional_limit) / 2 + 0.05 * (shmax_frictional_limit - shmin_frictional_limit)), color="gray", fontsize=11, ha="center")

    ax.plot([shmin], [shmax], marker="*", markersize=16, color=BREAKOUT_COLOR, linestyle="none", label="Stress state")

    ax.set_xlabel(f"Shmin [{pressure_unit}]")
    ax.set_ylabel(f"SHmax [{pressure_unit}]")
    ax.set_title(title)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.4)
    ax.legend(loc="upper left", fontsize=9)
    figure.tight_layout()

    return figure


def plot_elastic_properties(tvd: list[float], elastic_properties: list, static_youngs_modulus: list[float] | None = None, modulus_unit: str = "Pa", depth_unit: str = "ft", title: str = "Elastic Properties", figsize: tuple[float, float] | None = None, backend: str = "matplotlib"):
    """Plot elastic properties vs depth: Young's modulus (dynamic, with optional static overlay), Poisson's ratio and Vp/Vs.

    Accepts the result dataclasses produced by the library (`ElasticProperties` or
    `DynamicElasticProperties`); the Vp/Vs track is added automatically when the
    entries carry a `vp_vs_ratio` field.

    Args:
        tvd (list[float]): True Vertical Depth values, one per entry. Unit: [depth_unit]
        elastic_properties (list): `ElasticProperties` or `DynamicElasticProperties` entries, e.g. from `DynamicElasticPropertiesCalculation.calculate_from_slowness_array`.
        static_youngs_modulus (list[float] | None): Optional static Young's modulus values to overlay on the modulus track. Unit: [modulus_unit]. Defaults to None
        modulus_unit (str): Unit of the moduli, used for axis labelling. Defaults to "Pa"
        depth_unit (str): Unit of the tvd values. Defaults to "ft"
        title (str): Figure title. Defaults to "Elastic Properties"
        figsize (tuple[float, float] | None): Figure size in inches. Defaults to (3 per track, 9)

    Returns:
        matplotlib.figure.Figure: The figure containing one axes per track.

    Example:
        >>> dynamic = DynamicElasticPropertiesCalculation.calculate_from_slowness_array(dtco, dtsh, rhob, modulus_unit="GPa")
        >>> figure = plot_elastic_properties(tvd, dynamic, modulus_unit="GPa")"""
    if len(tvd) != len(elastic_properties):
        raise ValueError("tvd and elastic_properties must have the same length")

    youngs_modulus = [entry.youngs_modulus for entry in elastic_properties]
    poissons_ratio = [entry.poissons_ratio for entry in elastic_properties]

    modulus_curves: dict[str, list[float]] = {"E dynamic": youngs_modulus}
    if static_youngs_modulus is not None:
        modulus_curves["E static"] = static_youngs_modulus

    tracks: dict[str, dict[str, list[float]]] = {
        "Young's modulus": modulus_curves,
        "Poisson's ratio": {"PR dynamic": poissons_ratio},
    }
    track_units = {"Young's modulus": modulus_unit}

    if all(hasattr(entry, "vp_vs_ratio") for entry in elastic_properties):
        tracks["Vp/Vs"] = {"Vp/Vs": [entry.vp_vs_ratio for entry in elastic_properties]}

    return plot_mem_profile(tvd, tracks, track_units=track_units, depth_unit=depth_unit, title=title, figsize=figsize, backend=backend)


def _mud_weight_window_plotly(tvd, kick, breakout, loss, breakdown, lower, upper, mud_pressure, quantity_label, unit_label, depth_unit, title, figsize):
    """Interactive Plotly variant of the mud weight window plot."""
    graph_objects, _ = _require_plotly()

    figure = graph_objects.Figure()
    figure.add_trace(graph_objects.Scatter(x=lower, y=tvd, line={"width": 0}, showlegend=False, hoverinfo="skip"))
    figure.add_trace(graph_objects.Scatter(x=upper, y=tvd, name="Safe window", fill="tonextx", fillcolor="rgba(143, 209, 143, 0.4)", line={"width": 0}))
    for label, values, color, dash in [
        ("Pore pressure (kick)", kick, KICK_COLOR, "solid"),
        ("Breakout", breakout, BREAKOUT_COLOR, "solid"),
        ("Shmin (losses)", loss, LOSS_COLOR, "dash"),
        ("Breakdown", breakdown, BREAKDOWN_COLOR, "solid"),
    ]:
        figure.add_trace(graph_objects.Scatter(x=values, y=tvd, name=label, line={"color": color, "dash": dash}))
    if mud_pressure is not None:
        figure.add_trace(graph_objects.Scatter(x=mud_pressure, y=tvd, name="Mud pressure", line={"color": "black", "dash": "dot", "width": 3}))

    figure.update_yaxes(autorange="reversed", title_text=f"TVD [{depth_unit}]")
    figure.update_xaxes(title_text=f"{quantity_label} [{unit_label}]")
    figure.update_layout(title=title, width=int(figsize[0] * 80), height=int(figsize[1] * 80), legend={"orientation": "h", "y": -0.12})
    return figure


def _mem_profile_plotly(tvd, tracks, track_units, depth_unit, title, figsize):
    """Interactive Plotly variant of the multi-track MEM profile."""
    graph_objects, make_subplots = _require_plotly()

    subplot_titles = [
        f"{track_title} [{track_units[track_title]}]" if track_title in track_units else track_title
        for track_title in tracks
    ]
    figure = make_subplots(rows=1, cols=len(tracks), shared_yaxes=True, subplot_titles=subplot_titles, horizontal_spacing=0.04)
    for column_index, (track_title, curves) in enumerate(tracks.items(), start=1):
        for label, values in curves.items():
            figure.add_trace(
                graph_objects.Scatter(x=values, y=tvd, name=label, mode="lines", legendgroup=label),
                row=1, col=column_index,
            )
    figure.update_yaxes(autorange="reversed", title_text=f"TVD [{depth_unit}]", row=1, col=1)
    figure.update_layout(title=title, width=int(figsize[0] * 80), height=int(figsize[1] * 80), legend={"orientation": "h", "y": -0.1})
    return figure


def _stress_polygon_plotly(shmin, shmax, overburden_stress, q, shmin_frictional_limit, shmax_frictional_limit, friction_coefficient, pore_pressure, pressure_unit, title, figsize):
    """Interactive Plotly variant of the stress polygon."""
    graph_objects, _ = _require_plotly()

    polygon_shmin = [shmin_frictional_limit, shmin_frictional_limit, overburden_stress, shmax_frictional_limit, shmin_frictional_limit]
    polygon_shmax = [shmin_frictional_limit, q * (shmin_frictional_limit - pore_pressure) + pore_pressure, shmax_frictional_limit, shmax_frictional_limit, shmin_frictional_limit]

    figure = graph_objects.Figure()
    figure.add_trace(graph_objects.Scatter(x=polygon_shmin, y=polygon_shmax, name=f"Frictional limits (mu = {friction_coefficient})", line={"color": "black"}))
    figure.add_trace(graph_objects.Scatter(x=[shmin_frictional_limit, overburden_stress], y=[overburden_stress, overburden_stress], mode="lines", line={"color": "gray", "dash": "dash"}, showlegend=False))
    figure.add_trace(graph_objects.Scatter(x=[overburden_stress, overburden_stress], y=[overburden_stress, shmax_frictional_limit], mode="lines", line={"color": "gray", "dash": "dash"}, showlegend=False))
    figure.add_trace(graph_objects.Scatter(x=[shmin], y=[shmax], mode="markers", name="Stress state", marker={"symbol": "star", "size": 16, "color": BREAKOUT_COLOR}))
    for text, x, y in [
        ("NF", (shmin_frictional_limit + overburden_stress) / 2, (shmin_frictional_limit + overburden_stress) / 2 + 0.08 * (shmax_frictional_limit - shmin_frictional_limit)),
        ("SS", (shmin_frictional_limit + overburden_stress) / 2, (overburden_stress + shmax_frictional_limit) / 2),
        ("RF", (overburden_stress + shmax_frictional_limit) / 2, (overburden_stress + shmax_frictional_limit) / 2 + 0.05 * (shmax_frictional_limit - shmin_frictional_limit)),
    ]:
        figure.add_annotation(x=x, y=y, text=text, showarrow=False, font={"color": "gray", "size": 14})

    figure.update_xaxes(title_text=f"Shmin [{pressure_unit}]")
    figure.update_yaxes(title_text=f"SHmax [{pressure_unit}]", scaleanchor="x", scaleratio=1)
    figure.update_layout(title=title, width=int(figsize[0] * 80), height=int(figsize[1] * 80), legend={"orientation": "h", "y": -0.15})
    return figure
