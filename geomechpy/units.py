"""Unit conversion utilities used across GeomechPy.

Calculations in GeomechPy fall into two groups:
  - Unit-agnostic calculations (e.g. elastic moduli conversions, wellbore stability limits)
    accept any consistent unit and return results in that same unit.
  - Unit-bound calculations (e.g. gradient-based pore pressure, velocity-to-moduli conversion)
    accept optional unit arguments and use `UnitConverter` internally.

`UnitConverter` can also be used directly to move any quantity between unit systems.
Unit names are case-insensitive."""

PSI_TO_PA = 6894.757293168362
FT_TO_M = 0.3048
STANDARD_GRAVITY = 9.80665  # m/s2

_PRESSURE_FACTORS = {  # factor to Pascal
    "pa": 1.0,
    "kpa": 1.0e3,
    "mpa": 1.0e6,
    "gpa": 1.0e9,
    "psi": PSI_TO_PA,
    "psia": PSI_TO_PA,
    "kpsi": PSI_TO_PA * 1.0e3,
    "mpsi": PSI_TO_PA * 1.0e6,
    "bar": 1.0e5,
    "atm": 101325.0,
}

_DEPTH_FACTORS = {  # factor to metre
    "m": 1.0,
    "km": 1.0e3,
    "ft": FT_TO_M,
}

_DENSITY_FACTORS = {  # factor to kg/m3
    "kg/m3": 1.0,
    "g/cm3": 1.0e3,
    "g/cc": 1.0e3,
    "lb/ft3": 16.018463373960142,
    "ppg": 119.82642731689663,
    "sg": 1.0e3,
}

_VELOCITY_FACTORS = {  # factor to m/s
    "m/s": 1.0,
    "km/s": 1.0e3,
    "ft/s": FT_TO_M,
}

_SLOWNESS_FACTORS = {  # factor to s/m
    "s/m": 1.0,
    "us/m": 1.0e-6,
    "us/ft": 1.0e-6 / FT_TO_M,
}

_MUD_WEIGHT_GRADIENT_FACTORS = {  # factor to Pa/m for density-style (equivalent mud weight) gradient units
    "ppg": _DENSITY_FACTORS["ppg"] * STANDARD_GRAVITY,
    "sg": _DENSITY_FACTORS["sg"] * STANDARD_GRAVITY,
    "g/cm3": _DENSITY_FACTORS["g/cm3"] * STANDARD_GRAVITY,
    "g/cc": _DENSITY_FACTORS["g/cc"] * STANDARD_GRAVITY,
}


