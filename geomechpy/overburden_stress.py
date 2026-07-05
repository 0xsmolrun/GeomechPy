import math


class OverburdenStressCalculation:
    """Computation of the Overburden Stress using various methods based on gradient, density.

    Reference:
       Zhang, Jon Jincai. Applied petroleum geomechanics. Vol. 1. Cambridge: Gulf Professional Publishing, 2019. Chapter 6.1"""

    @staticmethod
    def calculate_overburden_stress_onshore(tvd: float, lithostatic_gradient: float = 1.05, air_gap: float = 0.0) -> float:
        """Calculates overburden stress (vertical stress) from tvd and lithostatic gradient in onshore setting.

        Args:
            tvd (float): True Vertical Depth. Unit: Depth Unit [ft]
            lithostatic_gradient (float): Overburden stress depth gradient. Unit: Depth Gradient Unit [psi/ft]. Defaults to 1.05
            air_gap (float): Distance from Drill Floor to Ground LEvel. Usually reported as Kelly bushing (KB) or Elevation Ground Level. Unit: Depth Unit [ft]. Defaults to 0.0

        Returns:
            overburden_stress (float): Overburden stress for onshore setting. Unit: Pressure Unit [psi]"""
        air_gradient = 0.0004
        air_pressure = air_gradient * air_gap

        if tvd >= 0 and tvd < air_gap:
            overburden_stress = air_gradient * tvd
        else:
            overburden_stress = air_pressure + lithostatic_gradient * (tvd - air_gap)

        return overburden_stress

    @staticmethod
    def calculate_overburden_stress_offshore(tvd: float, lithostatic_gradient: float = 1.05, air_gap: float = 0.0, water_depth: float = 0.0, sea_water_pressure_gradient: float = 0.47) -> float:
        """Calculates overburden stress (vertical stress) from tvd and lithostatic gradient in offshore setting.

        Args:
            tvd (float): True Vertical Depth. Unit: Depth Unit [ft]
            lithostatic_gradient (float): Overburden stress depth gradient. Unit: Depth Gradient Unit [psi/ft]. Defaults to 1.05 psi/ft
            air_gap (float): Distance from Drill Floor to mean sea level. Usually reported as Kelly bushing (KB). Unit: Depth Unit [ft]. Defaults to 0.0 ft
            water_depth (float): Water Depth measured from the mean sea level to sea bottom at well location. Unit: Depth Unit [ft]. Defaults to 0.0 ft
            sea_water_pressure_gradient (float): Water gradient of the sea water. Unit: Depth Gradient Unit [psi/ft]. Defaults to 0.47 psi/ft

        Returns:
            overburden_stress (float): Overburden stress for offshore setting. Unit: Pressure Unit [psi]"""
        air_gradient = 0.0004
        air_pressure = air_gradient * air_gap

        water_pressure = sea_water_pressure_gradient * water_depth

        if tvd >= 0 and tvd < air_gap:
            overburden_stress = air_gradient * tvd
        elif tvd >= air_gap and tvd <= (air_gap + water_depth):
            overburden_stress = air_pressure + sea_water_pressure_gradient * (tvd - air_gap)
        else:
            overburden_stress = air_pressure + water_pressure + lithostatic_gradient * (tvd - water_depth - air_gap)

        return overburden_stress

    @staticmethod
    def calculate_overburden_stress_onshore_array(tvd: list[float], lithostatic_gradient: float = 1.05, air_gap: float = 0.0) -> list[float]:
        """Calculates overburden stress for an array of tvd values in onshore setting.

        Args:
            tvd (list[float]): True Vertical Depth values. Unit: Depth Unit [ft]
            lithostatic_gradient (float): Overburden stress depth gradient. Unit: Depth Gradient Unit [psi/ft]. Defaults to 1.05
            air_gap (float): Distance from Drill Floor to Ground Level. Usually reported as Kelly bushing (KB) or Elevation Ground Level. Unit: Depth Unit [ft]. Defaults to 0.0

        Returns:
            overburden_stress (list[float]): Overburden stress values for onshore setting. Unit: Pressure Unit [psi]"""
        return [
            OverburdenStressCalculation.calculate_overburden_stress_onshore(
                tvd=value,
                lithostatic_gradient=lithostatic_gradient,
                air_gap=air_gap,
            )
            for value in tvd
        ]

    @staticmethod
    def calculate_overburden_stress_offshore_array(tvd: list[float], lithostatic_gradient: float = 1.05, air_gap: float = 0.0, water_depth: float = 0.0, sea_water_pressure_gradient: float = 0.47) -> list[float]:
        """Calculates overburden stress for an array of tvd values in offshore setting.

        Args:
            tvd (list[float]): True Vertical Depth values. Unit: Depth Unit [ft]
            lithostatic_gradient (float): Overburden stress depth gradient. Unit: Depth Gradient Unit [psi/ft]. Defaults to 1.05 psi/ft
            air_gap (float): Distance from Drill Floor to mean sea level. Usually reported as Kelly bushing (KB). Unit: Depth Unit [ft]. Defaults to 0.0 ft
            water_depth (float): Water Depth measured from the mean sea level to sea bottom at well location. Unit: Depth Unit [ft]. Defaults to 0.0 ft
            sea_water_pressure_gradient (float): Water gradient of the sea water. Unit: Depth Gradient Unit [psi/ft]. Defaults to 0.47 psi/ft

        Returns:
            overburden_stress (list[float]): Overburden stress values for offshore setting. Unit: Pressure Unit [psi]"""
        return [
            OverburdenStressCalculation.calculate_overburden_stress_offshore(
                tvd=value,
                lithostatic_gradient=lithostatic_gradient,
                air_gap=air_gap,
                water_depth=water_depth,
                sea_water_pressure_gradient=sea_water_pressure_gradient,
            )
            for value in tvd
        ]
