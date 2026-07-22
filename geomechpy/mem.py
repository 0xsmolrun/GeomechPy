"""High-level 1D Mechanical Earth Model workflow.

`MechanicalEarthModel` orchestrates the individual GeomechPy calculation classes into
the standard MEM chain — dynamic elastic properties, static calibration, rock
strength, pore pressure, overburden, horizontal stresses and the mud weight window —
so a complete model can be built in a few chained calls:

    >>> mem = MechanicalEarthModel(
    ...     tvd=[8000.0, 9000.0, 10000.0],
    ...     dtco=[85.0, 80.0, 76.0],
    ...     dtsh=[150.0, 140.0, 132.0],
    ...     rhob=[2500.0, 2550.0, 2600.0],
    ... )
    >>> _ = (mem.calculate_elastic_properties()
    ...         .calculate_rock_strength()
    ...         .calculate_pore_pressure(gradient=9.0, gradient_unit="ppg")
    ...         .calculate_overburden()
    ...         .calculate_stresses()
    ...         .calculate_wellbore_stability())
    >>> window = mem.mud_weight_window[-1]
    >>> window.kick_pressure < window.loss_pressure
    True

Each step delegates to the corresponding calculation class (nothing is re-implemented
here) and stores its curves in `results`; `to_dataframe()` returns everything as a
depth-indexed pandas DataFrame. Inputs may be given in any supported unit; internally
the model works in field units (ft, psi) and all stored curves are in ft/psi/ppg."""

from geomechpy.dynamic_elastic_properties import DynamicElasticProperties, DynamicElasticPropertiesCalculation
from geomechpy.overburden_stress import OverburdenStressCalculation
from geomechpy.pore_pressure import PorePressureCalculation
from geomechpy.rock_strength import RockStrengthPropertiesConverter
from geomechpy.static_elastic_properties import StaticElasticPropertiesConverter
from geomechpy.stress_calculations import HorizontalStressesCalculation
from geomechpy.units import UnitConverter
from geomechpy.wellbore_stability import MudWeightWindow, WellboreStabilityCalculation

_STATIC_CALIBRATIONS = {
    "najibi": lambda values: StaticElasticPropertiesConverter.dyn2sta_yme_najib_array(values),
    "bradford": lambda values: StaticElasticPropertiesConverter.dyn2sta_yme_bradord_array(values),
    "fuller": lambda values: StaticElasticPropertiesConverter.dyn2sta_yme_fuller_array(values, modulus_unit="Mpsi"),
}


