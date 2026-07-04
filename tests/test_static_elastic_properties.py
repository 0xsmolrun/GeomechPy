import pytest
from geomechpy.static_elastic_properties import StaticElasticPropertiesConverter

TOLERANCE = 1e-6


class TestBradfordCorrelation:
    def test_bradford_value(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_yme_bradord(yme_dyn=2.0)
        expected = 0.04794626440600849 * 2.0**2.7
        assert result == pytest.approx(expected, rel=TOLERANCE)

    def test_bradford_zero_input(self) -> None:
        assert StaticElasticPropertiesConverter.dyn2sta_yme_bradord(yme_dyn=0.0) == 0.0

    def test_bradford_monotonic(self) -> None:
        low_dyn_yme_static = StaticElasticPropertiesConverter.dyn2sta_yme_bradord(yme_dyn=1.0)
        high_dyn_yme_static = StaticElasticPropertiesConverter.dyn2sta_yme_bradord(yme_dyn=3.0)
        assert high_dyn_yme_static > low_dyn_yme_static


class TestNajibCorrelation:
    def test_najib_value(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_yme_najib(yme_dyn=2.0)
        expected = 0.07277314417314575 * 2.0**1.96
        assert result == pytest.approx(expected, rel=TOLERANCE)

    def test_najib_zero_input(self) -> None:
        assert StaticElasticPropertiesConverter.dyn2sta_yme_najib(yme_dyn=0.0) == 0.0


class TestFullerCorrelation:
    def test_fuller_value(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_yme_fuller(yme_dyn=10.0)
        expected = 0.08143824177457351 * 10.0**1.632
        assert result == pytest.approx(expected, rel=TOLERANCE)


class TestMoralesCorrelation:
    def test_consolidated_porosity_band(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_yme_morales(yme_dyn=5.0, porosity=0.12)
        expected = 2.562214651764409 * 5.0**0.6612
        assert result == pytest.approx(expected, rel=TOLERANCE)

    def test_moderately_consolidated_porosity_band(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_yme_morales(yme_dyn=5.0, porosity=0.20)
        expected = 0.5281242638335621 * 5.0**0.6920
        assert result == pytest.approx(expected, rel=TOLERANCE)

    def test_weakly_consolidated_porosity_band(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_yme_morales(yme_dyn=5.0, porosity=0.30)
        expected = 0.3467028522374105 * 5.0**0.9404
        assert result == pytest.approx(expected, rel=TOLERANCE)

    def test_low_porosity_excluded_by_default(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_yme_morales(yme_dyn=5.0, porosity=0.05)
        assert result == -9999

    def test_low_porosity_not_excluded_when_disabled(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_yme_morales(
            yme_dyn=5.0, porosity=0.05, exclude_low_por=False
        )
        expected = 2.562214651764409 * 5.0**0.6612
        assert result == pytest.approx(expected, rel=TOLERANCE)


class TestCustomCorrelations:
    def test_custom_power_law(self) -> None:
        result = StaticElasticPropertiesConverter.convert_dyn2sta_yme_custom_power_law(
            yme_dyn=10.0, multiplier=2.0, exponent=0.5
        )
        assert result == pytest.approx(2.0 * 10.0**0.5, rel=TOLERANCE)

    def test_custom_linear_law(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_yme_custom_linear_law(
            yme_dyn=10.0, slope=0.5, intercept=1.0
        )
        assert result == pytest.approx(6.0, rel=TOLERANCE)

    def test_custom_linear_law_with_zero_slope(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_yme_custom_linear_law(
            yme_dyn=10.0, slope=0.0, intercept=2.0
        )
        assert result == pytest.approx(2.0, rel=TOLERANCE)


class TestPoissonsRatioConversion:
    def test_poissons_ratio_scaling(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_poissons_ratio(pr_dyn=0.30, multiplier=0.8)
        assert result == pytest.approx(0.24, rel=TOLERANCE)

    def test_poissons_ratio_unit_multiplier(self) -> None:
        result = StaticElasticPropertiesConverter.dyn2sta_poissons_ratio(pr_dyn=0.25, multiplier=1.0)
        assert result == pytest.approx(0.25, rel=TOLERANCE)


class TestBiotCoefficient:
    def test_returns_constant(self) -> None:
        assert StaticElasticPropertiesConverter.biot_coefficient_constant_law(constant=0.7) == 0.7

    def test_returns_zero(self) -> None:
        assert StaticElasticPropertiesConverter.biot_coefficient_constant_law(constant=0.0) == 0.0
