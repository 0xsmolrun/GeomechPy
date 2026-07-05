import math
from dataclasses import dataclass

import numpy as np

from geomechpy.near_wellbore_stresses import NearWellboreStressesCalculation


@dataclass(frozen=True)
class MudWeightWindow:
    """Mud pressure limits bounding the safe drilling window at a given depth.

    The safe window for the static mud pressure is
    max(kick_pressure, breakout_pressure) < Pw < min(loss_pressure, breakdown_pressure).

    Attributes:
        kick_pressure (float): Pore pressure - drilling below it risks a formation fluid influx (kick). Unit: Pressure
        breakout_pressure (float): Shear failure (breakout) limit - drilling below it risks hole collapse. Unit: Pressure
        loss_pressure (float): Minimum horizontal stress - drilling above it risks mud losses into natural or reopened fractures. Unit: Pressure
        breakdown_pressure (float): Fracture initiation (breakdown) limit - drilling above it risks creating hydraulic fractures. Unit: Pressure"""

    kick_pressure: float
    breakout_pressure: float
    loss_pressure: float
    breakdown_pressure: float


class WellboreStabilityCalculation:
    """Compute the shear failure and tensile failure limits for a vertical well using the Mohr-Coulomb failure criterion using analytical solution

    All methods are unit-agnostic with respect to pressure: stresses, pore pressure and
    rock strength may be given in any consistent pressure unit (psi, kPa, MPa, ...) and
    the resulting limits are returned in that same unit. Use `geomechpy.units.UnitConverter`
    (e.g. `convert_pressure_to_mud_weight`) to express the results as an equivalent mud weight.

    Reference:
    Jaeger, John Conrad, Neville GW Cook, and Robert Zimmerman. Fundamentals of rock mechanics. John Wiley & Sons, 2009.
    Al-Ajmi, Adel M., and Robert W. Zimmerman. "Stability analysis of vertical boreholes using the Mogi–Coulomb failure criterion." International journal of rock mechanics and mining sciences 43.8 (2006): 1200-1211.

    """

    @staticmethod
    def calculate_breakdown_calculation_vertical_well_analytical(shmax: float, shmin: float, pprs: float, tstr: float) -> float:
        """
        Calculate the breakdown pressure (fracture initiation pressure) for a vertical well

        Applicable for: Generic.

        Reference: Jaeger, John Conrad, Neville GW Cook, and Robert Zimmerman. Fundamentals of rock mechanics. John Wiley & Sons, 2009, pp. 158-159.
        Hubbert, M. King, and David G. Willis. "Mechanics of hydraulic fracturing." Transactions of the AIME 210.01 (1957): 153-168.

        Args:
           shmax (float): Maximum horizontal stress magnitude. Unit: any consistent pressure unit
           shmin (float): Minimum horizontal stress magnitude. Unit: same pressure unit
           pprs (float): Pore pressure. Unit: same pressure unit
           tstr (float): Tensile rock strength. Unit: same pressure unit

        Returns:
           pw_breakdown (float): Breakdown (fracture initiation) pressure. Unit: same pressure unit as the inputs
        """

        pw_breakdown = 3 * shmin - shmax - pprs + tstr

        return float(pw_breakdown)

    @staticmethod
    def calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(shmax: float, shmin: float, pprs: float, overburden_stress: float, ucs: float, fang: float, pr_sta: float) -> float:
        """
        Calculate the breakout pressure (shear failure) for a vertical well using the Mohr Coulomb failure criterion
        Mohr-Coulomb criterion is evaluated analytically for three scenarios using the Kirsch equation for a vertical well on the borehole wall:
        z>t>r: axial stress > tangential stress > radial stress
        t>z>r: tangential stress > axial stress > radial stress
        t>r>z: tangential stress > radial stress > axial stress
        The maximum value of those three scenarios is selected to be the onset of shear failure on the borehole wall

        Applicable for: Generic.

        Reference: Jaeger, John Conrad, Neville GW Cook, and Robert Zimmerman. Fundamentals of rock mechanics. John Wiley & Sons, 2009, pp. 158-159.
        Al-Ajmi, Adel M., and Robert W. Zimmerman. "Stability analysis of vertical boreholes using the Mogi-Coulomb failure criterion." International journal of rock mechanics and mining sciences 43.8 (2006): 1200-1211.

        Args:
           shmax (float): Maximum horizontal stress magnitude. Unit: any consistent pressure unit
           shmin (float): Minimum horizontal stress magnitude. Unit: same pressure unit
           pprs (float): Pore pressure. Unit: same pressure unit
           overburden_stress (float): Overburden (vertical) stress magnitude. Unit: same pressure unit
           ucs (float): Unconfined compressive strength. Unit: same pressure unit
           fang (float): Internal friction angle. Unit: [dega]
           pr_sta (float): Static Poisson's ratio. Unit: unitless

        Returns:
           pw_breakout (float): Breakout (shear failure) pressure. Unit: same pressure unit as the inputs
        """
        q = math.tan(math.radians(45) + math.radians(fang / 2)) ** 2
        CC = ucs - pprs * (q - 1)

        A = 3 * shmax - shmin
        B = overburden_stress + 2 * pr_sta * (shmax - shmin)

        Pw_z_t_r = (B - CC) / q
        Pw_t_z_r = (A - CC) / (1 + q)
        Pw_t_r_z = A - CC - q * B

        pw_breakout = max(Pw_z_t_r, Pw_t_z_r, Pw_t_r_z)

        return float(pw_breakout)

    @staticmethod
    def calculate_breakdown_calculation_vertical_well_analytical_array(shmax: list[float], shmin: list[float], pprs: list[float], tstr: list[float]) -> list[float]:
        """
        Calculate the breakdown pressure for a vertical well across arrays of inputs.

        Args:
           shmax (list[float]): Maximum horizontal stress values. Unit: any consistent pressure unit
           shmin (list[float]): Minimum horizontal stress values. Unit: same pressure unit
           pprs (list[float]): Pore pressure values. Unit: same pressure unit
           tstr (list[float]): Tensile rock strength values. Unit: same pressure unit

        Returns:
           pw_breakdown (list[float]): Breakdown pressure values. Unit: same pressure unit as the inputs
        """
        return [
            WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical(
                shmax=sx,
                shmin=sn,
                pprs=pp,
                tstr=ts,
            )
            for sx, sn, pp, ts in zip(shmax, shmin, pprs, tstr, strict=True)
        ]

    @staticmethod
    def calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical_array(shmax: list[float], shmin: list[float], pprs: list[float], overburden_stress: list[float], ucs: list[float], fang: list[float], pr_sta: list[float]) -> list[float]:
        """
        Calculate the breakout pressure for a vertical well across arrays of inputs using the Mohr-Coulomb failure criterion.

        Args:
           shmax (list[float]): Maximum horizontal stress values. Unit: any consistent pressure unit
           shmin (list[float]): Minimum horizontal stress values. Unit: same pressure unit
           pprs (list[float]): Pore pressure values. Unit: same pressure unit
           overburden_stress (list[float]): Overburden stress values. Unit: same pressure unit
           ucs (list[float]): Unconfined compressive strength values. Unit: same pressure unit
           fang (list[float]): Internal friction angle values. Unit: [dega]
           pr_sta (list[float]): Static Poisson's ratio values. Unit: unitless

        Returns:
           pw_breakout (list[float]): Breakout pressure values. Unit: same pressure unit as the inputs
        """
        return [
            WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(
                shmax=sx,
                shmin=sn,
                pprs=pp,
                overburden_stress=ovb,
                ucs=uc,
                fang=fa,
                pr_sta=pr,
            )
            for sx, sn, pp, ovb, uc, fa, pr in zip(shmax, shmin, pprs, overburden_stress, ucs, fang, pr_sta, strict=True)
        ]

    @staticmethod
    def _borehole_wall_extreme_principal_stresses(shmax: float, shmin: float, overburden_stress: float, pprs: float, mud_pressure: float, pr_sta: float, borehole_deviation: float, borehole_azimuth: float, shmax_azimuth: float, n_theta: int):
        """Compute the maximum and minimum effective principal stresses around the borehole wall.

        Evaluates the Kirsch solution at n_theta azimuthal positions and combines the two
        in-plane principal stresses (from sigma_tt, sigma_zz, sigma_tz) with the radial
        stress to obtain the extreme principal stresses at each position."""
        theta = np.linspace(0.0, 360.0, n_theta)
        wall = NearWellboreStressesCalculation.calculate_kirsch_borehole_wall_stresses(
            shmin=shmin,
            shmax=shmax,
            svert=overburden_stress,
            pore_pressure=pprs,
            shmax_azimuth=shmax_azimuth,
            mud_pressure=mud_pressure,
            theta=theta,
            poisson_ratio_static=pr_sta,
            borehole_deviation=borehole_deviation,
            borehole_azimuth=borehole_azimuth,
        )
        mean_stress = 0.5 * (wall.sigma_tt + wall.sigma_zz)
        stress_radius = np.sqrt((0.5 * (wall.sigma_tt - wall.sigma_zz)) ** 2 + wall.sigma_tz**2)
        in_plane_max = mean_stress + stress_radius
        in_plane_min = mean_stress - stress_radius

        sigma_1 = np.maximum(in_plane_max, wall.sigma_rr)
        sigma_3 = np.minimum(in_plane_min, wall.sigma_rr)
        return sigma_1, sigma_3

    @staticmethod
    def calculate_breakout_pressure_deviated_well_mohr_coulomb(shmax: float, shmin: float, overburden_stress: float, pprs: float, ucs: float, fang: float, pr_sta: float, borehole_deviation: float, borehole_azimuth: float, shmax_azimuth: float = 0.0, n_theta: int = 181) -> float:
        """
        Calculate the breakout pressure (shear failure limit) for a deviated or inclined well
        using the Mohr-Coulomb failure criterion evaluated numerically on the borehole wall.

        The full stress tensor is rotated into the borehole frame, the Kirsch solution gives
        the effective wall stresses at n_theta azimuthal positions, and the minimum mud
        pressure at which no point on the wall violates sigma_1' = q*sigma_3' + UCS is found
        by bisection (the shear failure excess is convex in the mud pressure). For a vertical
        well this reproduces the analytical solution of
        `calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical`.

        Unit-agnostic with respect to pressure: any consistent pressure unit.

        Reference: Fjaer, Erling, et al. Petroleum related rock mechanics. Vol. 53. Elsevier, 2008; Chapter 4.
        Zoback, Mark D. Reservoir geomechanics. Cambridge University Press, 2010; Chapter 8 (wellbore stability of deviated wells).

        Args:
           shmax (float): Maximum horizontal stress magnitude. Unit: any consistent pressure unit
           shmin (float): Minimum horizontal stress magnitude. Unit: same pressure unit
           overburden_stress (float): Overburden (vertical) stress magnitude. Unit: same pressure unit
           pprs (float): Pore pressure. Unit: same pressure unit
           ucs (float): Unconfined compressive strength. Unit: same pressure unit
           fang (float): Internal friction angle. Unit: [dega]
           pr_sta (float): Static Poisson's ratio. Unit: unitless
           borehole_deviation (float): Borehole inclination from vertical. Unit: [deg]
           borehole_azimuth (float): Borehole azimuth from geographic North. Unit: [deg]
           shmax_azimuth (float): Azimuth of the maximum horizontal stress from geographic North. Unit: [deg]. Defaults to 0.0
           n_theta (int): Number of azimuthal positions evaluated around the wall. Defaults to 181

        Returns:
           pw_breakout (float): Minimum mud pressure preventing shear failure anywhere on the wall. Unit: same pressure unit

        Raises:
           ValueError: If no mud pressure can stabilize the wall (shear failure at every pressure)."""
        q = math.tan(math.radians(45 + fang / 2)) ** 2

        def shear_failure_excess(mud_pressure: float) -> float:
            sigma_1, sigma_3 = WellboreStabilityCalculation._borehole_wall_extreme_principal_stresses(
                shmax, shmin, overburden_stress, pprs, mud_pressure, pr_sta, borehole_deviation, borehole_azimuth, shmax_azimuth, n_theta
            )
            return float(np.max(sigma_1 - q * sigma_3 - ucs))

        pressure_scale = abs(shmax) + abs(overburden_stress) + abs(pprs) + abs(ucs) + 1.0
        low = -3.0 * pressure_scale
        high = 3.0 * pressure_scale

        # The failure excess is convex in mud pressure; locate its minimum first
        a, b = low, high
        for _ in range(120):
            m1 = a + (b - a) / 3
            m2 = b - (b - a) / 3
            if shear_failure_excess(m1) < shear_failure_excess(m2):
                b = m2
            else:
                a = m1
        stable_pressure = 0.5 * (a + b)
        if shear_failure_excess(stable_pressure) > 0:
            raise ValueError("No stable mud pressure exists for the given stresses and rock strength (shear failure at all mud pressures)")

        # Bisect between the failing low side and the stable minimum
        a, b = low, stable_pressure
        for _ in range(100):
            mid = 0.5 * (a + b)
            if shear_failure_excess(mid) > 0:
                a = mid
            else:
                b = mid

        return float(0.5 * (a + b))

    @staticmethod
    def calculate_breakdown_pressure_deviated_well(shmax: float, shmin: float, overburden_stress: float, pprs: float, tstr: float, pr_sta: float, borehole_deviation: float, borehole_azimuth: float, shmax_azimuth: float = 0.0, n_theta: int = 181) -> float:
        """
        Calculate the breakdown pressure (fracture initiation limit) for a deviated or
        inclined well, evaluated numerically on the borehole wall.

        Fracture initiates when the minimum effective principal stress on the wall reaches
        the negative tensile strength (sigma_3' = -tstr). The maximum mud pressure that
        avoids tensile failure anywhere on the wall is found by bisection. For a vertical
        well this reproduces `calculate_breakdown_calculation_vertical_well_analytical`.

        Unit-agnostic with respect to pressure: any consistent pressure unit.

        Reference: Fjaer, Erling, et al. Petroleum related rock mechanics. Vol. 53. Elsevier, 2008; Chapter 4.
        Hubbert, M. King, and David G. Willis. "Mechanics of hydraulic fracturing." Transactions of the AIME 210.01 (1957): 153-168.

        Args:
           shmax (float): Maximum horizontal stress magnitude. Unit: any consistent pressure unit
           shmin (float): Minimum horizontal stress magnitude. Unit: same pressure unit
           overburden_stress (float): Overburden (vertical) stress magnitude. Unit: same pressure unit
           pprs (float): Pore pressure. Unit: same pressure unit
           tstr (float): Tensile rock strength. Unit: same pressure unit
           pr_sta (float): Static Poisson's ratio. Unit: unitless
           borehole_deviation (float): Borehole inclination from vertical. Unit: [deg]
           borehole_azimuth (float): Borehole azimuth from geographic North. Unit: [deg]
           shmax_azimuth (float): Azimuth of the maximum horizontal stress from geographic North. Unit: [deg]. Defaults to 0.0
           n_theta (int): Number of azimuthal positions evaluated around the wall. Defaults to 181

        Returns:
           pw_breakdown (float): Maximum mud pressure before fracture initiation on the wall. Unit: same pressure unit"""

        def tensile_failure_excess(mud_pressure: float) -> float:
            _, sigma_3 = WellboreStabilityCalculation._borehole_wall_extreme_principal_stresses(
                shmax, shmin, overburden_stress, pprs, mud_pressure, pr_sta, borehole_deviation, borehole_azimuth, shmax_azimuth, n_theta
            )
            return float(-tstr - np.min(sigma_3))

        pressure_scale = abs(shmax) + abs(overburden_stress) + abs(pprs) + abs(tstr) + 1.0
        low = -3.0 * pressure_scale
        high = 3.0 * pressure_scale
        for _ in range(20):
            if tensile_failure_excess(high) > 0:
                break
            high = low + 2 * (high - low)

        # Locate the mud pressure minimizing the tensile excess (convex), then bisect upward
        a, b = low, high
        for _ in range(120):
            m1 = a + (b - a) / 3
            m2 = b - (b - a) / 3
            if tensile_failure_excess(m1) < tensile_failure_excess(m2):
                b = m2
            else:
                a = m1
        stable_pressure = 0.5 * (a + b)

        a, b = stable_pressure, high
        for _ in range(100):
            mid = 0.5 * (a + b)
            if tensile_failure_excess(mid) > 0:
                b = mid
            else:
                a = mid

        return float(0.5 * (a + b))

    @staticmethod
    def calculate_mud_weight_window_vertical_well(shmax: float, shmin: float, pprs: float, overburden_stress: float, ucs: float, fang: float, pr_sta: float, tstr: float) -> MudWeightWindow:
        """
        Calculate the full mud weight window for a vertical well using the analytical solutions.

        The window combines the four operational limits: pore pressure (kick), breakout
        pressure (hole collapse), minimum horizontal stress (mud losses) and breakdown
        pressure (fracture initiation). The safe static mud pressure window is
        max(kick, breakout) < Pw < min(loss, breakdown).

        Unit-agnostic with respect to pressure: any consistent pressure unit. Use
        `geomechpy.units.UnitConverter.convert_pressure_to_mud_weight` to express the
        limits as equivalent mud weights at a given depth.

        Args:
           shmax (float): Maximum horizontal stress magnitude. Unit: any consistent pressure unit
           shmin (float): Minimum horizontal stress magnitude. Unit: same pressure unit
           pprs (float): Pore pressure. Unit: same pressure unit
           overburden_stress (float): Overburden (vertical) stress magnitude. Unit: same pressure unit
           ucs (float): Unconfined compressive strength. Unit: same pressure unit
           fang (float): Internal friction angle. Unit: [dega]
           pr_sta (float): Static Poisson's ratio. Unit: unitless
           tstr (float): Tensile rock strength. Unit: same pressure unit

        Returns:
           MudWeightWindow: Dataclass with kick, breakout, loss and breakdown pressures. See `MudWeightWindow` for details. Unit: same pressure unit as the inputs"""
        breakout_pressure = WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(
            shmax=shmax, shmin=shmin, pprs=pprs, overburden_stress=overburden_stress, ucs=ucs, fang=fang, pr_sta=pr_sta
        )
        breakdown_pressure = WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical(
            shmax=shmax, shmin=shmin, pprs=pprs, tstr=tstr
        )

        return MudWeightWindow(
            kick_pressure=float(pprs),
            breakout_pressure=breakout_pressure,
            loss_pressure=float(shmin),
            breakdown_pressure=breakdown_pressure,
        )

    @staticmethod
    def calculate_mud_weight_window_deviated_well(shmax: float, shmin: float, pprs: float, overburden_stress: float, ucs: float, fang: float, pr_sta: float, tstr: float, borehole_deviation: float, borehole_azimuth: float, shmax_azimuth: float = 0.0, n_theta: int = 181) -> MudWeightWindow:
        """
        Calculate the full mud weight window for a deviated or inclined well using the
        numerical borehole-wall stability solutions.

        See `calculate_mud_weight_window_vertical_well` for the meaning of the four limits.

        Unit-agnostic with respect to pressure: any consistent pressure unit.

        Args:
           shmax (float): Maximum horizontal stress magnitude. Unit: any consistent pressure unit
           shmin (float): Minimum horizontal stress magnitude. Unit: same pressure unit
           pprs (float): Pore pressure. Unit: same pressure unit
           overburden_stress (float): Overburden (vertical) stress magnitude. Unit: same pressure unit
           ucs (float): Unconfined compressive strength. Unit: same pressure unit
           fang (float): Internal friction angle. Unit: [dega]
           pr_sta (float): Static Poisson's ratio. Unit: unitless
           tstr (float): Tensile rock strength. Unit: same pressure unit
           borehole_deviation (float): Borehole inclination from vertical. Unit: [deg]
           borehole_azimuth (float): Borehole azimuth from geographic North. Unit: [deg]
           shmax_azimuth (float): Azimuth of the maximum horizontal stress from geographic North. Unit: [deg]. Defaults to 0.0
           n_theta (int): Number of azimuthal positions evaluated around the wall. Defaults to 181

        Returns:
           MudWeightWindow: Dataclass with kick, breakout, loss and breakdown pressures. See `MudWeightWindow` for details. Unit: same pressure unit as the inputs"""
        breakout_pressure = WellboreStabilityCalculation.calculate_breakout_pressure_deviated_well_mohr_coulomb(
            shmax=shmax, shmin=shmin, overburden_stress=overburden_stress, pprs=pprs, ucs=ucs, fang=fang, pr_sta=pr_sta,
            borehole_deviation=borehole_deviation, borehole_azimuth=borehole_azimuth, shmax_azimuth=shmax_azimuth, n_theta=n_theta,
        )
        breakdown_pressure = WellboreStabilityCalculation.calculate_breakdown_pressure_deviated_well(
            shmax=shmax, shmin=shmin, overburden_stress=overburden_stress, pprs=pprs, tstr=tstr, pr_sta=pr_sta,
            borehole_deviation=borehole_deviation, borehole_azimuth=borehole_azimuth, shmax_azimuth=shmax_azimuth, n_theta=n_theta,
        )

        return MudWeightWindow(
            kick_pressure=float(pprs),
            breakout_pressure=breakout_pressure,
            loss_pressure=float(shmin),
            breakdown_pressure=breakdown_pressure,
        )

    @staticmethod
    def calculate_mud_weight_window_vertical_well_array(shmax: list[float], shmin: list[float], pprs: list[float], overburden_stress: list[float], ucs: list[float], fang: list[float], pr_sta: list[float], tstr: list[float]) -> list[MudWeightWindow]:
        """
        Calculate the mud weight window for a vertical well across arrays of inputs.

        Args:
           shmax (list[float]): Maximum horizontal stress values. Unit: any consistent pressure unit
           shmin (list[float]): Minimum horizontal stress values. Unit: same pressure unit
           pprs (list[float]): Pore pressure values. Unit: same pressure unit
           overburden_stress (list[float]): Overburden stress values. Unit: same pressure unit
           ucs (list[float]): Unconfined compressive strength values. Unit: same pressure unit
           fang (list[float]): Internal friction angle values. Unit: [dega]
           pr_sta (list[float]): Static Poisson's ratio values. Unit: unitless
           tstr (list[float]): Tensile rock strength values. Unit: same pressure unit

        Returns:
           list[MudWeightWindow]: Mud weight window entries for each input set."""
        return [
            WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well(
                shmax=sx, shmin=sn, pprs=pp, overburden_stress=ovb, ucs=uc, fang=fa, pr_sta=pr, tstr=ts
            )
            for sx, sn, pp, ovb, uc, fa, pr, ts in zip(shmax, shmin, pprs, overburden_stress, ucs, fang, pr_sta, tstr, strict=True)
        ]
