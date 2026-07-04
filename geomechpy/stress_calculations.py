import math
from dataclasses import dataclass

from geomechpy.units import UnitConverter


@dataclass(frozen=True)
class HorizontalStresses:
    """Calculation of stress components and properties.

    Attributes:
        shmin (float): Minimum horizontal stress magnitude. Unit: Pressure
        shmax (float): Maximum horizontal stress magnitude. Unit: Pressure
        q_factor (float): Stress regime indicator. Unit: unitless
        shmax_shmin_ratio (float): Ratio of maximum to minimum horizontal stress. Unit: unitless"""

    shmin: float
    shmax: float
    q_factor: float
    shmax_shmin_ratio: float


class HorizontalStressesCalculation:
    """Calculation of stress components and properties.

    Reference:
       Zhang, Jon Jincai. Applied petroleum geomechanics. Vol. 1. Cambridge: Gulf Professional Publishing, 2019 Chapter 6."""

    @staticmethod
    def calculate_poroelastic_horizontal_stresses(overburden_stress: float, pore_pressure: float, poisson_ratio: float, youngs_modulus: float, biot_coefficient: float = 1.0, EX: float = 0.0001, EY: float = 0.0009, pressure_unit: str = "psi", modulus_unit: str = "Mpsi") -> HorizontalStresses:
        """Calculates horizontal stress using Poroelastic horizontal stress equation.

        Implements shmin = A*Sv + (1 - A)*biot*Pp + B*ex + C*ey (and the symmetric expression
        for shmax) with A = v/(1-v), B = E/(1-v^2), C = v*E/(1-v^2), where ex/ey are the
        dimensionless tectonic strains. The Young's modulus is converted into the stress unit
        internally so the tectonic strain terms are dimensionally consistent with the stress terms.

        Reference: Thiercelin, Marc Jean, and Richard A. Plumb. "Core-based prediction of lithologic stress contrasts in East Texas formations." SPE Formation Evaluation 9.04 (1994): 251-258.

        Args:
            overburden_stress (float): Overburden stress magnitude. Unit: Pressure Unit [pressure_unit].
            pore_pressure (float): Pore pressure magnitude. Unit: Pressure Unit [pressure_unit].
            poisson_ratio (float): Static Poisson's ratio. Unit: unitless.
            youngs_modulus (float): Static Young's modulus. Unit: [modulus_unit].
            biot_coefficient (float): Biot's coefficient. Defaults to 1.0
            EX (float): Tectonic strain in the minimum horizontal stress direction. Unit: unitless (typical range 1e-4 to 1e-3). Defaults to 0.0001.
            EY (float): Tectonic strain in the maximum horizontal stress direction. Unit: unitless (typical range 1e-4 to 1e-3). Defaults to 0.0009.
            pressure_unit (str): Unit of the stress/pressure inputs and outputs (e.g. "psi", "kPa", "MPa"). Defaults to "psi".
            modulus_unit (str): Unit of the Young's modulus input (e.g. "Mpsi", "GPa"). Defaults to "Mpsi".

        Returns:
            shmin (float): Minimum horizontal stress magnitude Unit [pressure_unit].
            shmax (float): Maximum horizontal stress magnitude Unit [pressure_unit].
            q_factor (float): Stress Regime Indicator. Unit [unitless].
            shmax_shmin_ratio (float): Stress ratio. Unit [unitless]."""
        overburden_stress = UnitConverter.convert_pressure(overburden_stress, pressure_unit, "psi")
        pore_pressure = UnitConverter.convert_pressure(pore_pressure, pressure_unit, "psi")
        youngs_modulus = UnitConverter.convert_pressure(youngs_modulus, modulus_unit, "psi")

        A = poisson_ratio / (1 - poisson_ratio)
        B = youngs_modulus / (1 - poisson_ratio * poisson_ratio)
        C = (poisson_ratio * youngs_modulus) / (1 - poisson_ratio * poisson_ratio)

        shmin = A * overburden_stress + (1 - A) * biot_coefficient * pore_pressure + B * EX + C * EY
        shmax = A * overburden_stress + (1 - A) * biot_coefficient * pore_pressure + B * EY + C * EX

        q_factor = HorizontalStressesCalculation.calculate_stress_regime_q_factor(0.0, shmax, shmin)
        shmax_shmin_ratio = HorizontalStressesCalculation.calculate_horizontal_stress_ratio(shmax, shmin)

        shmin = UnitConverter.convert_pressure(shmin, "psi", pressure_unit)
        shmax = UnitConverter.convert_pressure(shmax, "psi", pressure_unit)

        return HorizontalStresses(shmin, shmax, q_factor, shmax_shmin_ratio)

    @staticmethod
    def calculate_shmax_multiplier(shmin: float, shmax_multiplier: float = 1.1) -> float:
        """Calculates maximum horizontal stress from minimum horizontal stress using multiplier.

        Args:
            shmin (float): Minimum horizontal stress magnitude. Unit: [psi]
            shmax_multiplier (float): A unitless multiplier representing the stress anisotropy Defaults to 1.1

        Returns:
            shmax (float): Maximum horizontal stress magnitude. Unit [psi]."""
        shmax = shmin * shmax_multiplier

        return shmax

    @staticmethod
    def calculate_stress_regime_q_factor(sigv: float, shmax: float, shmin: float) -> float:
        """Calculates q factor representing the stress regime based on the order and relative magnitude of the three principle stresses.
            Normal Stress Regime: sigv  > shmax > shmin --> 0 > q < 1
            Strike slip Regime: shmax > sigv  > shmin --> 1 > q < 2
            Reverse Faulting: shmax > shmin > sigv  --> 2 > q < 3

        Reference: Prats, M., Effect of Burial History on the Subsurface Horizontal Stresses of Formations Having Different Material Properties, SPE 9017-PA, 1981.

        Args:
            sigv (float): Vertical stress magnitude. Unit [psi].
            shmax (float): Maximum horizontal stress magnitude. Unit [psi].
            shmin (float): Minimum horizontal stress magnitude. Unit [psi].

        Returns:
            q_factor (float): q factor provides measure for the stress regime"""
        if sigv > shmax and shmax >= shmin:
            q_factor = (shmax - shmin) / (sigv - shmin)
        elif shmin < sigv and sigv <= shmax:
            q_factor = 2 - (sigv - shmin) / (shmax - shmin)
        elif sigv <= shmin and shmin < shmax:
            q_factor = 2 + (shmin - sigv) / (shmax - sigv)
        else:
            q_factor = 4

        return q_factor

    @staticmethod
    def calculate_horizontal_stress_ratio(shmax: float, shmin: float) -> float:
        """Calculates the ratio between maximum and minimum horizontal stress magnitudes.

        Args:
            shmax (float): Maximum horizontal stress magnitude. Unit [psi].
            shmin (float): Minimum horizontal stress magnitude. Unit [psi].

        Returns:
            shmax_shmin_ratio (float): stress ratio between maximum and minimum horizontal stress magnitudes. Unit [unitless].
            Value needs to be equal or bigger than 1"""
        shmax_shmin_ratio = shmax / shmin
        return shmax_shmin_ratio

    @staticmethod
    def calculate_poroelastic_horizontal_stresses_array(overburden_stress: list[float], pore_pressure: list[float], poisson_ratio: list[float], youngs_modulus: list[float], biot_coefficient: list[float], EX: float = 0.0001, EY: float = 0.0009, pressure_unit: str = "psi", modulus_unit: str = "Mpsi") -> list[HorizontalStresses]:
        """Calculates horizontal stresses for arrays of inputs using the Poroelastic horizontal stress equation.

        Args:
            overburden_stress (list[float]): Overburden stress values. Unit: Pressure Unit [pressure_unit].
            pore_pressure (list[float]): Pore pressure values. Unit: Pressure Unit [pressure_unit].
            poisson_ratio (list[float]): Static Poisson's ratio values. Unit: unitless.
            youngs_modulus (list[float]): Static Young's modulus values. Unit: [modulus_unit].
            biot_coefficient (float): Biot's coefficient. Defaults to 1.0
            EX (float): Tectonic strain in the minimum horizontal stress direction. Unit: unitless. Defaults to 0.0001.
            EY (float): Tectonic strain in the maximum horizontal stress direction. Unit: unitless. Defaults to 0.0009.
            pressure_unit (str): Unit of the stress/pressure inputs and outputs (e.g. "psi", "kPa", "MPa"). Defaults to "psi".
            modulus_unit (str): Unit of the Young's modulus inputs (e.g. "Mpsi", "GPa"). Defaults to "Mpsi".

        Returns:
            list[HorizontalStresses]: HorizontalStresses entries for each set of input values."""
        return [
            HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses(
                overburden_stress=ovb,
                pore_pressure=pp,
                poisson_ratio=pr,
                youngs_modulus=ym,
                biot_coefficient=bc,
                EX=EX,
                EY=EY,
                pressure_unit=pressure_unit,
                modulus_unit=modulus_unit,
            )
            for ovb, pp, pr, ym, bc in zip(overburden_stress, pore_pressure, poisson_ratio, youngs_modulus, biot_coefficient, strict=True)
        ]

    @staticmethod
    def calculate_shmax_multiplier_array(shmin: list[float], shmax_multiplier: float = 1.1) -> list[float]:
        """Calculates an array of maximum horizontal stress values from minimum horizontal stress using a multiplier.

        Args:
            shmin (list[float]): Minimum horizontal stress values. Unit: [psi]
            shmax_multiplier (float): A unitless multiplier representing the stress anisotropy. Defaults to 1.1

        Returns:
            shmax (list[float]): Maximum horizontal stress values. Unit [psi]."""
        return [
            HorizontalStressesCalculation.calculate_shmax_multiplier(shmin=value, shmax_multiplier=shmax_multiplier)
            for value in shmin
        ]

    @staticmethod
    def calculate_stress_regime_q_factor_array(sigv: list[float], shmax: list[float], shmin: list[float]) -> list[float]:
        """Calculates the stress regime q factor for arrays of principal stress values.

        Args:
            sigv (list[float]): Vertical stress values. Unit [psi].
            shmax (list[float]): Maximum horizontal stress values. Unit [psi].
            shmin (list[float]): Minimum horizontal stress values. Unit [psi].

        Returns:
            q_factor (list[float]): q factor values for each input depth."""
        return [
            HorizontalStressesCalculation.calculate_stress_regime_q_factor(
                sigv=sv,
                shmax=sx,
                shmin=sn,
            )
            for sv, sx, sn in zip(sigv, shmax, shmin, strict=True)
        ]

    @staticmethod
    def calculate_horizontal_stress_ratio_array(shmax: list[float], shmin: list[float]) -> list[float]:
        """Calculates the ratio between maximum and minimum horizontal stress magnitudes for arrays of values.

        Args:
            shmax (list[float]): Maximum horizontal stress values. Unit [psi].
            shmin (list[float]): Minimum horizontal stress values. Unit [psi].

        Returns:
            shmax_shmin_ratio (list[float]): Stress ratio values between maximum and minimum horizontal stresses. Unit [unitless]."""
        return [
            HorizontalStressesCalculation.calculate_horizontal_stress_ratio(shmax=sx, shmin=sn)
            for sx, sn in zip(shmax, shmin, strict=True)
        ]
