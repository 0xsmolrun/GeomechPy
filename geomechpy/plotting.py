"""Publication-ready plots for 1D geomechanics workflows.

Provides the classic industry displays: the mud weight window, the multi-track
Mechanical Earth Model (MEM) profile, the stress polygon and elastic property logs.
Every function returns the matplotlib ``Figure`` so plots can be customized further
or saved (``figure.savefig(...)``), and accepts an existing ``Axes`` where a single
panel is drawn.

Curves may be plain ``list[float]``, numpy arrays or pandas Series - anything
matplotlib can plot. Depth axes are drawn increasing downwards, as is conventional
for well logs.

matplotlib is an optional dependency: it is only imported when a plotting function
is called. Install it with ``pip install geomechpy[plotting]`` or
``pip install matplotlib``."""

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


def plot_mud_weight_window(tvd: list[float], mud_weight_windows: list[MudWeightWindow], depth_unit: str = "ft", pressure_unit: str = "psi", as_mud_weight: bool = False, mud_weight_unit: str = "ppg", mud_pressure: list[float] | None = None, title: str = "Mud Weight Window", figsize: tuple[float, float] = (7.0, 9.0), ax=None):
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
        ax (matplotlib.axes.Axes | None): Existing axes to draw into. Defaults to None (new figure)

    Returns:
        matplotlib.figure.Figure: The figure containing the plot.

    Example:
        >>> windows = WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well_array(...)
        >>> figure = plot_mud_weight_window(tvd, windows, as_mud_weight=True)
        >>> figure.savefig("mud_weight_window.png", dpi=200)"""
    pyplot = _require_matplotlib()

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

    unit_label = mud_weight_unit if as_mud_weight else pressure_unit
    quantity_label = "Equivalent mud weight" if as_mud_weight else "Pressure"
    ax.set_xlabel(f"{quantity_label} [{unit_label}]")
    ax.set_ylabel(f"TVD [{depth_unit}]")
    ax.set_title(title)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.4)
    ax.legend(loc="best", fontsize=9)
    figure.tight_layout()

    return figure


def plot_mem_profile(tvd: list[float], tracks: dict[str, dict[str, list[float]]], track_units: dict[str, str] | None = None, depth_unit: str = "ft", title: str = "1D Mechanical Earth Model", figsize: tuple[float, float] | None = None):
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

    Returns:
        matplotlib.figure.Figure: The figure containing one axes per track.

    Example:
        >>> figure = plot_mem_profile(
        ...     tvd,
        ...     tracks={
        ...         "Pressures & Stresses": {"Pp": pore_pressure, "Sv": overburden, "Shmin": shmin},
        ...         "Rock Strength": {"UCS": ucs},
        ...     },
        ...     track_units={"Pressures & Stresses": "psi", "Rock Strength": "psi"},
        ... )"""
    pyplot = _require_matplotlib()

    if not tracks:
        raise ValueError("tracks must contain at least one track")
    track_units = track_units or {}

    n_tracks = len(tracks)
    if figsize is None:
        figsize = (3.0 * n_tracks, 9.0)
    figure, axes = pyplot.subplots(1, n_tracks, figsize=figsize, sharey=True)
    if n_tracks == 1:
        axes = [axes]

    for axis, (track_title, curves) in zip(axes, tracks.items(), strict=True):
        for label, values in curves.items():
            if len(values) != len(tvd):
                raise ValueError(f"curve '{label}' in track '{track_title}' does not match the length of tvd")
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


def plot_stress_polygon(shmin: float, shmax: float, overburden_stress: float, pore_pressure: float, friction_coefficient: float = 0.6, pressure_unit: str = "psi", title: str = "Stress Polygon", figsize: tuple[float, float] = (7.0, 7.0), ax=None):
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
        ax (matplotlib.axes.Axes | None): Existing axes to draw into. Defaults to None (new figure)

    Returns:
        matplotlib.figure.Figure: The figure containing the plot.

    Example:
        >>> figure = plot_stress_polygon(shmin=8000, shmax=9000, overburden_stress=10000, pore_pressure=4500)"""
    pyplot = _require_matplotlib()

    q = (math.sqrt(friction_coefficient**2 + 1) + friction_coefficient) ** 2
    shmin_frictional_limit = (overburden_stress - pore_pressure) / q + pore_pressure
    shmax_frictional_limit = q * (overburden_stress - pore_pressure) + pore_pressure

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


def plot_elastic_properties(tvd: list[float], elastic_properties: list, static_youngs_modulus: list[float] | None = None, modulus_unit: str = "Pa", depth_unit: str = "ft", title: str = "Elastic Properties", figsize: tuple[float, float] | None = None):
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

    return plot_mem_profile(tvd, tracks, track_units=track_units, depth_unit=depth_unit, title=title, figsize=figsize)
