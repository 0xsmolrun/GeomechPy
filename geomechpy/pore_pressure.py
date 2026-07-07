from geomechpy.units import UnitConverter


class PorePressureCalculation:
    """Computation of the Pore Pressure using gradient based methods.

    All methods accept optional `depth_unit`, `pressure_unit` and `gradient_unit` arguments:
    depths are interpreted in `depth_unit`, results are returned in `pressure_unit`, and
    gradients are interpreted in `gradient_unit` — either a `<pressure>/<depth>` combination
    (e.g. "psi/ft", "kPa/m") or an equivalent mud weight unit (e.g. "ppg", "SG"). When
    `gradient_unit` is omitted, gradients default to `pressure_unit`/`depth_unit`.
    Defaults are field units (ft, psi, psi/ft).

    Reference:
       Zhang, Jon Jincai. Applied petroleum geomechanics. Vol. 1. Cambridge: Gulf Professional Publishing, 2019. Chapter 6.1"""

    @staticmethod
    def calculate_pore_pressure_onshore(tvd: float, formation_pore_pressure_gradient: float | None = None, air_gap: float = 0.0, gradient_unit: str | None = None, depth_unit: str = "ft", pressure_unit: str = "psi") -> float:
        """Calculates pore pressure from tvd and pore pressure gradient in onshore setting.

        Args:
            tvd (float): True Vertical Depth. Unit: Depth Unit [depth_unit]
            formation_pore_pressure_gradient (float | None): Pore pressure depth gradient. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 0.47 psi/ft
            air_gap (float): Distance from Drill Floor to Ground Level. Usually reported as Kelly bushing (KB) or Elevation Ground Level. Unit: Depth Unit [depth_unit]. Defaults to 0.0
            gradient_unit (str | None): Unit of the gradient inputs (e.g. "psi/ft", "kPa/m", "ppg", "SG"). Defaults to pressure_unit/depth_unit
            depth_unit (str): Unit of the depth inputs (e.g. "ft", "m"). Defaults to "ft"
            pressure_unit (str): Unit of the pressure output and gradient numerator (e.g. "psi", "kPa", "MPa"). Defaults to "psi"

        Returns:
            pore_pressure (float): Pore pressure for onshore setting. Unit: Pressure Unit [pressure_unit]

        Example:
            >>> PorePressureCalculation.calculate_pore_pressure_onshore(tvd=10000.0)
            4700.0
            >>> round(PorePressureCalculation.calculate_pore_pressure_onshore(
            ...     tvd=10000.0, formation_pore_pressure_gradient=9.0, gradient_unit="ppg"), 1)
            4675.3"""
        if tvd < 0:
            raise ValueError(f"tvd must be non-negative, got {tvd}")
        if air_gap < 0:
            raise ValueError("air_gap must be non-negative")
        if gradient_unit is None:
            gradient_unit = f"{pressure_unit}/{depth_unit}"
        tvd = UnitConverter.convert_depth(tvd, depth_unit, "ft")
        air_gap = UnitConverter.convert_depth(air_gap, depth_unit, "ft")
        if formation_pore_pressure_gradient is None:
            formation_pore_pressure_gradient = 0.47
        else:
            formation_pore_pressure_gradient = UnitConverter.convert_pressure_gradient(formation_pore_pressure_gradient, gradient_unit, "psi/ft")

        air_gradient = 0.0004
        air_pressure = air_gradient * air_gap
        if tvd >= 0 and tvd < air_gap:
            pore_pressure = air_gradient * tvd
        else:
            pore_pressure = air_pressure + formation_pore_pressure_gradient * (tvd - air_gap)

        return UnitConverter.convert_pressure(pore_pressure, "psi", pressure_unit)

    @staticmethod
    def calculate_pore_pressure_offshore(tvd: float, formation_pore_pressure_gradient: float | None = None, air_gap: float = 0.0, water_depth: float = 0.0, sea_water_pressure_gradient: float | None = None, gradient_unit: str | None = None, depth_unit: str = "ft", pressure_unit: str = "psi") -> float:
        """Calculates pore pressure from tvd and pore pressure gradient in offshore setting.

        Args:
            tvd (float): True Vertical Depth. Unit: Depth Unit [depth_unit]
            formation_pore_pressure_gradient (float | None): Pore pressure depth gradient. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 0.47 psi/ft
            air_gap (float): Distance from Drill Floor to mean sea level. Usually reported as Kelly bushing (KB). Unit: Depth Unit [depth_unit]. Defaults to 0.0
            water_depth (float): Water Depth measured from the mean sea level to sea bottom at well location. Unit: Depth Unit [depth_unit]. Defaults to 0.0
            sea_water_pressure_gradient (float | None): Water gradient of the sea water. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 0.47 psi/ft
            gradient_unit (str | None): Unit of the gradient inputs (e.g. "psi/ft", "kPa/m", "ppg", "SG"). Defaults to pressure_unit/depth_unit
            depth_unit (str): Unit of the depth inputs (e.g. "ft", "m"). Defaults to "ft"
            pressure_unit (str): Unit of the pressure output and gradient numerators (e.g. "psi", "kPa", "MPa"). Defaults to "psi"

        Returns:
            pore_pressure (float): Pore pressure for offshore setting. Unit: Pressure Unit [pressure_unit]"""
        if tvd < 0:
            raise ValueError(f"tvd must be non-negative, got {tvd}")
        if air_gap < 0 or water_depth < 0:
            raise ValueError("air_gap and water_depth must be non-negative")
        if gradient_unit is None:
            gradient_unit = f"{pressure_unit}/{depth_unit}"
        tvd = UnitConverter.convert_depth(tvd, depth_unit, "ft")
        air_gap = UnitConverter.convert_depth(air_gap, depth_unit, "ft")
        water_depth = UnitConverter.convert_depth(water_depth, depth_unit, "ft")
        if formation_pore_pressure_gradient is None:
            formation_pore_pressure_gradient = 0.47
        else:
            formation_pore_pressure_gradient = UnitConverter.convert_pressure_gradient(formation_pore_pressure_gradient, gradient_unit, "psi/ft")
        if sea_water_pressure_gradient is None:
            sea_water_pressure_gradient = 0.47
        else:
            sea_water_pressure_gradient = UnitConverter.convert_pressure_gradient(sea_water_pressure_gradient, gradient_unit, "psi/ft")

        air_gradient = 0.0004
        air_pressure = air_gradient * air_gap

        water_pressure = sea_water_pressure_gradient * water_depth

        if tvd >= 0 and tvd < air_gap:
            pore_pressure = air_gradient * tvd
        elif tvd >= air_gap and tvd <= (air_gap + water_depth):
            pore_pressure = air_pressure + sea_water_pressure_gradient * (tvd - air_gap)
        else:
            pore_pressure = air_pressure + water_pressure + formation_pore_pressure_gradient * (tvd - water_depth - air_gap)

        return UnitConverter.convert_pressure(pore_pressure, "psi", pressure_unit)

    @staticmethod
    def calculate_pore_pressure_onshore_array(tvd: list[float], formation_pore_pressure_gradient: float | None = None, air_gap: float = 0.0, gradient_unit: str | None = None, depth_unit: str = "ft", pressure_unit: str = "psi") -> list[float]:
        """Calculates pore pressure for an array of tvd values in onshore setting.

        Args:
            tvd (list[float]): True Vertical Depth values. Unit: Depth Unit [depth_unit]
            formation_pore_pressure_gradient (float | None): Pore pressure depth gradient. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 0.47 psi/ft
            air_gap (float): Distance from Drill Floor to Ground Level. Usually reported as Kelly bushing (KB) or Elevation Ground Level. Unit: Depth Unit [depth_unit]. Defaults to 0.0
            gradient_unit (str | None): Unit of the gradient inputs (e.g. "psi/ft", "kPa/m", "ppg", "SG"). Defaults to pressure_unit/depth_unit
            depth_unit (str): Unit of the depth inputs (e.g. "ft", "m"). Defaults to "ft"
            pressure_unit (str): Unit of the pressure output and gradient numerator (e.g. "psi", "kPa", "MPa"). Defaults to "psi"

        Returns:
            pore_pressure (list[float]): Pore pressure values for onshore setting. Unit: Pressure Unit [pressure_unit]"""
        return [
            PorePressureCalculation.calculate_pore_pressure_onshore(
                tvd=value,
                formation_pore_pressure_gradient=formation_pore_pressure_gradient,
                air_gap=air_gap,
                gradient_unit=gradient_unit,
                depth_unit=depth_unit,
                pressure_unit=pressure_unit,
            )
            for value in tvd
        ]

    @staticmethod
    def calculate_pore_pressure_offshore_array(tvd: list[float], formation_pore_pressure_gradient: float | None = None, air_gap: float = 0.0, water_depth: float = 0.0, sea_water_pressure_gradient: float | None = None, gradient_unit: str | None = None, depth_unit: str = "ft", pressure_unit: str = "psi") -> list[float]:
        """Calculates pore pressure for an array of tvd values in offshore setting.

        Args:
            tvd (list[float]): True Vertical Depth values. Unit: Depth Unit [depth_unit]
            formation_pore_pressure_gradient (float | None): Pore pressure depth gradient. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 0.47 psi/ft
            air_gap (float): Distance from Drill Floor to mean sea level. Usually reported as Kelly bushing (KB). Unit: Depth Unit [depth_unit]. Defaults to 0.0
            water_depth (float): Water Depth measured from the mean sea level to sea bottom at well location. Unit: Depth Unit [depth_unit]. Defaults to 0.0
            sea_water_pressure_gradient (float | None): Water gradient of the sea water. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 0.47 psi/ft
            gradient_unit (str | None): Unit of the gradient inputs (e.g. "psi/ft", "kPa/m", "ppg", "SG"). Defaults to pressure_unit/depth_unit
            depth_unit (str): Unit of the depth inputs (e.g. "ft", "m"). Defaults to "ft"
            pressure_unit (str): Unit of the pressure output and gradient numerators (e.g. "psi", "kPa", "MPa"). Defaults to "psi"

        Returns:
            pore_pressure (list[float]): Pore pressure values for offshore setting. Unit: Pressure Unit [pressure_unit]"""
        return [
            PorePressureCalculation.calculate_pore_pressure_offshore(
                tvd=value,
                formation_pore_pressure_gradient=formation_pore_pressure_gradient,
                air_gap=air_gap,
                water_depth=water_depth,
                sea_water_pressure_gradient=sea_water_pressure_gradient,
                gradient_unit=gradient_unit,
                depth_unit=depth_unit,
                pressure_unit=pressure_unit,
            )
            for value in tvd
        ]
