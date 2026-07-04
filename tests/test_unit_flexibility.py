import pytest
from geomechpy.dynamic_elastic_properties import DynamicElasticPropertiesCalculation
from geomechpy.overburden_stress import OverburdenStressCalculation
from geomechpy.pore_pressure import PorePressureCalculation
from geomechpy.rock_strength import RockStrengthPropertiesConverter
from geomechpy.static_elastic_properties import StaticElasticPropertiesConverter
from geomechpy.stress_calculations import HorizontalStressesCalculation
from geomechpy.units import UnitConverter

TOLERANCE = 1e-6


class TestPorePressureUnits:
    def test_si_inputs_match_field_inputs(self) -> None:
        tvd_ft = 10000.0
        gradient_psi_ft = 0.47

        field_result = PorePressureCalculation.calculate_pore_pressure_onshore(
            tvd=tvd_ft, formation_pore_pressure_gradient=gradient_psi_ft
        )
        si_result = PorePressureCalculation.calculate_pore_pressure_onshore(
            tvd=UnitConverter.convert_depth(tvd_ft, "ft", "m"),
            formation_pore_pressure_gradient=UnitConverter.convert_pressure_gradient(gradient_psi_ft, "psi/ft", "kPa/m"),
            depth_unit="m",
            pressure_unit="kPa",
        )

        assert UnitConverter.convert_pressure(si_result, "kPa", "psi") == pytest.approx(field_result, rel=TOLERANCE)

    def test_default_gradient_is_units_aware(self) -> None:
        field_result = PorePressureCalculation.calculate_pore_pressure_onshore(tvd=10000.0)
        si_result = PorePressureCalculation.calculate_pore_pressure_onshore(
            tvd=UnitConverter.convert_depth(10000.0, "ft", "m"), depth_unit="m", pressure_unit="kPa"
        )

        assert UnitConverter.convert_pressure(si_result, "kPa", "psi") == pytest.approx(field_result, rel=TOLERANCE)

    def test_offshore_si_inputs_match_field_inputs(self) -> None:
        field_result = PorePressureCalculation.calculate_pore_pressure_offshore(
            tvd=8000.0, air_gap=80.0, water_depth=1000.0
        )
        si_result = PorePressureCalculation.calculate_pore_pressure_offshore(
            tvd=UnitConverter.convert_depth(8000.0, "ft", "m"),
            air_gap=UnitConverter.convert_depth(80.0, "ft", "m"),
            water_depth=UnitConverter.convert_depth(1000.0, "ft", "m"),
            depth_unit="m",
            pressure_unit="MPa",
        )

        assert UnitConverter.convert_pressure(si_result, "MPa", "psi") == pytest.approx(field_result, rel=TOLERANCE)


class TestOverburdenStressUnits:
    def test_si_inputs_match_field_inputs(self) -> None:
        field_result = OverburdenStressCalculation.calculate_overburden_stress_onshore(tvd=10000.0)
        si_result = OverburdenStressCalculation.calculate_overburden_stress_onshore(
            tvd=UnitConverter.convert_depth(10000.0, "ft", "m"), depth_unit="m", pressure_unit="MPa"
        )

        assert UnitConverter.convert_pressure(si_result, "MPa", "psi") == pytest.approx(field_result, rel=TOLERANCE)

    def test_gradient_in_bar_per_m(self) -> None:
        field_result = OverburdenStressCalculation.calculate_overburden_stress_onshore(
            tvd=10000.0, lithostatic_gradient=1.0
        )
        si_result = OverburdenStressCalculation.calculate_overburden_stress_onshore(
            tvd=UnitConverter.convert_depth(10000.0, "ft", "m"),
            lithostatic_gradient=UnitConverter.convert_pressure_gradient(1.0, "psi/ft", "bar/m"),
            depth_unit="m",
            pressure_unit="bar",
        )

        assert UnitConverter.convert_pressure(si_result, "bar", "psi") == pytest.approx(field_result, rel=TOLERANCE)


