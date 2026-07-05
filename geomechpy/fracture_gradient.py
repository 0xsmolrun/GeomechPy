class FractureGradientCalculation:
    """Estimation of the formation fracture pressure (fracture gradient) using classic methods.

    All methods are unit-agnostic with respect to pressure: overburden stress and pore
    pressure may be given in any consistent pressure unit (psi, kPa, MPa, ...) and the
    fracture pressure is returned in that same unit. To express the result as a gradient
    or equivalent mud weight, divide by depth or use
    `geomechpy.units.UnitConverter.convert_pressure_to_mud_weight`.

    Reference:
       Zhang, Jon Jincai. Applied petroleum geomechanics. Vol. 1. Cambridge: Gulf Professional Publishing, 2019. Chapter 8."""

    @staticmethod
    def calculate_fracture_pressure_hubbert_willis_min(overburden_stress: float, pore_pressure: float) -> float:
        """Calculates the minimum fracture pressure using the Hubbert & Willis method.

        P_frac = (Sv + 2*Pp) / 3, equivalent to (Sv - Pp)/3 + Pp - the lower bound assuming
        the minimum effective horizontal stress is one third of the effective overburden.

        Reference: Hubbert, M. King, and David G. Willis. "Mechanics of hydraulic fracturing." Transactions of the AIME 210.01 (1957): 153-168.

        Args:
            overburden_stress (float): Overburden (vertical) stress magnitude. Unit: any consistent pressure unit
            pore_pressure (float): Pore pressure magnitude. Unit: same pressure unit

        Returns:
            fracture_pressure (float): Minimum fracture pressure estimate. Unit: same pressure unit as the inputs"""
        fracture_pressure = (overburden_stress + 2 * pore_pressure) / 3

        return float(fracture_pressure)

    @staticmethod
    def calculate_fracture_pressure_hubbert_willis_max(overburden_stress: float, pore_pressure: float) -> float:
        """Calculates the maximum fracture pressure using the Hubbert & Willis method.

        P_frac = (Sv + Pp) / 2, equivalent to (Sv - Pp)/2 + Pp - the upper bound assuming
        the minimum effective horizontal stress is one half of the effective overburden.

        Reference: Hubbert, M. King, and David G. Willis. "Mechanics of hydraulic fracturing." Transactions of the AIME 210.01 (1957): 153-168.

        Args:
            overburden_stress (float): Overburden (vertical) stress magnitude. Unit: any consistent pressure unit
            pore_pressure (float): Pore pressure magnitude. Unit: same pressure unit

        Returns:
            fracture_pressure (float): Maximum fracture pressure estimate. Unit: same pressure unit as the inputs"""
        fracture_pressure = (overburden_stress + pore_pressure) / 2

        return float(fracture_pressure)

    @staticmethod
    def calculate_fracture_pressure_matthews_kelly(overburden_stress: float, pore_pressure: float, matrix_stress_coefficient: float) -> float:
        """Calculates the fracture pressure using the Matthews & Kelly method.

        P_frac = Ki * (Sv - Pp) + Pp, where Ki is the matrix stress coefficient calibrated
        from regional leak-off or fracture data (Ki typically increases with depth).

        Reference: Matthews, W. R., and John Kelly. "How to predict formation pressure and fracture gradient." Oil and Gas Journal 65.8 (1967): 92-106.

        Args:
            overburden_stress (float): Overburden (vertical) stress magnitude. Unit: any consistent pressure unit
            pore_pressure (float): Pore pressure magnitude. Unit: same pressure unit
            matrix_stress_coefficient (float): Matrix stress coefficient Ki. Unit: unitless (typical 0.3 - 1.0)

        Returns:
            fracture_pressure (float): Fracture pressure estimate. Unit: same pressure unit as the inputs"""
        fracture_pressure = matrix_stress_coefficient * (overburden_stress - pore_pressure) + pore_pressure

        return float(fracture_pressure)

    @staticmethod
    def calculate_fracture_pressure_eaton(overburden_stress: float, pore_pressure: float, poisson_ratio: float) -> float:
        """Calculates the fracture pressure using Eaton's method.

        P_frac = v/(1-v) * (Sv - Pp) + Pp. Identical in form to Eaton's minimum horizontal
        stress (`HorizontalStressesCalculation.calculate_shmin_eaton` with Biot = 1): the
        fracture extension pressure equals the minimum horizontal stress.

        Reference: Eaton, Ben A. "Fracture gradient prediction and its application in oilfield operations." Journal of petroleum technology 21.10 (1969): 1353-1360.

        Args:
            overburden_stress (float): Overburden (vertical) stress magnitude. Unit: any consistent pressure unit
            pore_pressure (float): Pore pressure magnitude. Unit: same pressure unit
            poisson_ratio (float): Static Poisson's ratio. Unit: unitless

        Returns:
            fracture_pressure (float): Fracture pressure estimate. Unit: same pressure unit as the inputs"""
        fracture_pressure = poisson_ratio / (1 - poisson_ratio) * (overburden_stress - pore_pressure) + pore_pressure

        return float(fracture_pressure)

    @staticmethod
    def calculate_fracture_pressure_hubbert_willis_min_array(overburden_stress: list[float], pore_pressure: list[float]) -> list[float]:
        """Calculates the minimum Hubbert & Willis fracture pressure for arrays of inputs.

        Args:
            overburden_stress (list[float]): Overburden stress values. Unit: any consistent pressure unit
            pore_pressure (list[float]): Pore pressure values. Unit: same pressure unit

        Returns:
            fracture_pressure (list[float]): Minimum fracture pressure estimates. Unit: same pressure unit as the inputs"""
        return [
            FractureGradientCalculation.calculate_fracture_pressure_hubbert_willis_min(overburden_stress=ovb, pore_pressure=pp)
            for ovb, pp in zip(overburden_stress, pore_pressure, strict=True)
        ]

    @staticmethod
    def calculate_fracture_pressure_hubbert_willis_max_array(overburden_stress: list[float], pore_pressure: list[float]) -> list[float]:
        """Calculates the maximum Hubbert & Willis fracture pressure for arrays of inputs.

        Args:
            overburden_stress (list[float]): Overburden stress values. Unit: any consistent pressure unit
            pore_pressure (list[float]): Pore pressure values. Unit: same pressure unit

        Returns:
            fracture_pressure (list[float]): Maximum fracture pressure estimates. Unit: same pressure unit as the inputs"""
        return [
            FractureGradientCalculation.calculate_fracture_pressure_hubbert_willis_max(overburden_stress=ovb, pore_pressure=pp)
            for ovb, pp in zip(overburden_stress, pore_pressure, strict=True)
        ]

    @staticmethod
    def calculate_fracture_pressure_matthews_kelly_array(overburden_stress: list[float], pore_pressure: list[float], matrix_stress_coefficient: list[float]) -> list[float]:
        """Calculates the Matthews & Kelly fracture pressure for arrays of inputs.

        Args:
            overburden_stress (list[float]): Overburden stress values. Unit: any consistent pressure unit
            pore_pressure (list[float]): Pore pressure values. Unit: same pressure unit
            matrix_stress_coefficient (list[float]): Matrix stress coefficient Ki values (depth-dependent). Unit: unitless

        Returns:
            fracture_pressure (list[float]): Fracture pressure estimates. Unit: same pressure unit as the inputs"""
        return [
            FractureGradientCalculation.calculate_fracture_pressure_matthews_kelly(overburden_stress=ovb, pore_pressure=pp, matrix_stress_coefficient=ki)
            for ovb, pp, ki in zip(overburden_stress, pore_pressure, matrix_stress_coefficient, strict=True)
        ]

    @staticmethod
    def calculate_fracture_pressure_eaton_array(overburden_stress: list[float], pore_pressure: list[float], poisson_ratio: list[float]) -> list[float]:
        """Calculates the Eaton fracture pressure for arrays of inputs.

        Args:
            overburden_stress (list[float]): Overburden stress values. Unit: any consistent pressure unit
            pore_pressure (list[float]): Pore pressure values. Unit: same pressure unit
            poisson_ratio (list[float]): Static Poisson's ratio values. Unit: unitless

        Returns:
            fracture_pressure (list[float]): Fracture pressure estimates. Unit: same pressure unit as the inputs"""
        return [
            FractureGradientCalculation.calculate_fracture_pressure_eaton(overburden_stress=ovb, pore_pressure=pp, poisson_ratio=pr)
            for ovb, pp, pr in zip(overburden_stress, pore_pressure, poisson_ratio, strict=True)
        ]
