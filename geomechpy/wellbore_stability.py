import math
from dataclasses import dataclass


@dataclass(frozen=True)
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
           shmin (float): Minimum horizontal stress magnitude Unit [psi].
           shmax (float): Maximum horizontal stress magnitude Unit [psi].
           pore_pressure (float): value of pressure calculated for onshore in pressure unit  Unit: Pressure Unit [psi]
           tstr (float): tensile rock strength

        Returns:
           pw_breakdown (float):  Unit: psi
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
           shmin (float): Minimum horizontal stress magnitude Unit [psi].
           shmax (float): Maximum horizontal stress magnitude Unit [psi].
           pore_pressure (float): value of pressure in pressure unit  Unit: Pressure Unit [psi]
           overburden_stress: value of overburden stress in pressure unit  Unit: Pressure Unit [psi]
           ucs: Unconfined compressive strength (UCS) Unit: [psi]
           fang (float): Angle of internal friction angle  Unit: [dega]
           pr_sta (float): Static Poisson's ratio Unit: [unitless]

        Returns:
           pw_breakout (float):  Unit: psi
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
           shmax (list[float]): Maximum horizontal stress values Unit [psi].
           shmin (list[float]): Minimum horizontal stress values Unit [psi].
           pprs (list[float]): Pore pressure values Unit: Pressure Unit [psi]
           tstr (list[float]): Tensile rock strength values Unit [psi]

        Returns:
           pw_breakdown (list[float]): Breakdown pressure values. Unit: psi
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
           shmax (list[float]): Maximum horizontal stress values Unit [psi].
           shmin (list[float]): Minimum horizontal stress values Unit [psi].
           pprs (list[float]): Pore pressure values Unit: Pressure Unit [psi]
           overburden_stress (list[float]): Overburden stress values Unit: Pressure Unit [psi]
           ucs (list[float]): Unconfined compressive strength values Unit: [psi]
           fang (list[float]): Internal friction angle values Unit: [dega]
           pr_sta (list[float]): Static Poisson's ratio values Unit: [unitless]

        Returns:
           pw_breakout (list[float]): Breakout pressure values. Unit: psi
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