class MechanicalEarthModel:
    """Build a 1D Mechanical Earth Model from well logs in a few chained calls.

    The class is a thin orchestrator over the individual calculation classes
    (`DynamicElasticPropertiesCalculation`, `StaticElasticPropertiesConverter`,
    `RockStrengthPropertiesConverter`, `PorePressureCalculation`,
    `OverburdenStressCalculation`, `HorizontalStressesCalculation`,
    `WellboreStabilityCalculation`) — every number comes from those classes, and the
    individual classes remain available for finer control.

    Workflow order (each step depends on the previous ones and raises a descriptive
    RuntimeError when called too early):

        1. calculate_elastic_properties()  - dynamic moduli + static calibration
        2. calculate_rock_strength()       - UCS, tensile strength, friction angle
        3. calculate_pore_pressure()       - gradient / EMW based
        4. calculate_overburden()          - density-log integration (or gradient)
        5. calculate_stresses()            - Shmin/SHmax (Eaton, K0 or poroelastic)
        6. calculate_wellbore_stability()  - vertical-well mud weight window

    All computed curves are stored in the `results` dict (field units: psi, ft, ppg)
    and can be exported with `to_dataframe()`. The mud weight window entries are
    available as `mud_weight_window` (list of `MudWeightWindow`).

    Attributes:
        tvd (list[float]): True Vertical Depth samples. Unit: [ft]
        results (dict[str, list[float]]): All computed curves, one value per depth sample. Units: psi (pressures/stresses/strength), Mpsi (moduli), ppg (EMW columns), deg (friction angle)
        mud_weight_window (list[MudWeightWindow]): Window limits per depth, populated by `calculate_wellbore_stability`.

    Example:
        >>> mem = MechanicalEarthModel(tvd=[9000.0, 10000.0], dtco=[80.0, 76.0],
        ...                            dtsh=[140.0, 132.0], rhob=[2550.0, 2600.0])
        >>> mem = mem.calculate_all(pore_pressure_gradient=9.0, gradient_unit="ppg")
        >>> sorted(mem.results)[:3]
        ['breakdown_pressure', 'breakout_pressure', 'dyn_poissons_ratio']
        >>> print(f"{mem.results['emw_lower'][-1]:.1f} - {mem.results['emw_upper'][-1]:.1f} ppg")
        10.9 - 13.1 ppg"""

    def __init__(self, tvd: list[float], dtco: list[float], dtsh: list[float], rhob: list[float], depth_unit: str = "ft", slowness_unit: str = "us/ft", density_unit: str = "kg/m3"):
        """Create a model from depth-indexed well logs.

        Args:
            tvd (list[float]): True Vertical Depth samples, sorted in increasing order. Unit: [depth_unit]
            dtco (list[float]): Compressional slowness (DTCO log). Unit: [slowness_unit]
            dtsh (list[float]): Shear slowness (DTSH log). Unit: [slowness_unit]
            rhob (list[float]): Bulk density (RHOB log). Unit: [density_unit]
            depth_unit (str): Unit of the tvd input (e.g. "ft", "m"). Defaults to "ft"
            slowness_unit (str): Unit of the slowness inputs (e.g. "us/ft", "us/m"). Defaults to "us/ft"
            density_unit (str): Unit of the density input (e.g. "kg/m3", "g/cm3"). Defaults to "kg/m3"

        Raises:
            ValueError: If the logs have different lengths, fewer than two samples, or tvd is not sorted."""
        if not (len(tvd) == len(dtco) == len(dtsh) == len(rhob)):
            raise ValueError("tvd, dtco, dtsh and rhob must have the same length")
        if len(tvd) < 2:
            raise ValueError("at least two depth samples are required")

        self.tvd = UnitConverter.convert_depth_array(tvd, depth_unit, "ft")
        if any(later < earlier for earlier, later in zip(self.tvd, self.tvd[1:], strict=False)):
            raise ValueError("tvd must be sorted in increasing order")

        self.dtco = UnitConverter.convert_slowness_array(dtco, slowness_unit, "us/ft")
        self.dtsh = UnitConverter.convert_slowness_array(dtsh, slowness_unit, "us/ft")
        self.rhob = UnitConverter.convert_density_array(rhob, density_unit, "kg/m3")

        self.results: dict[str, list[float]] = {}
        self.dynamic_elastic_properties: list[DynamicElasticProperties] = []
        self.mud_weight_window: list[MudWeightWindow] = []

    def _require(self, columns: list[str], needed_for: str) -> None:
        """Raise a descriptive error when prerequisite curves have not been computed yet."""
        missing = [column for column in columns if column not in self.results]
        if missing:
            raise RuntimeError(f"{needed_for} requires {', '.join(missing)} - run the earlier workflow steps first (see class docstring for the order)")

    def calculate_elastic_properties(self, calibration: str = "najibi", poissons_ratio_multiplier: float = 1.0) -> "MechanicalEarthModel":
        """Compute dynamic elastic moduli from the logs and calibrate them to static values.

        Populates: dyn_youngs_modulus, dyn_poissons_ratio [Mpsi, -], sta_youngs_modulus,
        sta_poissons_ratio.

        Args:
            calibration (str): Dynamic-to-static Young's modulus correlation: "najibi" (carbonates), "bradford" (North Sea sandstones) or "fuller" (sandstone/shale). Defaults to "najibi"
            poissons_ratio_multiplier (float): Static/dynamic Poisson's ratio multiplier. Defaults to 1.0

        Returns:
            MechanicalEarthModel: self, for chaining."""
        if calibration not in _STATIC_CALIBRATIONS:
            raise ValueError(f"Unknown calibration '{calibration}'. Supported: {', '.join(sorted(_STATIC_CALIBRATIONS))}")

        self.dynamic_elastic_properties = DynamicElasticPropertiesCalculation.calculate_from_slowness_array(
            self.dtco, self.dtsh, self.rhob, modulus_unit="Mpsi"
        )
        self.results["dyn_youngs_modulus"] = [entry.youngs_modulus for entry in self.dynamic_elastic_properties]
        self.results["dyn_poissons_ratio"] = [entry.poissons_ratio for entry in self.dynamic_elastic_properties]
        self.results["sta_youngs_modulus"] = _STATIC_CALIBRATIONS[calibration](self.results["dyn_youngs_modulus"])
        self.results["sta_poissons_ratio"] = StaticElasticPropertiesConverter.dyn2sta_poissons_ratio_array(
            self.results["dyn_poissons_ratio"], multiplier=poissons_ratio_multiplier
        )
        return self

    def calculate_rock_strength(self, tensile_multiplier: float = 0.15) -> "MechanicalEarthModel":
        """Estimate UCS (Plumb), tensile strength and friction angle (Lal).

        Populates: ucs, tstr [psi], fang [deg].

        Args:
            tensile_multiplier (float): Tensile strength as a fraction of UCS. Defaults to 0.15

        Returns:
            MechanicalEarthModel: self, for chaining."""
        self._require(["sta_youngs_modulus"], "calculate_rock_strength")
        self.results["ucs"] = RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb_array(self.results["sta_youngs_modulus"])
        self.results["tstr"] = RockStrengthPropertiesConverter.convert_ucs_to_tstr_array(self.results["ucs"], multiplier=tensile_multiplier)
        self.results["fang"] = RockStrengthPropertiesConverter.convert_friction_angle_lal_array(self.dtco)
        return self

    def calculate_pore_pressure(self, gradient: float | None = None, gradient_unit: str | None = None, air_gap: float = 0.0, water_depth: float = 0.0) -> "MechanicalEarthModel":
        """Compute the pore pressure profile from a gradient (onshore or offshore).

        Populates: pore_pressure [psi].

        Args:
            gradient (float | None): Formation pore pressure gradient. Unit: [gradient_unit]. Defaults to the equivalent of 0.47 psi/ft
            gradient_unit (str | None): Gradient unit (e.g. "psi/ft", "kPa/m", "ppg", "SG"). Defaults to "psi/ft"
            air_gap (float): Drill floor elevation. Unit: [ft]. Defaults to 0.0
            water_depth (float): Water depth for offshore wells; 0 selects the onshore formulation. Unit: [ft]. Defaults to 0.0

        Returns:
            MechanicalEarthModel: self, for chaining."""
        if water_depth > 0:
            self.results["pore_pressure"] = PorePressureCalculation.calculate_pore_pressure_offshore_array(
                tvd=self.tvd, formation_pore_pressure_gradient=gradient, air_gap=air_gap, water_depth=water_depth, gradient_unit=gradient_unit
            )
        else:
            self.results["pore_pressure"] = PorePressureCalculation.calculate_pore_pressure_onshore_array(
                tvd=self.tvd, formation_pore_pressure_gradient=gradient, air_gap=air_gap, gradient_unit=gradient_unit
            )
        return self

    def calculate_overburden(self, air_gap: float = 0.0, water_depth: float = 0.0) -> "MechanicalEarthModel":
        """Compute the overburden stress profile by integrating the density log.

        Populates: overburden [psi].

        Args:
            air_gap (float): Drill floor elevation. Unit: [ft]. Defaults to 0.0
            water_depth (float): Water depth for offshore wells. Unit: [ft]. Defaults to 0.0

        Returns:
            MechanicalEarthModel: self, for chaining."""
        self.results["overburden"] = OverburdenStressCalculation.calculate_overburden_stress_from_density_array(
            tvd=self.tvd, density=self.rhob, air_gap=air_gap, water_depth=water_depth
        )
        return self

    def calculate_stresses(self, method: str = "eaton", shmax_multiplier: float = 1.05, biot_coefficient: float = 1.0, effective_stress_ratio: float = 0.75, strain_x: float = 0.0001, strain_y: float = 0.0004) -> "MechanicalEarthModel":
        """Compute the horizontal stress profiles.

        Populates: shmin, shmax [psi].

        Args:
            method (str): "eaton" (uniaxial strain), "k0" (calibrated effective stress ratio) or "poroelastic" (Thiercelin & Plumb, gives SHmax directly). Defaults to "eaton"
            shmax_multiplier (float): SHmax/Shmin anisotropy multiplier for the eaton and k0 methods. Defaults to 1.05
            biot_coefficient (float): Biot's coefficient. Defaults to 1.0
            effective_stress_ratio (float): K0 for the k0 method. Defaults to 0.75
            strain_x (float): Tectonic strain in the Shmin direction for the poroelastic method. Defaults to 0.0001
            strain_y (float): Tectonic strain in the SHmax direction for the poroelastic method. Defaults to 0.0004

        Returns:
            MechanicalEarthModel: self, for chaining."""
        self._require(["pore_pressure", "overburden", "sta_poissons_ratio"], "calculate_stresses")

        if method == "poroelastic":
            self._require(["sta_youngs_modulus"], "the poroelastic method")
            stresses = HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses_array(
                overburden_stress=self.results["overburden"], pore_pressure=self.results["pore_pressure"],
                poisson_ratio=self.results["sta_poissons_ratio"], youngs_modulus=self.results["sta_youngs_modulus"],
                biot_coefficient=[biot_coefficient] * len(self.tvd), EX=strain_x, EY=strain_y,
            )
            self.results["shmin"] = [entry.shmin for entry in stresses]
            self.results["shmax"] = [entry.shmax for entry in stresses]
        elif method == "k0":
            self.results["shmin"] = HorizontalStressesCalculation.calculate_shmin_effective_stress_ratio_array(
                overburden_stress=self.results["overburden"], pore_pressure=self.results["pore_pressure"],
                effective_stress_ratio=effective_stress_ratio, biot_coefficient=biot_coefficient,
            )
            self.results["shmax"] = HorizontalStressesCalculation.calculate_shmax_multiplier_array(self.results["shmin"], shmax_multiplier)
        elif method == "eaton":
            self.results["shmin"] = HorizontalStressesCalculation.calculate_shmin_eaton_array(
                overburden_stress=self.results["overburden"], pore_pressure=self.results["pore_pressure"],
                poisson_ratio=self.results["sta_poissons_ratio"], biot_coefficient=biot_coefficient,
            )
            self.results["shmax"] = HorizontalStressesCalculation.calculate_shmax_multiplier_array(self.results["shmin"], shmax_multiplier)
        else:
            raise ValueError(f"Unknown stress method '{method}'. Supported: eaton, k0, poroelastic")
        return self

    def calculate_wellbore_stability(self) -> "MechanicalEarthModel":
        """Compute the vertical-well mud weight window at every depth.

        Populates: kick_pressure, breakout_pressure, loss_pressure, breakdown_pressure
        [psi] plus emw_lower and emw_upper [ppg], and fills `mud_weight_window`.

        Returns:
            MechanicalEarthModel: self, for chaining."""
        self._require(["shmin", "shmax", "pore_pressure", "overburden", "ucs", "fang", "tstr"], "calculate_wellbore_stability")

        self.mud_weight_window = WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well_array(
            shmax=self.results["shmax"], shmin=self.results["shmin"], pprs=self.results["pore_pressure"],
            overburden_stress=self.results["overburden"], ucs=self.results["ucs"], fang=self.results["fang"],
            pr_sta=self.results["sta_poissons_ratio"], tstr=self.results["tstr"],
        )
        for column in ("kick_pressure", "breakout_pressure", "loss_pressure", "breakdown_pressure"):
            self.results[column] = [getattr(window, column) for window in self.mud_weight_window]

        lower = [max(window.kick_pressure, window.breakout_pressure) for window in self.mud_weight_window]
        upper = [min(window.loss_pressure, window.breakdown_pressure) for window in self.mud_weight_window]
        self.results["emw_lower"] = UnitConverter.convert_pressure_to_mud_weight_array(lower, self.tvd)
        self.results["emw_upper"] = UnitConverter.convert_pressure_to_mud_weight_array(upper, self.tvd)
        return self

    def calculate_all(self, calibration: str = "najibi", pore_pressure_gradient: float | None = None, gradient_unit: str | None = None, stress_method: str = "eaton", shmax_multiplier: float = 1.05, air_gap: float = 0.0, water_depth: float = 0.0) -> "MechanicalEarthModel":
        """Run the complete workflow with one call (using each step's defaults otherwise).

        Args:
            calibration (str): Dynamic-to-static calibration. Defaults to "najibi"
            pore_pressure_gradient (float | None): Pore pressure gradient. Unit: [gradient_unit]. Defaults to the equivalent of 0.47 psi/ft
            gradient_unit (str | None): Gradient unit (e.g. "psi/ft", "ppg"). Defaults to "psi/ft"
            stress_method (str): Horizontal stress method. Defaults to "eaton"
            shmax_multiplier (float): SHmax/Shmin multiplier. Defaults to 1.05
            air_gap (float): Drill floor elevation. Unit: [ft]. Defaults to 0.0
            water_depth (float): Water depth for offshore wells. Unit: [ft]. Defaults to 0.0

        Returns:
            MechanicalEarthModel: self, for chaining."""
        return (
            self.calculate_elastic_properties(calibration=calibration)
            .calculate_rock_strength()
            .calculate_pore_pressure(gradient=pore_pressure_gradient, gradient_unit=gradient_unit, air_gap=air_gap, water_depth=water_depth)
            .calculate_overburden(air_gap=air_gap, water_depth=water_depth)
            .calculate_stresses(method=stress_method, shmax_multiplier=shmax_multiplier)
            .calculate_wellbore_stability()
        )

    def to_dataframe(self):
        """Export the input logs and every computed curve as a depth-indexed pandas DataFrame.

        Returns:
            pandas.DataFrame: One row per depth sample, indexed by tvd [ft]; input logs first, then the computed curves in workflow order.

        Raises:
            ImportError: If pandas is not installed."""
        from geomechpy.dataframe_tools import _require_pandas

        pandas = _require_pandas()
        data = {"dtco": self.dtco, "dtsh": self.dtsh, "rhob": self.rhob, **self.results}
        return pandas.DataFrame(data, index=pandas.Index(self.tvd, name="tvd"))
