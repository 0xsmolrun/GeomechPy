import math
from dataclasses import dataclass

from geomechpy.units import UnitConverter


@dataclass(frozen=True)
class ElasticProperties:
    """Elastic properties model per depth. Can be populated manually or via converter.

    Attributes:
        bulk_modulus (float): The bulk modulus (K or B or k) of a substance is a measure of the resistance of a substance to bulk compression. Unit: Pressure
        youngs_modulus (float): Young modulus is a mechanical property of solid materials that measures the tensile or compressive stiffness when the force is applied lengthwise. Unit: Pressure
        lame_parameter (float): Lame parameters is a material-dependent quantity denoted by λ which arises in strain-stress relationships. Unit: Pressure
        shear_modulus (float): Shear modulus is a measure of the elastic shear stiffness of a material and is defined as the ratio of shear stress to the shear strain. Unit: Pressure
        poissons_ratio (float): Poisson's ratio is a measure of the Poisson effect, the deformation of a material in directions perpendicular to the specific direction of loading. Unit: unitless
        p_wave_modulus (float): P-wave modulus is one of the elastic moduli available to describe isotropic homogeneous materials. Unit: Pressure"""

    bulk_modulus: float
    youngs_modulus: float
    lame_parameter: float
    shear_modulus: float
    poissons_ratio: float
    p_wave_modulus: float


