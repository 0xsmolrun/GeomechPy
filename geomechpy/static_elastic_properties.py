import math

from geomechpy.units import UnitConverter


class StaticElasticPropertiesConverter:
    """Convert dynamic elastic properties to static elastic properties.

    The published correlations were calibrated in a specific unit (noted per method);
    the optional `modulus_unit` argument converts the input into that calibration unit
    and returns the result in the same `modulus_unit`. The custom power/linear laws use
    whatever unit the user regression coefficients were derived in.

    Reference:
        Zhang, Yuliang, et al. "Extracting static elastic moduli of rock through elastic wave velocities." Acta Geophysica 72.2 (2024): 915-931."""

    @staticmethod
    def dyn2sta_yme_bradord(yme_dyn: float, modulus_unit: str = "Mpsi") -> float:
        """Convert dynamic to static Young's modulus using Bradford correlation.

        Equation type: Power law (y = a*x**b)
        Applicable for: Turbiditic sandstones, Everest Field, North Sea.

        Reference: Bradford, I. D. R., Fuller, J., Thompson, P. J., & Walsgrove, T. R. (1998). Benefits of assessing the solids production risk in a North Sea reservoir using elastoplastic modelling (SPE/ISRM 47360). In SPE/ISRM. Eurorock '98 (pp. 261-269).

        Args:
           yme_dyn (float): Dynamic Young's modulus magnitude. Unit: [modulus_unit]
           modulus_unit (str): Unit of the Young's modulus input and output (e.g. "Mpsi", "GPa"). Correlation calibrated in Mpsi. Defaults to "Mpsi"

        Returns:
           float: Static Young's modulus magnitude (Bradford). Unit: [modulus_unit]"""
        yme_dyn = UnitConverter.convert_pressure(yme_dyn, modulus_unit, "Mpsi")

        multiplier = 0.04794626440600849
        exponent = 2.7
        yme_sta_bradford = multiplier * yme_dyn**exponent

        return UnitConverter.convert_pressure(float(yme_sta_bradford), "Mpsi", modulus_unit)

    @staticmethod
    def dyn2sta_yme_najib(yme_dyn: float, modulus_unit: str = "Mpsi") -> float:
        """Convert dynamic to static Young's modulus using Najib correlation.

        Equation type: Power law (y = a*x**b)
        Applicable for: Carbonates from Iran (Asmari and Sarvak limestone).

        Reference: Najibi, A., Ghafoori, M., Lashkaripur, G. and Asef, M., 2015. Empirical relations between strength and static and dynamic elastic properties of Asmari and Sarvak limestones, two main oil reservoirs in Iran, Journal of Petroleum Science and Engineering 126 (2015) 78-82.

        Args:
           yme_dyn (float): Dynamic Young's modulus magnitude. Unit: [modulus_unit]
           modulus_unit (str): Unit of the Young's modulus input and output (e.g. "Mpsi", "GPa"). Correlation calibrated in Mpsi. Defaults to "Mpsi"

        Returns:
           float: Static Young's modulus magnitude (Najib). Unit: [modulus_unit]"""
        yme_dyn = UnitConverter.convert_pressure(yme_dyn, modulus_unit, "Mpsi")

        multiplier = 0.07277314417314575
        exponent = 1.96
        yme_sta_najib = multiplier * yme_dyn**exponent

        return UnitConverter.convert_pressure(float(yme_sta_najib), "Mpsi", modulus_unit)

    @staticmethod
    def dyn2sta_yme_fuller(yme_dyn: float, modulus_unit: str = "GPa") -> float:
        """Convert dynamic to static Young's modulus using Fuller correlation.

        Equation type: Power law (y = a*x**b)
        Applicable for: Sandstone/Shale.

        Reference: Techlog help file

        Args:
           yme_dyn (float): Dynamic Young's modulus magnitude. Unit: [modulus_unit]
           modulus_unit (str): Unit of the Young's modulus input and output (e.g. "GPa", "Mpsi"). Correlation calibrated in GPa. Defaults to "GPa"

        Returns:
           float: Static Young's modulus magnitude (Fuller). Unit: [modulus_unit]"""
        yme_dyn = UnitConverter.convert_pressure(yme_dyn, modulus_unit, "GPa")

        multiplier = 0.08143824177457351
        exponent = 1.632
        yme_sta_fuller = multiplier * yme_dyn**exponent

        return UnitConverter.convert_pressure(float(yme_sta_fuller), "GPa", modulus_unit)

    @staticmethod
    def dyn2sta_yme_morales(yme_dyn: float, porosity: float, exclude_low_por: bool = True, modulus_unit: str = "Mpsi") -> float:
        """Convert dynamic to static Young's modulus using Morales correlation.

        Equation type: Power law (y = a*x**b)
        Applicable for: Sandstones:
                          Consolidated (10%-15%)
                          Moderately Consolidated (15%-25%)
                          Weakly consolidated (>25%)

        Reference: R.H. Morales and R. P. Marcinew, Fracturing of High-Permeability Formations: Mechanical Properties Correlations, SPE 26561, October 1993.

        Args:
           yme_dyn (float): Dynamic Young's modulus magnitude. Unit: [modulus_unit]
           porosity (float): Formation porosity as a fraction (e.g. 0.20 for 20%). Unit: unitless
           exclude_low_por (bool): If True, returns -9999 for porosity below 0.10. Defaults to True.
           modulus_unit (str): Unit of the Young's modulus input and output (e.g. "Mpsi", "GPa"). Correlation calibrated in Mpsi. Defaults to "Mpsi"

        Returns:
           float: Static Young's modulus magnitude (Morales). Unit: [modulus_unit]"""
        yme_dyn = UnitConverter.convert_pressure(yme_dyn, modulus_unit, "Mpsi")

        if porosity < 0.15:
            multiplier = 2.562214651764409
            exponent = 0.6612
        elif porosity < 0.25:
            multiplier = 0.5281242638335621
            exponent = 0.6920
        elif porosity > 0.25:
            multiplier = 0.3467028522374105
            exponent = 0.9404

        if porosity < 0.10 and exclude_low_por is True:
            yme_sta_morales = -9999
        else:
            yme_sta_morales = UnitConverter.convert_pressure(multiplier * yme_dyn**exponent, "Mpsi", modulus_unit)

        return yme_sta_morales

    @staticmethod
    def convert_dyn2sta_yme_custom_power_law(yme_dyn: float, multiplier: float, exponent: float) -> float:
        """Convert dynamic to static Young's modulus using a custom power law.

        Equation type: Power law (y = a*x**b)
        Applicable for: Generic.

        Args:
           yme_dyn (float): Dynamic Young's modulus magnitude. Unit: Mpsi
           multiplier (float): Custom multiplier - from core data regression or alternative power law correlation Unit: unitless
           exponent (float): Custom exponent - from core data regression or alternative power law correlation  Unit: unitless

        Returns:
           yme_sta_morales: Static Young's modulus magnitude. Unit: Mpsi"""
        yme_sta_power_law = multiplier * yme_dyn**exponent

        return float(yme_sta_power_law)

    @staticmethod
    def dyn2sta_yme_custom_linear_law(yme_dyn: float, slope: float, intercept: float) -> float:
        """Convert dynamic to static Young's modulus using a custom linear law.

        Equation type: Linear law (y = a*x + b)
        Applicable for: Generic.

        Args:
           yme_dyn (float): Dynamic Young's modulus magnitude Unit: Mpsi
           slope (float):  custom slope - from core data regression or alternative linear law correlation Unit: unitless
           intercept (float):  custom intercept - from core data regression or alternative linear law correlation Unit: unitless

        Returns:
           float: Static Young's modulus magnitude. Unit: Mpsi"""
        yme_sta_linear_law = slope * yme_dyn + intercept

        return yme_sta_linear_law

    @staticmethod
    def dyn2sta_poissons_ratio(pr_dyn: float, multiplier: float) -> float:
        """Convert dynamic to static Poisson's ratio using a constant multiplier.

        Equation type: Linear scaling (y = a*b)
        Applicable for: Generic.

        Reference: -

        Args:
           pr_dyn (float): Dynamic Poisson's ratio. Unit: unitless
           multiplier (float): Constant multiplier. Unit: unitless. Default set to 1.

        Returns:
           float: Static Poisson's ratio. Unit: unitless"""
        pr_sta = pr_dyn * multiplier

        return pr_sta

    @staticmethod
    def biot_coefficient_constant_law(constant: float) -> float:
        """Assign a constant value for the Biot coefficient.

        Equation type: Constant law (y = c)
        Applicable for: Generic.

        Reference: Jaeger, John Conrad, Neville GW Cook, and Robert Zimmerman. Fundamentals of rock mechanics. John Wiley & Sons, 2009.

        Args:
           constant (float): Constant value for Biot's coefficient. Unit: unitless

        Returns:
           float: Biot coefficient. Unit: unitless"""
        biot_constant = constant

        return biot_constant

    @staticmethod
    def dyn2sta_yme_bradord_array(yme_dyn: list[float], modulus_unit: str = "Mpsi") -> list[float]:
        """Convert an array of dynamic Young's modulus values to static using Bradford correlation.

        Args:
           yme_dyn (list[float]): Dynamic Young's modulus values. Unit: [modulus_unit]
           modulus_unit (str): Unit of the Young's modulus inputs and outputs. Defaults to "Mpsi"

        Returns:
           list[float]: Static Young's modulus values (Bradford). Unit: [modulus_unit]"""
        return [
            StaticElasticPropertiesConverter.dyn2sta_yme_bradord(yme_dyn=value, modulus_unit=modulus_unit)
            for value in yme_dyn
        ]

    @staticmethod
    def dyn2sta_yme_najib_array(yme_dyn: list[float], modulus_unit: str = "Mpsi") -> list[float]:
        """Convert an array of dynamic Young's modulus values to static using Najib correlation.

        Args:
           yme_dyn (list[float]): Dynamic Young's modulus values. Unit: [modulus_unit]
           modulus_unit (str): Unit of the Young's modulus inputs and outputs. Defaults to "Mpsi"

        Returns:
           list[float]: Static Young's modulus values (Najib). Unit: [modulus_unit]"""
        return [
            StaticElasticPropertiesConverter.dyn2sta_yme_najib(yme_dyn=value, modulus_unit=modulus_unit)
            for value in yme_dyn
        ]

    @staticmethod
    def dyn2sta_yme_fuller_array(yme_dyn: list[float], modulus_unit: str = "GPa") -> list[float]:
        """Convert an array of dynamic Young's modulus values to static using Fuller correlation.

        Args:
           yme_dyn (list[float]): Dynamic Young's modulus values. Unit: [modulus_unit]
           modulus_unit (str): Unit of the Young's modulus inputs and outputs. Defaults to "GPa"

        Returns:
           list[float]: Static Young's modulus values (Fuller). Unit: [modulus_unit]"""
        return [
            StaticElasticPropertiesConverter.dyn2sta_yme_fuller(yme_dyn=value, modulus_unit=modulus_unit)
            for value in yme_dyn
        ]

    @staticmethod
    def dyn2sta_yme_morales_array(yme_dyn: list[float], porosity: list[float], exclude_low_por: bool = True, modulus_unit: str = "Mpsi") -> list[float]:
        """Convert arrays of dynamic Young's modulus and porosity to static Young's modulus using Morales correlation.

        Args:
           yme_dyn (list[float]): Dynamic Young's modulus values. Unit: [modulus_unit]
           porosity (list[float]): Formation porosity values as fractions. Unit: unitless
           exclude_low_por (bool): If True, returns -9999 for porosity below 0.10. Defaults to True.
           modulus_unit (str): Unit of the Young's modulus inputs and outputs. Defaults to "Mpsi"

        Returns:
           list[float]: Static Young's modulus values (Morales). Unit: [modulus_unit]"""
        return [
            StaticElasticPropertiesConverter.dyn2sta_yme_morales(
                yme_dyn=yme_value,
                porosity=porosity_value,
                exclude_low_por=exclude_low_por,
                modulus_unit=modulus_unit,
            )
            for yme_value, porosity_value in zip(yme_dyn, porosity, strict=True)
        ]

    @staticmethod
    def convert_dyn2sta_yme_custom_power_law_array(yme_dyn: list[float], multiplier: float, exponent: float) -> list[float]:
        """Convert an array of dynamic Young's modulus values to static using a custom power law.

        Args:
           yme_dyn (list[float]): Dynamic Young's modulus values. Unit: Mpsi
           multiplier (float): Custom multiplier from regression. Unit: unitless
           exponent (float): Custom exponent from regression. Unit: unitless

        Returns:
           list[float]: Static Young's modulus values. Unit: Mpsi"""
        return [
            StaticElasticPropertiesConverter.convert_dyn2sta_yme_custom_power_law(
                yme_dyn=value,
                multiplier=multiplier,
                exponent=exponent,
            )
            for value in yme_dyn
        ]

    @staticmethod
    def dyn2sta_yme_custom_linear_law_array(yme_dyn: list[float], slope: float, intercept: float) -> list[float]:
        """Convert an array of dynamic Young's modulus values to static using a custom linear law.

        Args:
           yme_dyn (list[float]): Dynamic Young's modulus values. Unit: Mpsi
           slope (float): Custom slope from regression. Unit: unitless
           intercept (float): Custom intercept from regression. Unit: unitless

        Returns:
           list[float]: Static Young's modulus values. Unit: Mpsi"""
        return [
            StaticElasticPropertiesConverter.dyn2sta_yme_custom_linear_law(
                yme_dyn=value,
                slope=slope,
                intercept=intercept,
            )
            for value in yme_dyn
        ]

    @staticmethod
    def dyn2sta_poissons_ratio_array(pr_dyn: list[float], multiplier: float) -> list[float]:
        """Convert an array of dynamic Poisson's ratio values to static using a constant multiplier.

        Args:
           pr_dyn (list[float]): Dynamic Poisson's ratio values. Unit: unitless
           multiplier (float): Constant multiplier. Unit: unitless

        Returns:
           list[float]: Static Poisson's ratio values. Unit: unitless"""
        return [
            StaticElasticPropertiesConverter.dyn2sta_poissons_ratio(pr_dyn=value, multiplier=multiplier)
            for value in pr_dyn
        ]
