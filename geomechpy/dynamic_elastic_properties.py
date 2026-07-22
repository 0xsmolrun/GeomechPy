from dataclasses import dataclass

from geomechpy.elastic_properties import ElasticPropertiesConverter
from geomechpy.units import UnitConverter


@dataclass(frozen=True)
class DynamicElasticProperties:
    """Dynamic elastic properties model per depth computed from acoustic measurements and bulk density.

    Attributes:
        p_wave_velocity (float): Compressional (P) wave velocity. Unit: velocity unit of the calculation (default [m/s])
        s_wave_velocity (float): Shear (S) wave velocity. Unit: velocity unit of the calculation (default [m/s])
        vp_vs_ratio (float): Ratio of compressional to shear velocity, a lithology and fluid indicator. Unit: unitless
        bulk_modulus (float): Dynamic bulk modulus, resistance of the rock to bulk compression. Unit: modulus unit of the calculation (default Pascal [Pa])
        youngs_modulus (float): Dynamic Young's modulus, tensile/compressive stiffness under lengthwise load. Unit: modulus unit of the calculation (default Pascal [Pa])
        lame_parameter (float): Dynamic Lame parameter (first Lame constant, λ). Unit: modulus unit of the calculation (default Pascal [Pa])
        shear_modulus (float): Dynamic shear modulus, ratio of shear stress to shear strain. Unit: modulus unit of the calculation (default Pascal [Pa])
        poissons_ratio (float): Dynamic Poisson's ratio, lateral to axial strain ratio. Unit: unitless
        p_wave_modulus (float): Dynamic P-wave modulus (constrained modulus, M). Unit: modulus unit of the calculation (default Pascal [Pa])"""

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

    All methods accept optional unit arguments (`velocity_unit`, `slowness_unit`,
    `density_unit`, `modulus_unit`); inputs are interpreted in and outputs returned in
    those units. Defaults are SI logging units (m/s, us/ft, kg/m3, Pa).

    Reference:
        Mavko, Gary, Tapan Mukerji, and Jack Dvorkin. The rock physics handbook. Cambridge university press, 2020. Chapter 2.2.
        Fjaer, Erling, et al. Petroleum related rock mechanics. Vol. 53. Elsevier, 2008. Chapter 5."""

    @staticmethod
    def convert_slowness_to_velocity(slowness: float, slowness_unit: str = "us/ft", velocity_unit: str = "m/s") -> float:
        """Convert sonic slowness to velocity.

        Args:
            slowness (float): Sonic slowness (e.g. DTCO or DTSH log). Unit: [slowness_unit]
            slowness_unit (str): Unit of the slowness input (e.g. "us/ft", "us/m"). Defaults to "us/ft"
            velocity_unit (str): Unit of the velocity output (e.g. "m/s", "ft/s"). Defaults to "m/s"

        Returns:
            velocity (float): Wave velocity. Unit: [velocity_unit]"""
        if slowness <= 0:
            raise ValueError(f"slowness must be positive, got {slowness}")
        slowness_s_per_m = UnitConverter.convert_slowness(slowness, slowness_unit, "s/m")
        velocity = 1 / slowness_s_per_m

        return UnitConverter.convert_velocity(velocity, "m/s", velocity_unit)

    @staticmethod
    def convert_velocity_to_slowness(velocity: float, velocity_unit: str = "m/s", slowness_unit: str = "us/ft") -> float:
        """Convert wave velocity to sonic slowness.

        Args:
            velocity (float): Wave velocity. Unit: [velocity_unit]
            velocity_unit (str): Unit of the velocity input (e.g. "m/s", "ft/s"). Defaults to "m/s"
            slowness_unit (str): Unit of the slowness output (e.g. "us/ft", "us/m"). Defaults to "us/ft"

        Returns:
            slowness (float): Sonic slowness. Unit: [slowness_unit]"""
        if velocity <= 0:
            raise ValueError(f"velocity must be positive, got {velocity}")
        velocity_m_per_s = UnitConverter.convert_velocity(velocity, velocity_unit, "m/s")
        slowness = 1 / velocity_m_per_s

        return UnitConverter.convert_slowness(slowness, "s/m", slowness_unit)

    @staticmethod
    def calculate_from_velocity(p_wave_velocity: float, s_wave_velocity: float, density: float, velocity_unit: str = "m/s", density_unit: str = "kg/m3", modulus_unit: str = "Pa") -> DynamicElasticProperties:
        """Calculate dynamic elastic properties from P and S wave velocities and bulk density.

        Args:
            p_wave_velocity (float): Compressional (P) wave velocity. Unit: [velocity_unit]
            s_wave_velocity (float): Shear (S) wave velocity. Unit: [velocity_unit]
            density (float): Bulk density. Unit: [density_unit]
            velocity_unit (str): Unit of the velocity inputs (e.g. "m/s", "ft/s"). Defaults to "m/s"
            density_unit (str): Unit of the density input (e.g. "kg/m3", "g/cm3"). Defaults to "kg/m3"
            modulus_unit (str): Unit of the elastic moduli output (e.g. "Pa", "GPa", "Mpsi"). Defaults to "Pa"

        Returns:
            DynamicElasticProperties: Dataclass containing velocities (in velocity_unit), Vp/Vs ratio and dynamic elastic moduli (in modulus_unit). See `DynamicElasticProperties` for details.

        Example:
            >>> props = DynamicElasticPropertiesCalculation.calculate_from_velocity(
            ...     p_wave_velocity=4000.0, s_wave_velocity=2400.0, density=2650.0, modulus_unit="GPa")
            >>> print(f"E = {props.youngs_modulus:.2f} GPa, PR = {props.poissons_ratio:.3f}, Vp/Vs = {props.vp_vs_ratio:.2f}")
            E = 37.21 GPa, PR = 0.219, Vp/Vs = 1.67"""
        if density <= 0:
            raise ValueError(f"density must be positive, got {density}")
        if p_wave_velocity <= 0 or s_wave_velocity <= 0:
            raise ValueError(f"velocities must be positive, got Vp={p_wave_velocity}, Vs={s_wave_velocity}")
        if p_wave_velocity / s_wave_velocity <= 2.0 / 3.0**0.5:
            raise ValueError(
                f"Vp/Vs = {p_wave_velocity / s_wave_velocity:.3f} is non-physical (must exceed 2/sqrt(3) ~ 1.155, otherwise the bulk modulus would be negative)"
            )
        p_wave_velocity_si = UnitConverter.convert_velocity(p_wave_velocity, velocity_unit, "m/s")
        s_wave_velocity_si = UnitConverter.convert_velocity(s_wave_velocity, velocity_unit, "m/s")
        density_si = UnitConverter.convert_density(density, density_unit, "kg/m3")

        shear_modulus = density_si * s_wave_velocity_si**2
        p_wave_modulus = density_si * p_wave_velocity_si**2

        elastic_properties = ElasticPropertiesConverter.convert_from_shear_and_p_wave(shear_modulus, p_wave_modulus)
        vp_vs_ratio = p_wave_velocity_si / s_wave_velocity_si

        return DynamicElasticProperties(
            p_wave_velocity=p_wave_velocity,
            s_wave_velocity=s_wave_velocity,
            vp_vs_ratio=vp_vs_ratio,
            bulk_modulus=UnitConverter.convert_pressure(elastic_properties.bulk_modulus, "Pa", modulus_unit),
            youngs_modulus=UnitConverter.convert_pressure(elastic_properties.youngs_modulus, "Pa", modulus_unit),
            lame_parameter=UnitConverter.convert_pressure(elastic_properties.lame_parameter, "Pa", modulus_unit),
            shear_modulus=UnitConverter.convert_pressure(elastic_properties.shear_modulus, "Pa", modulus_unit),
            poissons_ratio=elastic_properties.poissons_ratio,
            p_wave_modulus=UnitConverter.convert_pressure(elastic_properties.p_wave_modulus, "Pa", modulus_unit),
        )

    @staticmethod
    def calculate_from_slowness(p_wave_slowness: float, s_wave_slowness: float, density: float, slowness_unit: str = "us/ft", density_unit: str = "kg/m3", modulus_unit: str = "Pa", velocity_unit: str = "m/s") -> DynamicElasticProperties:
        """Calculate dynamic elastic properties from P and S wave slownesses (sonic log) and bulk density.

        Args:
            p_wave_slowness (float): Compressional slowness (DTCO log). Unit: [slowness_unit]
            s_wave_slowness (float): Shear slowness (DTSH log). Unit: [slowness_unit]
            density (float): Bulk density. Unit: [density_unit]
            slowness_unit (str): Unit of the slowness inputs (e.g. "us/ft", "us/m"). Defaults to "us/ft"
            density_unit (str): Unit of the density input (e.g. "kg/m3", "g/cm3"). Defaults to "kg/m3"
            modulus_unit (str): Unit of the elastic moduli output (e.g. "Pa", "GPa", "Mpsi"). Defaults to "Pa"
            velocity_unit (str): Unit of the velocities reported in the result (e.g. "m/s", "ft/s"). Defaults to "m/s"

        Returns:
            DynamicElasticProperties: Dataclass containing velocities (in velocity_unit), Vp/Vs ratio and dynamic elastic moduli (in modulus_unit). See `DynamicElasticProperties` for details.

        Example:
            >>> props = DynamicElasticPropertiesCalculation.calculate_from_slowness(
            ...     p_wave_slowness=76.2, s_wave_slowness=127.0, density=2650.0, modulus_unit="GPa")
            >>> print(f"E = {props.youngs_modulus:.2f} GPa")
            E = 37.21 GPa"""
        p_wave_velocity = DynamicElasticPropertiesCalculation.convert_slowness_to_velocity(p_wave_slowness, slowness_unit=slowness_unit, velocity_unit=velocity_unit)
        s_wave_velocity = DynamicElasticPropertiesCalculation.convert_slowness_to_velocity(s_wave_slowness, slowness_unit=slowness_unit, velocity_unit=velocity_unit)

        return DynamicElasticPropertiesCalculation.calculate_from_velocity(p_wave_velocity, s_wave_velocity, density, velocity_unit=velocity_unit, density_unit=density_unit, modulus_unit=modulus_unit)

    @staticmethod
    def convert_slowness_to_velocity_array(slowness: list[float], slowness_unit: str = "us/ft", velocity_unit: str = "m/s") -> list[float]:
        """Convert an array of sonic slowness values to velocities.

        Args:
            slowness (list[float]): Sonic slowness values. Unit: [slowness_unit]
            slowness_unit (str): Unit of the slowness inputs. Defaults to "us/ft"
            velocity_unit (str): Unit of the velocity outputs. Defaults to "m/s"

        Returns:
            velocity (list[float]): Wave velocity values. Unit: [velocity_unit]"""
        return [
            DynamicElasticPropertiesCalculation.convert_slowness_to_velocity(slowness=value, slowness_unit=slowness_unit, velocity_unit=velocity_unit)
            for value in slowness
        ]

    @staticmethod
    def convert_velocity_to_slowness_array(velocity: list[float], velocity_unit: str = "m/s", slowness_unit: str = "us/ft") -> list[float]:
        """Convert an array of wave velocity values to sonic slownesses.

        Args:
            velocity (list[float]): Wave velocity values. Unit: [velocity_unit]
            velocity_unit (str): Unit of the velocity inputs. Defaults to "m/s"
            slowness_unit (str): Unit of the slowness outputs. Defaults to "us/ft"

        Returns:
            slowness (list[float]): Sonic slowness values. Unit: [slowness_unit]"""
        return [
            DynamicElasticPropertiesCalculation.convert_velocity_to_slowness(velocity=value, velocity_unit=velocity_unit, slowness_unit=slowness_unit)
            for value in velocity
        ]

    @staticmethod
    def calculate_from_velocity_array(p_wave_velocity: list[float], s_wave_velocity: list[float], density: list[float], velocity_unit: str = "m/s", density_unit: str = "kg/m3", modulus_unit: str = "Pa") -> list[DynamicElasticProperties]:
        """Calculate dynamic elastic properties for arrays of P/S wave velocities and bulk density.

        Args:
            p_wave_velocity (list[float]): Compressional velocity values. Unit: [velocity_unit]
            s_wave_velocity (list[float]): Shear velocity values. Unit: [velocity_unit]
            density (list[float]): Bulk density values. Unit: [density_unit]
            velocity_unit (str): Unit of the velocity inputs. Defaults to "m/s"
            density_unit (str): Unit of the density inputs. Defaults to "kg/m3"
            modulus_unit (str): Unit of the elastic moduli outputs. Defaults to "Pa"

        Returns:
            list[DynamicElasticProperties]: Computed dynamic elastic properties for each input set."""
        return [
            DynamicElasticPropertiesCalculation.calculate_from_velocity(vp, vs, rho, velocity_unit=velocity_unit, density_unit=density_unit, modulus_unit=modulus_unit)
            for vp, vs, rho in zip(p_wave_velocity, s_wave_velocity, density, strict=True)
        ]

    @staticmethod
    def calculate_from_slowness_array(p_wave_slowness: list[float], s_wave_slowness: list[float], density: list[float], slowness_unit: str = "us/ft", density_unit: str = "kg/m3", modulus_unit: str = "Pa", velocity_unit: str = "m/s") -> list[DynamicElasticProperties]:
        """Calculate dynamic elastic properties for arrays of P/S wave slownesses and bulk density.

        Args:
            p_wave_slowness (list[float]): Compressional slowness values (DTCO log). Unit: [slowness_unit]
            s_wave_slowness (list[float]): Shear slowness values (DTSH log). Unit: [slowness_unit]
            density (list[float]): Bulk density values. Unit: [density_unit]
            slowness_unit (str): Unit of the slowness inputs. Defaults to "us/ft"
            density_unit (str): Unit of the density inputs. Defaults to "kg/m3"
            modulus_unit (str): Unit of the elastic moduli outputs. Defaults to "Pa"
            velocity_unit (str): Unit of the velocities reported in the results. Defaults to "m/s"

        Returns:
            list[DynamicElasticProperties]: Computed dynamic elastic properties for each input set."""
        return [
            DynamicElasticPropertiesCalculation.calculate_from_slowness(dtp, dts, rho, slowness_unit=slowness_unit, density_unit=density_unit, modulus_unit=modulus_unit, velocity_unit=velocity_unit)
            for dtp, dts, rho in zip(p_wave_slowness, s_wave_slowness, density, strict=True)
        ]