class UnitConverter:
    """Convert pressures, depths, densities, velocities, slownesses, pressure gradients and mud weights between units.

    Supported units (case-insensitive):
        Pressure / modulus: Pa, kPa, MPa, GPa, psi, psia, kpsi, Mpsi, bar, atm
        Depth / length: m, km, ft
        Density: kg/m3, g/cm3, g/cc, lb/ft3, ppg, SG
        Velocity: m/s, km/s, ft/s
        Slowness: s/m, us/m, us/ft
        Pressure gradient: any '<pressure>/<depth>' combination (e.g. psi/ft, kPa/m, MPa/km)
            plus the equivalent mud weight units ppg, SG, g/cm3

    Reference:
        Thompson, Ambler, and Barry N. Taylor. Guide for the use of the International System of Units (SI). NIST Special Publication 811, 2008."""

    @staticmethod
    def _factor(factors: dict[str, float], unit: str, quantity: str) -> float:
        """Look up the SI conversion factor for a unit, raising a descriptive error for unknown units."""
        key = unit.strip().lower()
        if key not in factors:
            supported = ", ".join(sorted(factors))
            raise ValueError(f"Unsupported {quantity} unit '{unit}'. Supported units: {supported}")
        return factors[key]

    @staticmethod
    def _pressure_gradient_factor(unit: str) -> float:
        """Look up the conversion factor to Pa/m for a pressure gradient unit.

        Accepts any '<pressure>/<depth>' combination as well as equivalent mud weight units (ppg, SG, g/cm3)."""
        key = unit.strip().lower()
        if key in _MUD_WEIGHT_GRADIENT_FACTORS:
            return _MUD_WEIGHT_GRADIENT_FACTORS[key]
        pressure_unit, separator, depth_unit = key.partition("/")
        if separator and pressure_unit in _PRESSURE_FACTORS and depth_unit in _DEPTH_FACTORS:
            return _PRESSURE_FACTORS[pressure_unit] / _DEPTH_FACTORS[depth_unit]
        pressure_units = ", ".join(sorted(_PRESSURE_FACTORS))
        depth_units = ", ".join(sorted(_DEPTH_FACTORS))
        mud_weight_units = ", ".join(sorted(_MUD_WEIGHT_GRADIENT_FACTORS))
        raise ValueError(
            f"Unsupported pressure gradient unit '{unit}'. "
            f"Supported units: any '<pressure>/<depth>' combination with pressure in ({pressure_units}) "
            f"and depth in ({depth_units}), or an equivalent mud weight unit ({mud_weight_units})"
        )

    @staticmethod
    def convert_pressure(value: float, from_unit: str, to_unit: str) -> float:
        """Convert a pressure (or elastic modulus) value between units.

        Args:
            value (float): Pressure magnitude. Unit: from_unit
            from_unit (str): Source pressure unit (e.g. "psi", "kPa", "MPa", "Mpsi").
            to_unit (str): Target pressure unit.

        Returns:
            float: Pressure magnitude. Unit: to_unit"""
        return value * UnitConverter._factor(_PRESSURE_FACTORS, from_unit, "pressure") / UnitConverter._factor(_PRESSURE_FACTORS, to_unit, "pressure")

    @staticmethod
    def convert_depth(value: float, from_unit: str, to_unit: str) -> float:
        """Convert a depth (or length) value between units.

        Args:
            value (float): Depth magnitude. Unit: from_unit
            from_unit (str): Source depth unit (e.g. "ft", "m", "km").
            to_unit (str): Target depth unit.

        Returns:
            float: Depth magnitude. Unit: to_unit"""
        return value * UnitConverter._factor(_DEPTH_FACTORS, from_unit, "depth") / UnitConverter._factor(_DEPTH_FACTORS, to_unit, "depth")

    @staticmethod
    def convert_density(value: float, from_unit: str, to_unit: str) -> float:
        """Convert a density value between units.

        Args:
            value (float): Density magnitude. Unit: from_unit
            from_unit (str): Source density unit (e.g. "kg/m3", "g/cm3", "ppg", "SG").
            to_unit (str): Target density unit.

        Returns:
            float: Density magnitude. Unit: to_unit"""
        return value * UnitConverter._factor(_DENSITY_FACTORS, from_unit, "density") / UnitConverter._factor(_DENSITY_FACTORS, to_unit, "density")

    @staticmethod
    def convert_velocity(value: float, from_unit: str, to_unit: str) -> float:
        """Convert a velocity value between units.

        Args:
            value (float): Velocity magnitude. Unit: from_unit
            from_unit (str): Source velocity unit (e.g. "m/s", "ft/s", "km/s").
            to_unit (str): Target velocity unit.

        Returns:
            float: Velocity magnitude. Unit: to_unit"""
        return value * UnitConverter._factor(_VELOCITY_FACTORS, from_unit, "velocity") / UnitConverter._factor(_VELOCITY_FACTORS, to_unit, "velocity")

    @staticmethod
    def convert_slowness(value: float, from_unit: str, to_unit: str) -> float:
        """Convert a sonic slowness value between units.

        Args:
            value (float): Slowness magnitude. Unit: from_unit
            from_unit (str): Source slowness unit (e.g. "us/ft", "us/m").
            to_unit (str): Target slowness unit.

        Returns:
            float: Slowness magnitude. Unit: to_unit"""
        return value * UnitConverter._factor(_SLOWNESS_FACTORS, from_unit, "slowness") / UnitConverter._factor(_SLOWNESS_FACTORS, to_unit, "slowness")

    @staticmethod
    def convert_pressure_gradient(value: float, from_unit: str, to_unit: str) -> float:
        """Convert a pressure gradient value between units, including equivalent mud weight units.

        Args:
            value (float): Pressure gradient magnitude. Unit: from_unit
            from_unit (str): Source gradient unit (e.g. "psi/ft", "kPa/m", "ppg", "SG").
            to_unit (str): Target gradient unit.

        Returns:
            float: Pressure gradient magnitude. Unit: to_unit"""
        return value * UnitConverter._pressure_gradient_factor(from_unit) / UnitConverter._pressure_gradient_factor(to_unit)

    @staticmethod
    def convert_density_to_pressure_gradient(density: float, density_unit: str = "kg/m3", gradient_unit: str = "psi/ft") -> float:
        """Convert a density to the hydrostatic pressure gradient it exerts under standard gravity.

        Args:
            density (float): Density magnitude. Unit: density_unit
            density_unit (str): Density unit (e.g. "kg/m3", "g/cm3", "ppg"). Defaults to "kg/m3".
            gradient_unit (str): Target pressure gradient unit (e.g. "psi/ft", "kPa/m"). Defaults to "psi/ft".

        Returns:
            float: Pressure gradient magnitude. Unit: gradient_unit"""
        density_si = density * UnitConverter._factor(_DENSITY_FACTORS, density_unit, "density")
        gradient_pa_per_m = density_si * STANDARD_GRAVITY

        return gradient_pa_per_m / UnitConverter._pressure_gradient_factor(gradient_unit)

    @staticmethod
    def convert_pressure_to_mud_weight(pressure: float, tvd: float, pressure_unit: str = "psi", depth_unit: str = "ft", mud_weight_unit: str = "ppg") -> float:
        """Convert a downhole pressure at a given true vertical depth to an equivalent mud weight.

        Args:
            pressure (float): Downhole pressure magnitude. Unit: pressure_unit
            tvd (float): True Vertical Depth at which the pressure acts. Unit: depth_unit
            pressure_unit (str): Pressure unit (e.g. "psi", "kPa"). Defaults to "psi".
            depth_unit (str): Depth unit (e.g. "ft", "m"). Defaults to "ft".
            mud_weight_unit (str): Target equivalent mud weight unit (e.g. "ppg", "SG", "g/cm3"). Defaults to "ppg".

        Returns:
            float: Equivalent mud weight. Unit: mud_weight_unit"""
        pressure_pa = pressure * UnitConverter._factor(_PRESSURE_FACTORS, pressure_unit, "pressure")
        tvd_m = tvd * UnitConverter._factor(_DEPTH_FACTORS, depth_unit, "depth")
        gradient_pa_per_m = pressure_pa / tvd_m

        return gradient_pa_per_m / UnitConverter._pressure_gradient_factor(mud_weight_unit)

    @staticmethod
    def convert_mud_weight_to_pressure(mud_weight: float, tvd: float, mud_weight_unit: str = "ppg", pressure_unit: str = "psi", depth_unit: str = "ft") -> float:
        """Convert a mud weight to the downhole pressure it exerts at a given true vertical depth.

        Args:
            mud_weight (float): Mud weight magnitude. Unit: mud_weight_unit
            tvd (float): True Vertical Depth. Unit: depth_unit
            mud_weight_unit (str): Mud weight unit (e.g. "ppg", "SG", "g/cm3"). Defaults to "ppg".
            pressure_unit (str): Target pressure unit (e.g. "psi", "kPa"). Defaults to "psi".
            depth_unit (str): Depth unit (e.g. "ft", "m"). Defaults to "ft".

        Returns:
            float: Downhole pressure magnitude. Unit: pressure_unit"""
        gradient_pa_per_m = mud_weight * UnitConverter._pressure_gradient_factor(mud_weight_unit)
        tvd_m = tvd * UnitConverter._factor(_DEPTH_FACTORS, depth_unit, "depth")
        pressure_pa = gradient_pa_per_m * tvd_m

        return pressure_pa / UnitConverter._factor(_PRESSURE_FACTORS, pressure_unit, "pressure")

    @staticmethod
    def convert_pressure_array(values: list[float], from_unit: str, to_unit: str) -> list[float]:
        """Convert an array of pressure (or elastic modulus) values between units.

        Args:
            values (list[float]): Pressure values. Unit: from_unit
            from_unit (str): Source pressure unit.
            to_unit (str): Target pressure unit.

        Returns:
            list[float]: Pressure values. Unit: to_unit"""
        return [UnitConverter.convert_pressure(value, from_unit, to_unit) for value in values]

    @staticmethod
    def convert_depth_array(values: list[float], from_unit: str, to_unit: str) -> list[float]:
        """Convert an array of depth (or length) values between units.

        Args:
            values (list[float]): Depth values. Unit: from_unit
            from_unit (str): Source depth unit.
            to_unit (str): Target depth unit.

        Returns:
            list[float]: Depth values. Unit: to_unit"""
        return [UnitConverter.convert_depth(value, from_unit, to_unit) for value in values]

    @staticmethod
    def convert_density_array(values: list[float], from_unit: str, to_unit: str) -> list[float]:
        """Convert an array of density values between units.

        Args:
            values (list[float]): Density values. Unit: from_unit
            from_unit (str): Source density unit.
            to_unit (str): Target density unit.

        Returns:
            list[float]: Density values. Unit: to_unit"""
        return [UnitConverter.convert_density(value, from_unit, to_unit) for value in values]

    @staticmethod
    def convert_velocity_array(values: list[float], from_unit: str, to_unit: str) -> list[float]:
        """Convert an array of velocity values between units.

        Args:
            values (list[float]): Velocity values. Unit: from_unit
            from_unit (str): Source velocity unit.
            to_unit (str): Target velocity unit.

        Returns:
            list[float]: Velocity values. Unit: to_unit"""
        return [UnitConverter.convert_velocity(value, from_unit, to_unit) for value in values]

    @staticmethod
    def convert_slowness_array(values: list[float], from_unit: str, to_unit: str) -> list[float]:
        """Convert an array of sonic slowness values between units.

        Args:
            values (list[float]): Slowness values. Unit: from_unit
            from_unit (str): Source slowness unit.
            to_unit (str): Target slowness unit.

        Returns:
            list[float]: Slowness values. Unit: to_unit"""
        return [UnitConverter.convert_slowness(value, from_unit, to_unit) for value in values]

    @staticmethod
    def convert_pressure_gradient_array(values: list[float], from_unit: str, to_unit: str) -> list[float]:
        """Convert an array of pressure gradient values between units.

        Args:
            values (list[float]): Pressure gradient values. Unit: from_unit
            from_unit (str): Source gradient unit.
            to_unit (str): Target gradient unit.

        Returns:
            list[float]: Pressure gradient values. Unit: to_unit"""
        return [UnitConverter.convert_pressure_gradient(value, from_unit, to_unit) for value in values]

    @staticmethod
    def convert_density_to_pressure_gradient_array(density: list[float], density_unit: str = "kg/m3", gradient_unit: str = "psi/ft") -> list[float]:
        """Convert an array of density values to hydrostatic pressure gradients under standard gravity.

        Args:
            density (list[float]): Density values. Unit: density_unit
            density_unit (str): Density unit. Defaults to "kg/m3".
            gradient_unit (str): Target pressure gradient unit. Defaults to "psi/ft".

        Returns:
            list[float]: Pressure gradient values. Unit: gradient_unit"""
        return [
            UnitConverter.convert_density_to_pressure_gradient(density=value, density_unit=density_unit, gradient_unit=gradient_unit)
            for value in density
        ]

    @staticmethod
    def convert_pressure_to_mud_weight_array(pressure: list[float], tvd: list[float], pressure_unit: str = "psi", depth_unit: str = "ft", mud_weight_unit: str = "ppg") -> list[float]:
        """Convert arrays of downhole pressure and true vertical depth to equivalent mud weights.

        Args:
            pressure (list[float]): Downhole pressure values. Unit: pressure_unit
            tvd (list[float]): True Vertical Depth values. Unit: depth_unit
            pressure_unit (str): Pressure unit. Defaults to "psi".
            depth_unit (str): Depth unit. Defaults to "ft".
            mud_weight_unit (str): Target equivalent mud weight unit. Defaults to "ppg".

        Returns:
            list[float]: Equivalent mud weight values. Unit: mud_weight_unit"""
        return [
            UnitConverter.convert_pressure_to_mud_weight(pressure=p, tvd=d, pressure_unit=pressure_unit, depth_unit=depth_unit, mud_weight_unit=mud_weight_unit)
            for p, d in zip(pressure, tvd, strict=True)
        ]

    @staticmethod
    def convert_mud_weight_to_pressure_array(mud_weight: list[float], tvd: list[float], mud_weight_unit: str = "ppg", pressure_unit: str = "psi", depth_unit: str = "ft") -> list[float]:
        """Convert arrays of mud weight and true vertical depth to downhole pressures.

        Args:
            mud_weight (list[float]): Mud weight values. Unit: mud_weight_unit
            tvd (list[float]): True Vertical Depth values. Unit: depth_unit
            mud_weight_unit (str): Mud weight unit. Defaults to "ppg".
            pressure_unit (str): Target pressure unit. Defaults to "psi".
            depth_unit (str): Depth unit. Defaults to "ft".

        Returns:
            list[float]: Downhole pressure values. Unit: pressure_unit"""
        return [
            UnitConverter.convert_mud_weight_to_pressure(mud_weight=mw, tvd=d, mud_weight_unit=mud_weight_unit, pressure_unit=pressure_unit, depth_unit=depth_unit)
            for mw, d in zip(mud_weight, tvd, strict=True)
        ]