class ElasticPropertiesConverter:
    """Convert any pair of two elastic properties into all other types of elastic property notations.

    The pairwise `convert_from_*` methods are unit-agnostic: any consistent pressure unit
    (GPa, psi, Mpsi, ...) may be used and results are returned in that same unit. The
    velocity/slowness-based methods accept explicit unit arguments.

    Reference:
        https://en.wikipedia.org/wiki/Elastic_modulus"""

    @staticmethod
    def convert_from_bulk_and_youngs(bulk_modulus: float, youngs_modulus: float) -> ElasticProperties:
        """Convert Bulk and Youngs modulus to other elastic property types.

        Input Unit: Pressure Unit of any type (GPa, psi, Mpsi etc). Pressure unit of both inputs needs to be consistent.

        Args:
            bulk_modulus (float): Bulk modulus magnitude Unit: Pressure Unit
            youngs_modulus (float): Young modulus magnitude Unit: Pressure Unit

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        lame_parameter = 3 * bulk_modulus * (3 * bulk_modulus - youngs_modulus) / (9 * bulk_modulus - youngs_modulus)
        shear_modulus = 3 * bulk_modulus * youngs_modulus / (9 * bulk_modulus - youngs_modulus)
        poissons_ratio = (3 * bulk_modulus - youngs_modulus) / (6 * bulk_modulus)
        p_wave_modulus = 3 * bulk_modulus * (3 * bulk_modulus + youngs_modulus) / (9 * bulk_modulus - youngs_modulus)

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_bulk_and_lame(bulk_modulus: float, lame_parameter: float) -> ElasticProperties:
        """Convert Bulk modulus and Lame parameter to other elastic property types.

        Input Unit: Pressure Unit of any type (GPa, psi, Mpsi etc). Pressure unit of both inputs needs to be consistent.

        Args:
            bulk_modulus (float): Bulk modulus magnitude Unit: Pressure Unit
            lame_parameter (float): Lame parameter magnitude Unit: Pressure Unit

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        youngs_modulus = 9 * bulk_modulus * (bulk_modulus - lame_parameter) / (3 * bulk_modulus - lame_parameter)
        shear_modulus = 3 * (bulk_modulus - lame_parameter) / 2
        poissons_ratio = lame_parameter / (3 * bulk_modulus - lame_parameter)
        p_wave_modulus = 3 * bulk_modulus - 2 * lame_parameter

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_bulk_and_shear(bulk_modulus: float, shear_modulus: float) -> ElasticProperties:
        """Convert Bulk modulus and Shear modulus to other elastic property types.

        Input Unit: Pressure Unit of any type (GPa, psi, Mpsi etc). Pressure unit of both inputs needs to be consistent.

        Args:
            bulk_modulus (float): Bulk modulus magnitude Unit: Pressure Unit
            shear_modulus (float): Shear modulus magnitude Unit: Pressure Unit

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        youngs_modulus = 9 * bulk_modulus * shear_modulus / (3 * bulk_modulus + shear_modulus)
        lame_parameter = bulk_modulus - 2 * shear_modulus / 3
        poissons_ratio = (3 * bulk_modulus - 2 * shear_modulus) / (2 * (3 * bulk_modulus + shear_modulus))
        p_wave_modulus = bulk_modulus + 4 * shear_modulus / 3

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_bulk_and_poissons(bulk_modulus: float, poissons_ratio: float) -> ElasticProperties:
        """Convert Bulk modulus and Poisson's ratio to other elastic property types.

        Input Unit: Bulk modulus - pressure unit, Poisson's ratio - unitless.

        Args:
            bulk_modulus (float): Bulk modulus magnitude Unit: Pressure Unit
            poissons_ratio (float): Young modulus magnitude Unit: Unitless

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        youngs_modulus = 3 * bulk_modulus * (1 - 2 * poissons_ratio)
        lame_parameter = 3 * bulk_modulus * poissons_ratio / (1 + poissons_ratio)
        shear_modulus = 3 * bulk_modulus * (1 - 2 * poissons_ratio) / (2 * (1 + poissons_ratio))
        p_wave_modulus = 3 * bulk_modulus * (1 - poissons_ratio) / (1 + poissons_ratio)

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_bulk_and_p_wave(bulk_modulus: float, p_wave_modulus: float) -> ElasticProperties:
        """Convert Bulk and P-wave modulus to other elastic property types.

        Input Unit: Pressure Unit of any type (GPa, psi, Mpsi etc). Pressure unit of both inputs needs to be consistent.

        Args:
            bulk_modulus (float): Bulk modulus magnitude Unit: Pressure Unit
            p_wave_modulus (float): P-wave modulus magnitude Unit: Pressure Unit

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        youngs_modulus = 9 * bulk_modulus * (p_wave_modulus - bulk_modulus) / (3 * bulk_modulus + p_wave_modulus)
        lame_parameter = (3 * bulk_modulus - p_wave_modulus) / 2
        shear_modulus = (3 * (p_wave_modulus - bulk_modulus)) / 4
        poissons_ratio = (3 * bulk_modulus - p_wave_modulus) / (3 * bulk_modulus + p_wave_modulus)

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_youngs_and_lame(youngs_modulus: float, lame_parameter: float) -> ElasticProperties:
        """Convert Young's modulus and Lame parameter to other elastic property types.

        Input Unit: Pressure Unit of any type (GPa, psi, Mpsi etc). Pressure unit of both inputs needs to be consistent.

        Args:
            youngs_modulus (float): Young's modulus magnitude Unit: Pressure Unit
            lame_parameter (float): Lame parameter magnitude Unit: Pressure Unit

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        R = math.sqrt(youngs_modulus**2 + 9 * lame_parameter**2 + 2 * youngs_modulus * lame_parameter)

        bulk_modulus = (youngs_modulus + 3 * lame_parameter + R) / 6
        shear_modulus = (youngs_modulus - 3 * lame_parameter + R) / 4
        poissons_ratio = 2 * lame_parameter / (youngs_modulus + lame_parameter + R)
        p_wave_modulus = (youngs_modulus - lame_parameter + R) / 2

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_youngs_and_shear(youngs_modulus: float, shear_modulus: float) -> ElasticProperties:
        """Convert Young's and Shear modulus to other elastic property types.

        Input Unit: Pressure Unit of any type (GPa, psi, Mpsi etc). Pressure unit of both inputs needs to be consistent.

        Args:
            youngs_modulus (float): Young's modulus magnitude Unit: Pressure Unit
            shear_modulus (float): Shear modulus magnitude Unit: Pressure Unit

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        bulk_modulus = youngs_modulus * shear_modulus / (3 * (3 * shear_modulus - youngs_modulus))
        lame_parameter = (shear_modulus * (youngs_modulus - 2 * shear_modulus)) / (3 * shear_modulus - youngs_modulus)
        poissons_ratio = 0.5 * (youngs_modulus / shear_modulus) - 1
        p_wave_modulus = (shear_modulus * (4 * shear_modulus - youngs_modulus)) / (3 * shear_modulus - youngs_modulus)

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_youngs_and_poissons(youngs_modulus: float, poissons_ratio: float) -> ElasticProperties:
        """Convert Young's modulus and Poisson's ratio to other elastic property types.

        Input Unit: Young's modulus - pressure unit, Poisson's ratio - unitless.

        Args:
            youngs_modulus (float): Bulk modulus magnitude Unit: Pressure Unit
            poissons_ratio (float): Poisson's ratio magnitude Unit: unitless

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        bulk_modulus = youngs_modulus / (3 * (1 - 2 * poissons_ratio))
        lame_parameter = youngs_modulus * poissons_ratio / ((1 + poissons_ratio) * (1 - 2 * poissons_ratio))
        shear_modulus = youngs_modulus / (2 * (1 + poissons_ratio))
        p_wave_modulus = (youngs_modulus * (1 - poissons_ratio)) / ((1 + poissons_ratio) * (1 - 2 * poissons_ratio))

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_youngs_and_p_wave(youngs_modulus: float, p_wave_modulus: float) -> ElasticProperties:
        """Convert Young's modulus and P-wave modulus to other elastic property types.

        Input Unit: Pressure Unit of any type (GPa, psi, Mpsi etc). Pressure unit of both inputs needs to be consistent.

        Args:
            youngs_modulus (float): Young's modulus magnitude Unit: Pressure Unit
            p_wave_modulus (float): P-wave modulus magnitude Unit: Pressure Unit

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        S = math.sqrt(youngs_modulus**2 + 9 * p_wave_modulus**2 - 10 * youngs_modulus * p_wave_modulus)

        bulk_modulus = (3 * p_wave_modulus - youngs_modulus + S) / 6
        lame_parameter = (p_wave_modulus - youngs_modulus + S) / 4
        shear_modulus = (3 * p_wave_modulus + youngs_modulus - S) / 8
        poissons_ratio = (youngs_modulus - p_wave_modulus + S) / (4 * p_wave_modulus)

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_lame_and_shear(lame_parameter: float, shear_modulus: float) -> ElasticProperties:
        """Convert Lame parameter and Shear modulus to other elastic property types.

        Input Unit: Pressure Unit of any type (GPa, psi, Mpsi etc). Pressure unit of both inputs needs to be consistent.

        Args:
            lame_parameter (float): Lame parameter magnitude Unit: Pressure Unit
            shear_modulus (float): Shear modulus magnitude Unit: Pressure Unit

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        bulk_modulus = lame_parameter + (2 * shear_modulus / 3)
        youngs_modulus = shear_modulus * (3 * lame_parameter + 2 * shear_modulus) / (lame_parameter + shear_modulus)
        poissons_ratio = lame_parameter / (2 * (lame_parameter + shear_modulus))
        p_wave_modulus = lame_parameter + 2 * shear_modulus

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_lame_and_poissons(lame_parameter: float, poissons_ratio: float) -> ElasticProperties:
        """Convert Lame parameter and Poisson's ratio to other elastic property types.

        Input Unit: Lame parameter - pressure unit, Poisson's ratio - unitless.

        Args:
            lame_parameter (float): Lame parameter magnitude Unit: Pressure Unit
            poissons_ratio (float): Poisson's ratio magnitude Unit: unitless

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        bulk_modulus = lame_parameter * (1 + poissons_ratio) / (3 * poissons_ratio)
        youngs_modulus = (lame_parameter * (1 + poissons_ratio) * (1 - 2 * poissons_ratio)) / poissons_ratio
        shear_modulus = lame_parameter * (1 - 2 * poissons_ratio) / (2 * poissons_ratio)
        p_wave_modulus = (lame_parameter * (1 - poissons_ratio)) / poissons_ratio

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_lame_and_p_wave(lame_parameter: float, p_wave_modulus: float) -> ElasticProperties:
        """Convert Lame parameter and P-wave modulus to other elastic property types.

        Input Unit: Pressure Unit of any type (GPa, psi, Mpsi etc). Pressure unit of both inputs needs to be consistent.

        Args:
            lame_parameter (float): Lame parameter magnitude Unit: Pressure Unit
            p_wave_modulus (float): P-wave modulus magnitude Unit: Pressure Unit

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        bulk_modulus = (p_wave_modulus + 2 * lame_parameter) / 3
        youngs_modulus = ((p_wave_modulus - lame_parameter) * (p_wave_modulus + 2 * lame_parameter)) / (p_wave_modulus + lame_parameter)
        shear_modulus = (p_wave_modulus - lame_parameter) / 2
        poissons_ratio = lame_parameter / (p_wave_modulus + lame_parameter)

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_shear_and_poissons(shear_modulus: float, poissons_ratio: float) -> ElasticProperties:
        """Convert Shear modulus and Poisson's ratio to other elastic property types.

        Input Unit: Young's modulus - pressure unit, Poisson's ratio - unitless.

        Args:
            shear_modulus (float): Shear modulus magnitude Unit: Pressure Unit
            poissons_ratio (float): Poisson's ratio magnitude Unit: unitless

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        bulk_modulus = (2 * shear_modulus * (1 + poissons_ratio)) / (3 * (1 - 2 * poissons_ratio))
        youngs_modulus = 2 * shear_modulus * (1 + poissons_ratio)
        lame_parameter = 2 * shear_modulus * poissons_ratio / (1 - 2 * poissons_ratio)
        p_wave_modulus = (2 * shear_modulus * (1 - poissons_ratio)) / (1 - 2 * poissons_ratio)

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_shear_and_p_wave(shear_modulus: float, p_wave_modulus: float) -> ElasticProperties:
        """Convert Shear modulus and P-wave modulus to other elastic property types.

        Input Unit: Pressure Unit of any type (GPa, psi, Mpsi etc). Pressure unit of both inputs needs to be consistent.

        Args:
            shear_modulus (float): Shear modulus magnitude Unit: Pressure Unit
            p_wave_modulus (float): P-wave modulus magnitude Unit: Pressure Unit

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        bulk_modulus = p_wave_modulus - (4 / 3) * shear_modulus
        youngs_modulus = (shear_modulus * (3 * p_wave_modulus - 4 * shear_modulus)) / (p_wave_modulus - shear_modulus)
        lame_parameter = p_wave_modulus - 2 * shear_modulus
        poissons_ratio = (p_wave_modulus - 2 * shear_modulus) / (2 * p_wave_modulus - 2 * shear_modulus)

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_from_poissons_and_p_wave(poissons_ratio: float, p_wave_modulus: float) -> ElasticProperties:
        """Convert Poisson's ratio and P-wave modulus to other elastic property types.

        Input Unit: Poisson's ratio - unitless, P-wave modulus - pressure unit.

        Args:
            poissons_ratio (float): Poisson's ratio magnitude Unit: unitless
            p_wave_modulus (float): P-wave modulus magnitude Unit: Pressure Unit

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: consistent with input unit"""
        bulk_modulus = (p_wave_modulus * (1 + poissons_ratio)) / (3 * (1 - poissons_ratio))
        youngs_modulus = (p_wave_modulus * (1 + poissons_ratio) * (1 - 2 * poissons_ratio)) / (1 - poissons_ratio)
        lame_parameter = p_wave_modulus * poissons_ratio / (1 - poissons_ratio)
        shear_modulus = (p_wave_modulus * (1 - 2 * poissons_ratio)) / (2 * (1 - poissons_ratio))

        return ElasticProperties(bulk_modulus, youngs_modulus, lame_parameter, shear_modulus, poissons_ratio, p_wave_modulus)

    @staticmethod
    def convert_dynamic_elastic_properties_from_velocity(p_wave_velocity: float, s_wave_velocity: float, density: float, velocity_unit: str = "m/s", density_unit: str = "kg/m3", modulus_unit: str = "Pa") -> ElasticProperties:
        """Convert P and S Wave Velocity and Bulk Density to all elastic property types.

        Args:
            p_wave_velocity (float): Compressional Velocity Unit: [velocity_unit]
            s_wave_velocity (float): Shear Velocity Unit: [velocity_unit]
            density (float): Bulk Density Unit: [density_unit]
            velocity_unit (str): Unit of the velocity inputs (e.g. "m/s", "ft/s"). Defaults to "m/s"
            density_unit (str): Unit of the density input (e.g. "kg/m3", "g/cm3"). Defaults to "kg/m3"
            modulus_unit (str): Unit of the elastic moduli output (e.g. "Pa", "GPa", "Mpsi"). Defaults to "Pa"

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: [modulus_unit]"""
        p_wave_velocity = UnitConverter.convert_velocity(p_wave_velocity, velocity_unit, "m/s")
        s_wave_velocity = UnitConverter.convert_velocity(s_wave_velocity, velocity_unit, "m/s")
        density = UnitConverter.convert_density(density, density_unit, "kg/m3")

        shear_modulus = density * s_wave_velocity**2
        p_wave_modulus = density * p_wave_velocity**2

        elastic_properties = ElasticPropertiesConverter.convert_from_shear_and_p_wave(shear_modulus, p_wave_modulus)

        return ElasticProperties(
            bulk_modulus=UnitConverter.convert_pressure(elastic_properties.bulk_modulus, "Pa", modulus_unit),
            youngs_modulus=UnitConverter.convert_pressure(elastic_properties.youngs_modulus, "Pa", modulus_unit),
            lame_parameter=UnitConverter.convert_pressure(elastic_properties.lame_parameter, "Pa", modulus_unit),
            shear_modulus=UnitConverter.convert_pressure(elastic_properties.shear_modulus, "Pa", modulus_unit),
            poissons_ratio=elastic_properties.poissons_ratio,
            p_wave_modulus=UnitConverter.convert_pressure(elastic_properties.p_wave_modulus, "Pa", modulus_unit),
        )

    @staticmethod
    def convert_dynamic_elastic_properties_from_slowness(p_wave_slowness: float, s_wave_slowness: float, density: float, slowness_unit: str = "us/ft", density_unit: str = "kg/m3", modulus_unit: str = "Pa") -> ElasticProperties:
        """Convert P and S Wave Slowness and Bulk Density to all elastic property types.

        Args:
            p_wave_slowness (float): Compressional Slowness Unit: [slowness_unit]
            s_wave_slowness (float): Shear Slowness Unit: [slowness_unit]
            density (float): Bulk Density Unit: [density_unit]
            slowness_unit (str): Unit of the slowness inputs (e.g. "us/ft", "us/m"). Defaults to "us/ft"
            density_unit (str): Unit of the density input (e.g. "kg/m3", "g/cm3"). Defaults to "kg/m3"
            modulus_unit (str): Unit of the elastic moduli output (e.g. "Pa", "GPa", "Mpsi"). Defaults to "Pa"

        Returns:
            ElasticProperties: Dataclass containing computed elastic properties. See `ElasticProperties` for details. Unit: [modulus_unit]"""
        p_wave_slowness = UnitConverter.convert_slowness(p_wave_slowness, slowness_unit, "us/ft")
        s_wave_slowness = UnitConverter.convert_slowness(s_wave_slowness, slowness_unit, "us/ft")

        return ElasticPropertiesConverter.convert_dynamic_elastic_properties_from_velocity(
            p_wave_velocity=304800 / p_wave_slowness,
            s_wave_velocity=304800 / s_wave_slowness,
            density=density,
            density_unit=density_unit,
            modulus_unit=modulus_unit,
        )

    @staticmethod
    def convert_from_bulk_and_youngs_array(bulk_modulus: list[float], youngs_modulus: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Bulk and Young's moduli to ElasticProperties entries.

        Args:
            bulk_modulus (list[float]): Bulk modulus values. Unit: Pressure Unit
            youngs_modulus (list[float]): Young's modulus values. Unit: Pressure Unit

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_bulk_and_youngs(bm, ym)
            for bm, ym in zip(bulk_modulus, youngs_modulus, strict=True)
        ]

    @staticmethod
    def convert_from_bulk_and_lame_array(bulk_modulus: list[float], lame_parameter: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Bulk modulus and Lame parameter to ElasticProperties entries.

        Args:
            bulk_modulus (list[float]): Bulk modulus values. Unit: Pressure Unit
            lame_parameter (list[float]): Lame parameter values. Unit: Pressure Unit

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_bulk_and_lame(bm, lp)
            for bm, lp in zip(bulk_modulus, lame_parameter, strict=True)
        ]

    @staticmethod
    def convert_from_bulk_and_shear_array(bulk_modulus: list[float], shear_modulus: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Bulk and Shear moduli to ElasticProperties entries.

        Args:
            bulk_modulus (list[float]): Bulk modulus values. Unit: Pressure Unit
            shear_modulus (list[float]): Shear modulus values. Unit: Pressure Unit

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_bulk_and_shear(bm, sm)
            for bm, sm in zip(bulk_modulus, shear_modulus, strict=True)
        ]

    @staticmethod
    def convert_from_bulk_and_poissons_array(bulk_modulus: list[float], poissons_ratio: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Bulk modulus and Poisson's ratio to ElasticProperties entries.

        Args:
            bulk_modulus (list[float]): Bulk modulus values. Unit: Pressure Unit
            poissons_ratio (list[float]): Poisson's ratio values. Unit: unitless

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_bulk_and_poissons(bm, pr)
            for bm, pr in zip(bulk_modulus, poissons_ratio, strict=True)
        ]

    @staticmethod
    def convert_from_bulk_and_p_wave_array(bulk_modulus: list[float], p_wave_modulus: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Bulk and P-wave moduli to ElasticProperties entries.

        Args:
            bulk_modulus (list[float]): Bulk modulus values. Unit: Pressure Unit
            p_wave_modulus (list[float]): P-wave modulus values. Unit: Pressure Unit

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_bulk_and_p_wave(bm, pw)
            for bm, pw in zip(bulk_modulus, p_wave_modulus, strict=True)
        ]

    @staticmethod
    def convert_from_youngs_and_lame_array(youngs_modulus: list[float], lame_parameter: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Young's modulus and Lame parameter to ElasticProperties entries.

        Args:
            youngs_modulus (list[float]): Young's modulus values. Unit: Pressure Unit
            lame_parameter (list[float]): Lame parameter values. Unit: Pressure Unit

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_youngs_and_lame(ym, lp)
            for ym, lp in zip(youngs_modulus, lame_parameter, strict=True)
        ]

    @staticmethod
    def convert_from_youngs_and_shear_array(youngs_modulus: list[float], shear_modulus: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Young's and Shear moduli to ElasticProperties entries.

        Args:
            youngs_modulus (list[float]): Young's modulus values. Unit: Pressure Unit
            shear_modulus (list[float]): Shear modulus values. Unit: Pressure Unit

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_youngs_and_shear(ym, sm)
            for ym, sm in zip(youngs_modulus, shear_modulus, strict=True)
        ]

    @staticmethod
    def convert_from_youngs_and_poissons_array(youngs_modulus: list[float], poissons_ratio: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Young's modulus and Poisson's ratio to ElasticProperties entries.

        Args:
            youngs_modulus (list[float]): Young's modulus values. Unit: Pressure Unit
            poissons_ratio (list[float]): Poisson's ratio values. Unit: unitless

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_youngs_and_poissons(ym, pr)
            for ym, pr in zip(youngs_modulus, poissons_ratio, strict=True)
        ]

    @staticmethod
    def convert_from_youngs_and_p_wave_array(youngs_modulus: list[float], p_wave_modulus: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Young's modulus and P-wave modulus to ElasticProperties entries.

        Args:
            youngs_modulus (list[float]): Young's modulus values. Unit: Pressure Unit
            p_wave_modulus (list[float]): P-wave modulus values. Unit: Pressure Unit

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_youngs_and_p_wave(ym, pw)
            for ym, pw in zip(youngs_modulus, p_wave_modulus, strict=True)
        ]

    @staticmethod
    def convert_from_lame_and_shear_array(lame_parameter: list[float], shear_modulus: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Lame parameter and Shear modulus to ElasticProperties entries.

        Args:
            lame_parameter (list[float]): Lame parameter values. Unit: Pressure Unit
            shear_modulus (list[float]): Shear modulus values. Unit: Pressure Unit

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_lame_and_shear(lp, sm)
            for lp, sm in zip(lame_parameter, shear_modulus, strict=True)
        ]

    @staticmethod
    def convert_from_lame_and_poissons_array(lame_parameter: list[float], poissons_ratio: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Lame parameter and Poisson's ratio to ElasticProperties entries.

        Args:
            lame_parameter (list[float]): Lame parameter values. Unit: Pressure Unit
            poissons_ratio (list[float]): Poisson's ratio values. Unit: unitless

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_lame_and_poissons(lp, pr)
            for lp, pr in zip(lame_parameter, poissons_ratio, strict=True)
        ]

    @staticmethod
    def convert_from_lame_and_p_wave_array(lame_parameter: list[float], p_wave_modulus: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Lame parameter and P-wave modulus to ElasticProperties entries.

        Args:
            lame_parameter (list[float]): Lame parameter values. Unit: Pressure Unit
            p_wave_modulus (list[float]): P-wave modulus values. Unit: Pressure Unit

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_lame_and_p_wave(lp, pw)
            for lp, pw in zip(lame_parameter, p_wave_modulus, strict=True)
        ]

    @staticmethod
    def convert_from_shear_and_poissons_array(shear_modulus: list[float], poissons_ratio: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Shear modulus and Poisson's ratio to ElasticProperties entries.

        Args:
            shear_modulus (list[float]): Shear modulus values. Unit: Pressure Unit
            poissons_ratio (list[float]): Poisson's ratio values. Unit: unitless

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_shear_and_poissons(sm, pr)
            for sm, pr in zip(shear_modulus, poissons_ratio, strict=True)
        ]

    @staticmethod
    def convert_from_shear_and_p_wave_array(shear_modulus: list[float], p_wave_modulus: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Shear modulus and P-wave modulus to ElasticProperties entries.

        Args:
            shear_modulus (list[float]): Shear modulus values. Unit: Pressure Unit
            p_wave_modulus (list[float]): P-wave modulus values. Unit: Pressure Unit

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_shear_and_p_wave(sm, pw)
            for sm, pw in zip(shear_modulus, p_wave_modulus, strict=True)
        ]

    @staticmethod
    def convert_from_poissons_and_p_wave_array(poissons_ratio: list[float], p_wave_modulus: list[float]) -> list[ElasticProperties]:
        """Convert arrays of Poisson's ratio and P-wave modulus to ElasticProperties entries.

        Args:
            poissons_ratio (list[float]): Poisson's ratio values. Unit: unitless
            p_wave_modulus (list[float]): P-wave modulus values. Unit: Pressure Unit

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input pair."""
        return [
            ElasticPropertiesConverter.convert_from_poissons_and_p_wave(pr, pw)
            for pr, pw in zip(poissons_ratio, p_wave_modulus, strict=True)
        ]

    @staticmethod
    def convert_dynamic_elastic_properties_from_velocity_array(p_wave_velocity: list[float], s_wave_velocity: list[float], density: list[float], velocity_unit: str = "m/s", density_unit: str = "kg/m3", modulus_unit: str = "Pa") -> list[ElasticProperties]:
        """Convert arrays of P/S wave velocity and bulk density to ElasticProperties entries.

        Args:
            p_wave_velocity (list[float]): Compressional velocity values. Unit: [velocity_unit]
            s_wave_velocity (list[float]): Shear velocity values. Unit: [velocity_unit]
            density (list[float]): Bulk density values. Unit: [density_unit]
            velocity_unit (str): Unit of the velocity inputs. Defaults to "m/s"
            density_unit (str): Unit of the density inputs. Defaults to "kg/m3"
            modulus_unit (str): Unit of the elastic moduli outputs. Defaults to "Pa"

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input set."""
        return [
            ElasticPropertiesConverter.convert_dynamic_elastic_properties_from_velocity(vp, vs, rho, velocity_unit=velocity_unit, density_unit=density_unit, modulus_unit=modulus_unit)
            for vp, vs, rho in zip(p_wave_velocity, s_wave_velocity, density, strict=True)
        ]

    @staticmethod
    def convert_dynamic_elastic_properties_from_slowness_array(p_wave_slowness: list[float], s_wave_slowness: list[float], density: list[float], slowness_unit: str = "us/ft", density_unit: str = "kg/m3", modulus_unit: str = "Pa") -> list[ElasticProperties]:
        """Convert arrays of P/S wave slowness and bulk density to ElasticProperties entries.

        Args:
            p_wave_slowness (list[float]): Compressional slowness values. Unit: [slowness_unit]
            s_wave_slowness (list[float]): Shear slowness values. Unit: [slowness_unit]
            density (list[float]): Bulk density values. Unit: [density_unit]
            slowness_unit (str): Unit of the slowness inputs. Defaults to "us/ft"
            density_unit (str): Unit of the density inputs. Defaults to "kg/m3"
            modulus_unit (str): Unit of the elastic moduli outputs. Defaults to "Pa"

        Returns:
            list[ElasticProperties]: Computed elastic properties for each input set."""
        return [
            ElasticPropertiesConverter.convert_dynamic_elastic_properties_from_slowness(dtp, dts, rho, slowness_unit=slowness_unit, density_unit=density_unit, modulus_unit=modulus_unit)
            for dtp, dts, rho in zip(p_wave_slowness, s_wave_slowness, density, strict=True)
        ]
