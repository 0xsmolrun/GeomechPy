import pytest
from geomechpy.units import UnitConverter

TOLERANCE = 1e-6


class TestPressureConversion:
    def test_psi_to_kpa(self) -> None:
        assert UnitConverter.convert_pressure(1.0, "psi", "kPa") == pytest.approx(6.894757293, rel=TOLERANCE)

    def test_psia_is_alias_of_psi(self) -> None:
        assert UnitConverter.convert_pressure(100.0, "psia", "psi") == pytest.approx(100.0, rel=TOLERANCE)

    def test_mpa_to_psi(self) -> None:
        assert UnitConverter.convert_pressure(1.0, "MPa", "psi") == pytest.approx(145.0377377, rel=TOLERANCE)

    def test_mpsi_to_gpa(self) -> None:
        assert UnitConverter.convert_pressure(1.0, "Mpsi", "GPa") == pytest.approx(6.894757293, rel=TOLERANCE)

    def test_bar_to_pa(self) -> None:
        assert UnitConverter.convert_pressure(1.0, "bar", "Pa") == pytest.approx(1.0e5, rel=TOLERANCE)

    def test_round_trip(self) -> None:
        assert UnitConverter.convert_pressure(UnitConverter.convert_pressure(1234.5, "psi", "kPa"), "kPa", "psi") == pytest.approx(1234.5, rel=TOLERANCE)

    def test_case_insensitive(self) -> None:
        assert UnitConverter.convert_pressure(1.0, "PSI", "KPA") == pytest.approx(6.894757293, rel=TOLERANCE)

    def test_unknown_unit_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported pressure unit"):
            UnitConverter.convert_pressure(1.0, "furlongs", "psi")


class TestDepthConversion:
    def test_ft_to_m(self) -> None:
        assert UnitConverter.convert_depth(1000.0, "ft", "m") == pytest.approx(304.8, rel=TOLERANCE)

    def test_km_to_ft(self) -> None:
        assert UnitConverter.convert_depth(1.0, "km", "ft") == pytest.approx(3280.839895, rel=TOLERANCE)


class TestDensityConversion:
    def test_g_cm3_to_kg_m3(self) -> None:
        assert UnitConverter.convert_density(2.65, "g/cm3", "kg/m3") == pytest.approx(2650.0, rel=TOLERANCE)

    def test_ppg_to_kg_m3(self) -> None:
        assert UnitConverter.convert_density(8.33, "ppg", "kg/m3") == pytest.approx(998.15, rel=1e-3)

    def test_sg_to_g_cm3(self) -> None:
        assert UnitConverter.convert_density(1.1, "SG", "g/cm3") == pytest.approx(1.1, rel=TOLERANCE)


class TestVelocityAndSlownessConversion:
    def test_ft_s_to_m_s(self) -> None:
        assert UnitConverter.convert_velocity(10000.0, "ft/s", "m/s") == pytest.approx(3048.0, rel=TOLERANCE)

    def test_us_ft_to_us_m(self) -> None:
        assert UnitConverter.convert_slowness(100.0, "us/ft", "us/m") == pytest.approx(328.0839895, rel=TOLERANCE)


class TestPressureGradientConversion:
    def test_psi_ft_to_kpa_m(self) -> None:
        assert UnitConverter.convert_pressure_gradient(1.0, "psi/ft", "kPa/m") == pytest.approx(22.62059413, rel=TOLERANCE)

    def test_ppg_to_psi_ft(self) -> None:
        # The classic 0.052 conversion factor of mud engineering
        assert UnitConverter.convert_pressure_gradient(1.0, "ppg", "psi/ft") == pytest.approx(0.0519, rel=1e-2)

    def test_sg_to_psi_ft(self) -> None:
        # Fresh water gradient is approximately 0.433 psi/ft
        assert UnitConverter.convert_pressure_gradient(1.0, "SG", "psi/ft") == pytest.approx(0.4335, rel=1e-3)

    def test_any_pressure_depth_combination(self) -> None:
        assert UnitConverter.convert_pressure_gradient(1.0, "MPa/km", "kPa/m") == pytest.approx(1.0, rel=TOLERANCE)

    def test_unknown_gradient_unit_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported pressure gradient unit"):
            UnitConverter.convert_pressure_gradient(1.0, "psi/gallon", "psi/ft")


class TestDensityToGradient:
    def test_fresh_water(self) -> None:
        assert UnitConverter.convert_density_to_pressure_gradient(1000.0, "kg/m3", "psi/ft") == pytest.approx(0.4335, rel=1e-3)

    def test_kpa_m_output(self) -> None:
        assert UnitConverter.convert_density_to_pressure_gradient(1000.0, "kg/m3", "kPa/m") == pytest.approx(9.80665, rel=TOLERANCE)


class TestMudWeightConversion:
    def test_mud_weight_to_pressure(self) -> None:
        # 10 ppg at 10000 ft is about 0.052 * 10 * 10000 = 5200 psi
        result = UnitConverter.convert_mud_weight_to_pressure(10.0, 10000.0, mud_weight_unit="ppg", pressure_unit="psi", depth_unit="ft")
        assert result == pytest.approx(5194.8, rel=1e-3)

    def test_pressure_to_mud_weight_round_trip(self) -> None:
        pressure = UnitConverter.convert_mud_weight_to_pressure(12.5, 8000.0)
        assert UnitConverter.convert_pressure_to_mud_weight(pressure, 8000.0) == pytest.approx(12.5, rel=TOLERANCE)

    def test_metric_mud_weight(self) -> None:
        # 1.2 SG at 3000 m: 1200 kg/m3 * 9.80665 m/s2 * 3000 m = 35.30 MPa
        result = UnitConverter.convert_mud_weight_to_pressure(1.2, 3000.0, mud_weight_unit="SG", pressure_unit="MPa", depth_unit="m")
        assert result == pytest.approx(35.30394, rel=1e-4)


class TestArrayVersions:
    def test_pressure_array(self) -> None:
        result = UnitConverter.convert_pressure_array([1.0, 2.0], "MPa", "kPa")
        assert result == pytest.approx([1000.0, 2000.0], rel=TOLERANCE)

    def test_mud_weight_array_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError):
            UnitConverter.convert_pressure_to_mud_weight_array([5000.0, 6000.0], [10000.0])
