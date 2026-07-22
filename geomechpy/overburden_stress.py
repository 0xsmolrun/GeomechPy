from geomechpy.units import STANDARD_GRAVITY, UnitConverter


class OverburdenStressCalculation:
    """Computation of the Overburden Stress using various methods based on gradient, density.

    All methods accept optional `depth_unit`, `pressure_unit` and `gradient_unit` arguments:
    depths are interpreted in `depth_unit`, results are returned in `pressure_unit`, and
    gradients are interpreted in `gradient_unit` — either a `<pressure>/<depth>` combination
    (e.g. "psi/ft", "kPa/m") or an equivalent mud weight unit (e.g. "ppg", "SG"). When
    `gradient_unit` is omitted, gradients default to `pressure_unit`/`depth_unit`.
    Defaults are field units (ft, psi, psi/ft).

    Reference:
       Zhang, Jon Jincai. Applied petroleum geomechanics. Vol. 1. Cambridge: Gulf Professional Publishing, 2019. Chapter 6.1"""

    @staticmethod
    def calculate_overburden_stress_onshore(tvd: float, lithostatic_gradient: float | None = None, air_gap: float = 0.0, gradient_unit: str | None = None, depth_unit: str = "ft", pressure_unit: str = "psi") -> float:
        """Calculates overburden stress (vertical stress) from tvd and lithostatic gradient in onshore setting.

        Args:
            tvd (float): True Vertical Depth. Unit: Depth Unit [depth_unit]
            lithostatic_gradient (float | None): Overburden stress depth gradient. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 1.05 psi/ft
            air_gap (float): Distance from Drill Floor to Ground Level. Usually reported as Kelly bushing (KB) or Elevation Ground Level. Unit: Depth Unit [depth_unit]. Defaults to 0.0
            gradient_unit (str | None): Unit of the gradient inputs (e.g. "psi/ft", "kPa/m", "ppg", "SG"). Defaults to pressure_unit/depth_unit
            depth_unit (str): Unit of the depth inputs (e.g. "ft", "m"). Defaults to "ft"
            pressure_unit (str): Unit of the pressure output and gradient numerator (e.g. "psi", "kPa", "MPa"). Defaults to "psi"

        Returns:
            overburden_stress (float): Overburden stress for onshore setting. Unit: Pressure Unit [pressure_unit]

        Example:
            >>> OverburdenStressCalculation.calculate_overburden_stress_onshore(tvd=10000.0)
            10500.0"""
        if tvd < 0:
            raise ValueError(f"tvd must be non-negative, got {tvd}")
        if air_gap < 0:
            raise ValueError("air_gap must be non-negative")
        if gradient_unit is None:
            gradient_unit = f"{pressure_unit}/{depth_unit}"
        tvd = UnitConverter.convert_depth(tvd, depth_unit, "ft")
        air_gap = UnitConverter.convert_depth(air_gap, depth_unit, "ft")
        if lithostatic_gradient is None:
            lithostatic_gradient = 1.05
        else:
            lithostatic_gradient = UnitConverter.convert_pressure_gradient(lithostatic_gradient, gradient_unit, "psi/ft")

        air_gradient = 0.0004
        air_pressure = air_gradient * air_gap

        if tvd >= 0 and tvd < air_gap:
            overburden_stress = air_gradient * tvd
        else:
            overburden_stress = air_pressure + lithostatic_gradient * (tvd - air_gap)

        return UnitConverter.convert_pressure(overburden_stress, "psi", pressure_unit)

    @staticmethod
    def calculate_overburden_stress_offshore(tvd: float, lithostatic_gradient: float | None = None, air_gap: float = 0.0, water_depth: float = 0.0, sea_water_pressure_gradient: float | None = None, gradient_unit: str | None = None, depth_unit: str = "ft", pressure_unit: str = "psi") -> float:
        """Calculates overburden stress (vertical stress) from tvd and lithostatic gradient in offshore setting.

        Args:
            tvd (float): True Vertical Depth. Unit: Depth Unit [depth_unit]
            lithostatic_gradient (float | None): Overburden stress depth gradient. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 1.05 psi/ft
            air_gap (float): Distance from Drill Floor to mean sea level. Usually reported as Kelly bushing (KB). Unit: Depth Unit [depth_unit]. Defaults to 0.0
            water_depth (float): Water Depth measured from the mean sea level to sea bottom at well location. Unit: Depth Unit [depth_unit]. Defaults to 0.0
            sea_water_pressure_gradient (float | None): Water gradient of the sea water. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 0.47 psi/ft
            gradient_unit (str | None): Unit of the gradient inputs (e.g. "psi/ft", "kPa/m", "ppg", "SG"). Defaults to pressure_unit/depth_unit
            depth_unit (str): Unit of the depth inputs (e.g. "ft", "m"). Defaults to "ft"
            pressure_unit (str): Unit of the pressure output and gradient numerators (e.g. "psi", "kPa", "MPa"). Defaults to "psi"

        Returns:
            overburden_stress (float): Overburden stress for offshore setting. Unit: Pressure Unit [pressure_unit]"""
        if tvd < 0:
            raise ValueError(f"tvd must be non-negative, got {tvd}")
        if air_gap < 0 or water_depth < 0:
            raise ValueError("air_gap and water_depth must be non-negative")
        if gradient_unit is None:
            gradient_unit = f"{pressure_unit}/{depth_unit}"
        tvd = UnitConverter.convert_depth(tvd, depth_unit, "ft")
        air_gap = UnitConverter.convert_depth(air_gap, depth_unit, "ft")
        water_depth = UnitConverter.convert_depth(water_depth, depth_unit, "ft")
        if lithostatic_gradient is None:
            lithostatic_gradient = 1.05
        else:
            lithostatic_gradient = UnitConverter.convert_pressure_gradient(lithostatic_gradient, gradient_unit, "psi/ft")
        if sea_water_pressure_gradient is None:
            sea_water_pressure_gradient = 0.47
        else:
            sea_water_pressure_gradient = UnitConverter.convert_pressure_gradient(sea_water_pressure_gradient, gradient_unit, "psi/ft")

        air_gradient = 0.0004
        air_pressure = air_gradient * air_gap

        water_pressure = sea_water_pressure_gradient * water_depth

        if tvd >= 0 and tvd < air_gap:
            overburden_stress = air_gradient * tvd
        elif tvd >= air_gap and tvd <= (air_gap + water_depth):
            overburden_stress = air_pressure + sea_water_pressure_gradient * (tvd - air_gap)
        else:
            overburden_stress = air_pressure + water_pressure + lithostatic_gradient * (tvd - water_depth - air_gap)

        return UnitConverter.convert_pressure(overburden_stress, "psi", pressure_unit)

    @staticmethod
    def calculate_overburden_stress_onshore_array(tvd: list[float], lithostatic_gradient: float | None = None, air_gap: float = 0.0, gradient_unit: str | None = None, depth_unit: str = "ft", pressure_unit: str = "psi") -> list[float]:
        """Calculates overburden stress for an array of tvd values in onshore setting.

        Args:
            tvd (list[float]): True Vertical Depth values. Unit: Depth Unit [depth_unit]
            lithostatic_gradient (float | None): Overburden stress depth gradient. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 1.05 psi/ft
            air_gap (float): Distance from Drill Floor to Ground Level. Usually reported as Kelly bushing (KB) or Elevation Ground Level. Unit: Depth Unit [depth_unit]. Defaults to 0.0
            gradient_unit (str | None): Unit of the gradient inputs (e.g. "psi/ft", "kPa/m", "ppg", "SG"). Defaults to pressure_unit/depth_unit
            depth_unit (str): Unit of the depth inputs (e.g. "ft", "m"). Defaults to "ft"
            pressure_unit (str): Unit of the pressure output and gradient numerator (e.g. "psi", "kPa", "MPa"). Defaults to "psi"

        Returns:
            overburden_stress (list[float]): Overburden stress values for onshore setting. Unit: Pressure Unit [pressure_unit]"""
        return [
            OverburdenStressCalculation.calculate_overburden_stress_onshore(
                tvd=value,
                lithostatic_gradient=lithostatic_gradient,
                air_gap=air_gap,
                gradient_unit=gradient_unit,
                depth_unit=depth_unit,
                pressure_unit=pressure_unit,
            )
            for value in tvd
        ]

    @staticmethod
    def calculate_overburden_stress_offshore_array(tvd: list[float], lithostatic_gradient: float | None = None, air_gap: float = 0.0, water_depth: float = 0.0, sea_water_pressure_gradient: float | None = None, gradient_unit: str | None = None, depth_unit: str = "ft", pressure_unit: str = "psi") -> list[float]:
        """Calculates overburden stress for an array of tvd values in offshore setting.

        Args:
            tvd (list[float]): True Vertical Depth values. Unit: Depth Unit [depth_unit]
            lithostatic_gradient (float | None): Overburden stress depth gradient. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 1.05 psi/ft
            air_gap (float): Distance from Drill Floor to mean sea level. Usually reported as Kelly bushing (KB). Unit: Depth Unit [depth_unit]. Defaults to 0.0
            water_depth (float): Water Depth measured from the mean sea level to sea bottom at well location. Unit: Depth Unit [depth_unit]. Defaults to 0.0
            sea_water_pressure_gradient (float | None): Water gradient of the sea water. Unit: Depth Gradient Unit [gradient_unit]. Defaults to the equivalent of 0.47 psi/ft
            gradient_unit (str | None): Unit of the gradient inputs (e.g. "psi/ft", "kPa/m", "ppg", "SG"). Defaults to pressure_unit/depth_unit
            depth_unit (str): Unit of the depth inputs (e.g. "ft", "m"). Defaults to "ft"
            pressure_unit (str): Unit of the pressure output and gradient numerators (e.g. "psi", "kPa", "MPa"). Defaults to "psi"

        Returns:
            overburden_stress (list[float]): Overburden stress values for offshore setting. Unit: Pressure Unit [pressure_unit]"""
        return [
            OverburdenStressCalculation.calculate_overburden_stress_offshore(
                tvd=value,
                lithostatic_gradient=lithostatic_gradient,
                air_gap=air_gap,
                water_depth=water_depth,
                sea_water_pressure_gradient=sea_water_pressure_gradient,
                gradient_unit=gradient_unit,
                depth_unit=depth_unit,
                pressure_unit=pressure_unit,
            )
            for value in tvd
        ]

    @staticmethod
    def calculate_overburden_stress_from_density_array(tvd: list[float], density: list[float], air_gap: float = 0.0, water_depth: float = 0.0, sea_water_density: float | None = None, depth_unit: str = "ft", density_unit: str = "kg/m3", pressure_unit: str = "psi") -> list[float]:
        """Calculates overburden stress by depth-integrating a bulk density profile.

        Integrates rho(z) * g over depth with the trapezoidal rule, which honors the actual
        density log instead of assuming a constant lithostatic gradient. The density between
        the mudline (or ground level) and the first sample is taken as the first sample's
        density. Offshore settings are handled by adding the sea water column above the
        mudline; the air gap contributes a negligible air column (0.0004 psi/ft).

        Reference:
           Zhang, Jon Jincai. Applied petroleum geomechanics. Vol. 1. Cambridge: Gulf Professional Publishing, 2019. Chapter 1.4 (sigma_v = integral of rho(z)*g dz).

        Args:
            tvd (list[float]): True Vertical Depth values, sorted in increasing order and all below the mudline (air_gap + water_depth). Unit: Depth Unit [depth_unit]
            density (list[float]): Bulk density values at each tvd. Unit: Density Unit [density_unit]
            air_gap (float): Distance from Drill Floor to Ground Level / mean sea level. Unit: Depth Unit [depth_unit]. Defaults to 0.0
            water_depth (float): Water Depth from mean sea level to sea bottom. Unit: Depth Unit [depth_unit]. Defaults to 0.0
            sea_water_density (float | None): Sea water density. Unit: Density Unit [density_unit]. Defaults to the equivalent of 1025 kg/m3
            depth_unit (str): Unit of the depth inputs (e.g. "ft", "m"). Defaults to "ft"
            density_unit (str): Unit of the density inputs (e.g. "kg/m3", "g/cm3"). Defaults to "kg/m3"
            pressure_unit (str): Unit of the overburden stress output (e.g. "psi", "kPa", "MPa"). Defaults to "psi"

        Returns:
            overburden_stress (list[float]): Overburden stress values at each tvd. Unit: Pressure Unit [pressure_unit]

        Raises:
            ValueError: If tvd and density lengths differ, tvd is not sorted in increasing order, or any tvd lies above the mudline.

        Example:
            >>> sv = OverburdenStressCalculation.calculate_overburden_stress_from_density_array(
            ...     tvd=[9000.0, 10000.0], density=[2500.0, 2600.0])
            >>> [round(value, 1) for value in sv]
            [9754.4, 10859.9]"""
        if len(tvd) != len(density):
            raise ValueError("tvd and density must have the same length")
        if len(tvd) == 0:
            return []

        tvd_m = UnitConverter.convert_depth_array(tvd, depth_unit, "m")
        density_si = UnitConverter.convert_density_array(density, density_unit, "kg/m3")
        air_gap_m = UnitConverter.convert_depth(air_gap, depth_unit, "m")
        water_depth_m = UnitConverter.convert_depth(water_depth, depth_unit, "m")
        if sea_water_density is None:
            sea_water_density_si = 1025.0
        else:
            sea_water_density_si = UnitConverter.convert_density(sea_water_density, density_unit, "kg/m3")

        mudline_m = air_gap_m + water_depth_m
        if any(later < earlier for earlier, later in zip(tvd_m, tvd_m[1:], strict=False)):
            raise ValueError("tvd must be sorted in increasing order")
        if tvd_m[0] < mudline_m:
            raise ValueError("all tvd values must lie below the mudline (air_gap + water_depth)")

        air_gradient_pa_per_m = UnitConverter.convert_pressure_gradient(0.0004, "psi/ft", "Pa/m")
        surface_pressure_pa = air_gradient_pa_per_m * air_gap_m + sea_water_density_si * STANDARD_GRAVITY * water_depth_m

        overburden_pa: list[float] = []
        # Constant density assumed from the mudline down to the first sample
        cumulative_pa = surface_pressure_pa + density_si[0] * STANDARD_GRAVITY * (tvd_m[0] - mudline_m)
        overburden_pa.append(cumulative_pa)
        for index in range(1, len(tvd_m)):
            interval_m = tvd_m[index] - tvd_m[index - 1]
            average_density = 0.5 * (density_si[index] + density_si[index - 1])
            cumulative_pa += average_density * STANDARD_GRAVITY * interval_m
            overburden_pa.append(cumulative_pa)

        return UnitConverter.convert_pressure_array(overburden_pa, "Pa", pressure_unit)
