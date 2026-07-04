import math

import pytest
from geomechpy.rock_strength import RockStrengthPropertiesConverter

TOLERANCE = 1e-6


class TestPlumbUcs:
    def test_plumb_correlation_value(self) -> None:
        # Source form UCS [MPa] = 1.45 * E [GPa]  ->  UCS [psi] = 1450 * E [Mpsi]
        result = RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb(yme_sta=5.0)
        assert result == pytest.approx(1450.0 * 5.0, rel=TOLERANCE)

    def test_plumb_matches_source_form_in_si_units(self) -> None:
        # E = 13.789514 GPa (2 Mpsi) -> UCS = 1.45 * 13.789514 = 19.995 MPa
        result = RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb(
            yme_sta=13.789514586336723, modulus_unit="GPa", pressure_unit="MPa"
        )
        assert result == pytest.approx(1.45 * 13.789514586336723, rel=TOLERANCE)

    def test_plumb_zero_input(self) -> None:
        assert RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb(yme_sta=0.0) == 0.0

    def test_plumb_returns_float(self) -> None:
        result = RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb(yme_sta=2.0)
        assert isinstance(result, float)


class TestUcsToTstr:
    def test_default_multiplier(self) -> None:
        result = RockStrengthPropertiesConverter.convert_ucs_to_tstr(ucs=1000.0)
        assert result == pytest.approx(150.0, rel=TOLERANCE)

    def test_custom_multiplier(self) -> None:
        result = RockStrengthPropertiesConverter.convert_ucs_to_tstr(ucs=1000.0, multiplier=0.2)
        assert result == pytest.approx(200.0, rel=TOLERANCE)

    def test_zero_ucs(self) -> None:
        assert RockStrengthPropertiesConverter.convert_ucs_to_tstr(ucs=0.0) == 0.0


class TestFrictionAngleLal:
    def test_typical_sandstone_slowness(self) -> None:
        result = RockStrengthPropertiesConverter.convert_friction_angle_lal(dtco=80.0)
        expected = math.degrees(math.asin((304800 - 80000) / (304800 + 80000)))
        assert result == pytest.approx(expected, rel=TOLERANCE)

    def test_zero_slowness_returns_ninety_degrees(self) -> None:
        result = RockStrengthPropertiesConverter.convert_friction_angle_lal(dtco=0.0)
        assert result == pytest.approx(90.0, rel=1e-4)

    def test_friction_angle_decreases_with_increasing_slowness(self) -> None:
        friction_angle_at_low_slowness = RockStrengthPropertiesConverter.convert_friction_angle_lal(dtco=50.0)
        friction_angle_at_high_slowness = RockStrengthPropertiesConverter.convert_friction_angle_lal(dtco=150.0)
        assert friction_angle_at_low_slowness > friction_angle_at_high_slowness
