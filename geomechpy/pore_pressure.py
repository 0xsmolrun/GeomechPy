from dataclasses import dataclass


class PorePressureCalculation:
    """Computation of the Pore Pressure using gradient based methods.

    Reference:
       Zhang, Jon Jincai. Applied petroleum geomechanics. Vol. 1. Cambridge: Gulf Professional Publishing, 2019. Chapter 6.1"""

    @staticmethod
    def calculate_pore_pressure_onshore(tvd: float, formation_pore_pressure_gradient: float = 0.47, air_gap: float = 0.0) -> float:
        """Calculates pore pressure from tvd and pore pressure gradient in onshore setting.

        Args:
            tvd (float): True Vertical Depth. Unit: Depth Unit [ft]
            formation_pore_pressure_gradient (float): Pore pressure depth gradient. Unit: Depth Gradient Unit [psi/ft]. Defaults to 0.47
            air_gap (float): Distance from Drill Floor to Ground Level. Usually reported as Kelly bushing (KB) or Elevation Ground Level. Unit: Depth Unit [ft]. Defaults to 0.0

        Returns:
            pore_pressure (float): Pore pressure for onshore setting. Unit: Pressure Unit [psi]"""
        air_gradient = 0.0004
        air_pressure = air_gradient * air_gap
        if tvd >= 0 and tvd < air_gap:
            pore_pressure = air_gradient * tvd
        else:
            pore_pressure = air_pressure + formation_pore_pressure_gradient * (tvd - air_gap)

        return pore_pressure

    @staticmethod
    def calculate_pore_pressure_offshore(tvd: float, formation_pore_pressure_gradient: float = 0.47, air_gap: float = 0.0, water_depth: float = 0.0, sea_water_pressure_gradient: float = 0.47) -> float:
        """Calculates pore pressure from tvd and pore pressure gradient in offshore setting.

        Args:
            tvd (float): True Vertical Depth. Unit: Depth Unit [ft]
            formation_pore_pressure_gradient (float): Pore pressure depth gradient. Unit: Depth Gradient Unit [psi/ft]. Defaults to 0.47
            air_gap (float): Distance from Drill Floor to mean sea level. Usually reported as Kelly bushing (KB). Unit: Depth Unit [ft]. Defaults to 0.0 ft
            water_depth (float): Water Depth measured from the mean sea level to sea bottom at well location. Unit: Depth Unit [ft]. Defaults to 0.0 ft
            sea_water_pressure_gradient (float): Water gradient of the sea water. Unit: Depth Gradient Unit [psi/ft]. Defaults to 0.47 psi/ft

        Returns:
            pore_pressure (float): Pore pressure for offshore setting. Unit: Pressure Unit [psi]"""
        air_gradient = 0.0004
        air_pressure = air_gradient * air_gap

        water_pressure = sea_water_pressure_gradient * water_depth

        if tvd >= 0 and tvd < air_gap:
            pore_pressure = air_gradient * tvd
        elif tvd >= air_gap and tvd <= (air_gap + water_depth):
            pore_pressure = air_pressure + sea_water_pressure_gradient * (tvd - air_gap)
        else:
            pore_pressure = air_pressure + water_pressure + formation_pore_pressure_gradient * (tvd - water_depth - air_gap)

        return pore_pressure

    @staticmethod
    def calculate_pore_pressure_onshore_array(tvd: list[float], formation_pore_pressure_gradient: float = 0.47, air_gap: float = 0.0) -> list[float]:
        """Calculates pore pressure for an array of tvd values in onshore setting.

        Args:
            tvd (list[float]): True Vertical Depth values. Unit: Depth Unit [ft]
            formation_pore_pressure_gradient (float): Pore pressure depth gradient. Unit: Depth Gradient Unit [psi/ft]. Defaults to 0.47
            air_gap (float): Distance from Drill Floor to Ground Level. Usually reported as Kelly bushing (KB) or Elevation Ground Level. Unit: Depth Unit [ft]. Defaults to 0.0

        Returns:
            pore_pressure (list[float]): Pore pressure values for onshore setting. Unit: Pressure Unit [psi]"""
        return [
            PorePressureCalculation.calculate_pore_pressure_onshore(
                tvd=value,
                formation_pore_pressure_gradient=formation_pore_pressure_gradient,
                air_gap=air_gap,
            )
            for value in tvd
        ]

    @staticmethod
    def calculate_pore_pressure_offshore_array(tvd: list[float], formation_pore_pressure_gradient: float = 0.47, air_gap: float = 0.0, water_depth: float = 0.0, sea_water_pressure_gradient: float = 0.47) -> list[float]:
        """Calculates pore pressure for an array of tvd values in offshore setting.

        Args:
            tvd (list[float]): True Vertical Depth values. Unit: Depth Unit [ft]
            formation_pore_pressure_gradient (float): Pore pressure depth gradient. Unit: Depth Gradient Unit [psi/ft]. Defaults to 0.47
            air_gap (float): Distance from Drill Floor to mean sea level. Usually reported as Kelly bushing (KB). Unit: Depth Unit [ft]. Defaults to 0.0 ft
            water_depth (float): Water Depth measured from the mean sea level to sea bottom at well location. Unit: Depth Unit [ft]. Defaults to 0.0 ft
            sea_water_pressure_gradient (float): Water gradient of the sea water. Unit: Depth Gradient Unit [psi/ft]. Defaults to 0.47 psi/ft

        Returns:
            pore_pressure (list[float]): Pore pressure values for offshore setting. Unit: Pressure Unit [psi]"""
        return [
            PorePressureCalculation.calculate_pore_pressure_offshore(
                tvd=value,
                formation_pore_pressure_gradient=formation_pore_pressure_gradient,
                air_gap=air_gap,
                water_depth=water_depth,
                sea_water_pressure_gradient=sea_water_pressure_gradient,
            )
            for value in tvd
        ]
