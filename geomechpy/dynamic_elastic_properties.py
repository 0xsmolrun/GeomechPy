from dataclasses import dataclass

from geomechpy.elastic_properties import ElasticPropertiesConverter


@dataclass(frozen=True)
class DynamicElasticProperties:
    """Dynamic elastic properties model per depth computed from acoustic measurements and bulk density.

    Attributes:
        p_wave_velocity (float): Compressional (P) wave velocity. Unit: [m/s]
        s_wave_velocity (float): Shear (S) wave velocity. Unit: [m/s]
        vp_vs_ratio (float): Ratio of compressional to shear velocity, a lithology and fluid indicator. Unit: unitless
        bulk_modulus (float): Dynamic bulk modulus, resistance of the rock to bulk compression. Unit: Pascal [Pa]
        youngs_modulus (float): Dynamic Young's modulus, tensile/compressive stiffness under lengthwise load. Unit: Pascal [Pa]
        lame_parameter (float): Dynamic Lame parameter (first Lame constant, λ). Unit: Pascal [Pa]
        shear_modulus (float): Dynamic shear modulus, ratio of shear stress to shear strain. Unit: Pascal [Pa]
        poissons_ratio (float): Dynamic Poisson's ratio, lateral to axial strain ratio. Unit: unitless
        p_wave_modulus (float): Dynamic P-wave modulus (constrained modulus, M). Unit: Pascal [Pa]"""

    p_wave_velocity: float
    s_wave_velocity: float
    vp_vs_ratio: float
    bulk_modulus: float
    youngs_modulus: float
    lame_parameter: float
    shear_modulus: float
    poissons_ratio: float
    p_wave_modulus: float