class TestDynamicElasticPropertiesUnits:
    def test_modulus_output_in_gpa(self) -> None:
        base = DynamicElasticPropertiesCalculation.calculate_from_velocity(4000.0, 2400.0, 2650.0)
        gpa = DynamicElasticPropertiesCalculation.calculate_from_velocity(4000.0, 2400.0, 2650.0, modulus_unit="GPa")

        assert gpa.youngs_modulus == pytest.approx(base.youngs_modulus / 1e9, rel=TOLERANCE)
        assert gpa.poissons_ratio == pytest.approx(base.poissons_ratio, rel=TOLERANCE)

    def test_velocity_in_ft_s_and_density_in_g_cm3(self) -> None:
        base = DynamicElasticPropertiesCalculation.calculate_from_velocity(4000.0, 2400.0, 2650.0)
        converted = DynamicElasticPropertiesCalculation.calculate_from_velocity(
            UnitConverter.convert_velocity(4000.0, "m/s", "ft/s"),
            UnitConverter.convert_velocity(2400.0, "m/s", "ft/s"),
            2.65,
            velocity_unit="ft/s",
            density_unit="g/cm3",
        )

        assert converted.youngs_modulus == pytest.approx(base.youngs_modulus, rel=TOLERANCE)
        assert converted.vp_vs_ratio == pytest.approx(base.vp_vs_ratio, rel=TOLERANCE)

    def test_slowness_in_us_m(self) -> None:
        base = DynamicElasticPropertiesCalculation.calculate_from_slowness(76.2, 127.0, 2650.0)
        converted = DynamicElasticPropertiesCalculation.calculate_from_slowness(
            UnitConverter.convert_slowness(76.2, "us/ft", "us/m"),
            UnitConverter.convert_slowness(127.0, "us/ft", "us/m"),
            2650.0,
            slowness_unit="us/m",
        )

        assert converted.bulk_modulus == pytest.approx(base.bulk_modulus, rel=TOLERANCE)


class TestPoroelasticStressUnits:
    def test_si_inputs_match_field_inputs(self) -> None:
        field_result = HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses(
            overburden_stress=3000.0, pore_pressure=1400.0, poisson_ratio=0.25, youngs_modulus=2.0
        )
        si_result = HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses(
            overburden_stress=UnitConverter.convert_pressure(3000.0, "psi", "MPa"),
            pore_pressure=UnitConverter.convert_pressure(1400.0, "psi", "MPa"),
            poisson_ratio=0.25,
            youngs_modulus=UnitConverter.convert_pressure(2.0, "Mpsi", "GPa"),
            pressure_unit="MPa",
            modulus_unit="GPa",
        )

        assert UnitConverter.convert_pressure(si_result.shmin, "MPa", "psi") == pytest.approx(field_result.shmin, rel=TOLERANCE)
        assert UnitConverter.convert_pressure(si_result.shmax, "MPa", "psi") == pytest.approx(field_result.shmax, rel=TOLERANCE)
        assert si_result.q_factor == pytest.approx(field_result.q_factor, rel=TOLERANCE)


class TestRockStrengthUnits:
    def test_plumb_with_gpa_input_and_mpa_output(self) -> None:
        field_result = RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb(yme_sta=5.0)
        si_result = RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb(
            yme_sta=UnitConverter.convert_pressure(5.0, "Mpsi", "GPa"),
            modulus_unit="GPa",
            pressure_unit="MPa",
        )

        assert UnitConverter.convert_pressure(si_result, "MPa", "psi") == pytest.approx(field_result, rel=TOLERANCE)

    def test_lal_with_us_m_input(self) -> None:
        field_result = RockStrengthPropertiesConverter.convert_friction_angle_lal(dtco=100.0)
        si_result = RockStrengthPropertiesConverter.convert_friction_angle_lal(
            dtco=UnitConverter.convert_slowness(100.0, "us/ft", "us/m"),
            slowness_unit="us/m",
        )

        assert si_result == pytest.approx(field_result, rel=TOLERANCE)


class TestStaticElasticPropertiesUnits:
    def test_bradford_with_gpa_input(self) -> None:
        field_result = StaticElasticPropertiesConverter.dyn2sta_yme_bradord(yme_dyn=2.0)
        si_result = StaticElasticPropertiesConverter.dyn2sta_yme_bradord(
            yme_dyn=UnitConverter.convert_pressure(2.0, "Mpsi", "GPa"),
            modulus_unit="GPa",
        )

        assert UnitConverter.convert_pressure(si_result, "GPa", "Mpsi") == pytest.approx(field_result, rel=TOLERANCE)

    def test_fuller_with_mpsi_input(self) -> None:
        field_result = StaticElasticPropertiesConverter.dyn2sta_yme_fuller(yme_dyn=10.0)
        si_result = StaticElasticPropertiesConverter.dyn2sta_yme_fuller(
            yme_dyn=UnitConverter.convert_pressure(10.0, "GPa", "Mpsi"),
            modulus_unit="Mpsi",
        )

        assert UnitConverter.convert_pressure(si_result, "Mpsi", "GPa") == pytest.approx(field_result, rel=TOLERANCE)