class DynamicElasticPropertiesCalculation:
    """Computation of dynamic elastic moduli from acoustic velocities or sonic slownesses and bulk density.

    The shear and P-wave moduli follow directly from the wave velocities and density
    (G = rho * Vs^2, M = rho * Vp^2); all remaining moduli are derived via
    `ElasticPropertiesConverter`.

    Reference:
        Mavko, Gary, Tapan Mukerji, and Jack Dvorkin. The rock physics handbook. Cambridge university press, 2020. Chapter 2.2.
        Fjaer, Erling, et al. Petroleum related rock mechanics. Vol. 53. Elsevier, 2008. Chapter 5."""

    @staticmethod
    def convert_slowness_to_velocity(slowness: float) -> float:
        """Convert sonic slowness to velocity.

        Args:
            slowness (float): Sonic slowness (e.g. DTCO or DTSH log). Unit: [us/ft]

        Returns:
            velocity (float): Wave velocity. Unit: [m/s]"""
        velocity = 304800 / slowness

        return float(velocity)

    @staticmethod
    def convert_velocity_to_slowness(velocity: float) -> float:
        """Convert wave velocity to sonic slowness.

        Args:
            velocity (float): Wave velocity. Unit: [m/s]

        Returns:
            slowness (float): Sonic slowness. Unit: [us/ft]"""
        slowness = 304800 / velocity

        return float(slowness)

    @staticmethod
    def calculate_from_velocity(p_wave_velocity: float, s_wave_velocity: float, density: float) -> DynamicElasticProperties:
        """Calculate dynamic elastic properties from P and S wave velocities and bulk density.

        Args:
            p_wave_velocity (float): Compressional (P) wave velocity. Unit: [m/s]
            s_wave_velocity (float): Shear (S) wave velocity. Unit: [m/s]
            density (float): Bulk density. Unit: [kg/m3]

        Returns:
            DynamicElasticProperties: Dataclass containing velocities, Vp/Vs ratio and dynamic elastic moduli. See `DynamicElasticProperties` for details. Unit: Pascal [Pa]"""
        shear_modulus = density * s_wave_velocity**2
        p_wave_modulus = density * p_wave_velocity**2

        elastic_properties = ElasticPropertiesConverter.convert_from_shear_and_p_wave(shear_modulus, p_wave_modulus)
        vp_vs_ratio = p_wave_velocity / s_wave_velocity

        return DynamicElasticProperties(
            p_wave_velocity=p_wave_velocity,
            s_wave_velocity=s_wave_velocity,
            vp_vs_ratio=vp_vs_ratio,
            bulk_modulus=elastic_properties.bulk_modulus,
            youngs_modulus=elastic_properties.youngs_modulus,
            lame_parameter=elastic_properties.lame_parameter,
            shear_modulus=elastic_properties.shear_modulus,
            poissons_ratio=elastic_properties.poissons_ratio,
            p_wave_modulus=elastic_properties.p_wave_modulus,
        )

    @staticmethod
    def calculate_from_slowness(p_wave_slowness: float, s_wave_slowness: float, density: float) -> DynamicElasticProperties:
        """Calculate dynamic elastic properties from P and S wave slownesses (sonic log) and bulk density.

        Args:
            p_wave_slowness (float): Compressional slowness (DTCO log). Unit: [us/ft]
            s_wave_slowness (float): Shear slowness (DTSH log). Unit: [us/ft]
            density (float): Bulk density. Unit: [kg/m3]

        Returns:
            DynamicElasticProperties: Dataclass containing velocities, Vp/Vs ratio and dynamic elastic moduli. See `DynamicElasticProperties` for details. Unit: Pascal [Pa]"""
        p_wave_velocity = DynamicElasticPropertiesCalculation.convert_slowness_to_velocity(p_wave_slowness)
        s_wave_velocity = DynamicElasticPropertiesCalculation.convert_slowness_to_velocity(s_wave_slowness)

        return DynamicElasticPropertiesCalculation.calculate_from_velocity(p_wave_velocity, s_wave_velocity, density)

    @staticmethod
    def convert_slowness_to_velocity_array(slowness: list[float]) -> list[float]:
        """Convert an array of sonic slowness values to velocities.

        Args:
            slowness (list[float]): Sonic slowness values. Unit: [us/ft]

        Returns:
            velocity (list[float]): Wave velocity values. Unit: [m/s]"""
        return [
            DynamicElasticPropertiesCalculation.convert_slowness_to_velocity(slowness=value)
            for value in slowness
        ]

    @staticmethod
    def convert_velocity_to_slowness_array(velocity: list[float]) -> list[float]:
        """Convert an array of wave velocity values to sonic slownesses.

        Args:
            velocity (list[float]): Wave velocity values. Unit: [m/s]

        Returns:
            slowness (list[float]): Sonic slowness values. Unit: [us/ft]"""
        return [
            DynamicElasticPropertiesCalculation.convert_velocity_to_slowness(velocity=value)
            for value in velocity
        ]

    @staticmethod
    def calculate_from_velocity_array(p_wave_velocity: list[float], s_wave_velocity: list[float], density: list[float]) -> list[DynamicElasticProperties]:
        """Calculate dynamic elastic properties for arrays of P/S wave velocities and bulk density.

        Args:
            p_wave_velocity (list[float]): Compressional velocity values. Unit: [m/s]
            s_wave_velocity (list[float]): Shear velocity values. Unit: [m/s]
            density (list[float]): Bulk density values. Unit: [kg/m3]

        Returns:
            list[DynamicElasticProperties]: Computed dynamic elastic properties for each input set."""
        return [
            DynamicElasticPropertiesCalculation.calculate_from_velocity(vp, vs, rho)
            for vp, vs, rho in zip(p_wave_velocity, s_wave_velocity, density, strict=True)
        ]

    @staticmethod
    def calculate_from_slowness_array(p_wave_slowness: list[float], s_wave_slowness: list[float], density: list[float]) -> list[DynamicElasticProperties]:
        """Calculate dynamic elastic properties for arrays of P/S wave slownesses and bulk density.

        Args:
            p_wave_slowness (list[float]): Compressional slowness values (DTCO log). Unit: [us/ft]
            s_wave_slowness (list[float]): Shear slowness values (DTSH log). Unit: [us/ft]
            density (list[float]): Bulk density values. Unit: [kg/m3]

        Returns:
            list[DynamicElasticProperties]: Computed dynamic elastic properties for each input set."""
        return [
            DynamicElasticPropertiesCalculation.calculate_from_slowness(dtp, dts, rho)
            for dtp, dts, rho in zip(p_wave_slowness, s_wave_slowness, density, strict=True)
        ]
