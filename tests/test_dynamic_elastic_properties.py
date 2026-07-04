import pytest
from geomechpy.dynamic_elastic_properties import DynamicElasticProperties, DynamicElasticPropertiesCalculation

CONVERTER_TOLERANCE = 1e-2


def test_convert_slowness_to_velocity() -> None:
    # 100 us/ft corresponds to 3048 m/s
    assert DynamicElasticPropertiesCalculation.convert_slowness_to_velocity(100.0) == pytest.approx(3048.0, rel=CONVERTER_TOLERANCE)


def test_convert_velocity_to_slowness() -> None:
    assert DynamicElasticPropertiesCalculation.convert_velocity_to_slowness(3048.0) == pytest.approx(100.0, rel=CONVERTER_TOLERANCE)


def test_slowness_velocity_round_trip() -> None:
    slowness = 76.5
    velocity = DynamicElasticPropertiesCalculation.convert_slowness_to_velocity(slowness)
    assert DynamicElasticPropertiesCalculation.convert_velocity_to_slowness(velocity) == pytest.approx(slowness, rel=1e-9)


def test_calculate_from_velocity() -> None:
    # Typical sandstone: Vp = 4000 m/s, Vs = 2400 m/s, rho = 2650 kg/m3
    calculated_model = DynamicElasticPropertiesCalculation.calculate_from_velocity(4000.0, 2400.0, 2650.0)

    assert calculated_model.shear_modulus == pytest.approx(2650.0 * 2400.0**2, rel=CONVERTER_TOLERANCE)
    assert calculated_model.p_wave_modulus == pytest.approx(2650.0 * 4000.0**2, rel=CONVERTER_TOLERANCE)
    assert calculated_model.bulk_modulus == pytest.approx(2.2048e10, rel=CONVERTER_TOLERANCE)
    assert calculated_model.youngs_modulus == pytest.approx(3.7095e10, rel=CONVERTER_TOLERANCE)
    assert calculated_model.lame_parameter == pytest.approx(1.1872e10, rel=CONVERTER_TOLERANCE)
    assert calculated_model.poissons_ratio == pytest.approx(0.2188, rel=CONVERTER_TOLERANCE)
    assert calculated_model.vp_vs_ratio == pytest.approx(4000.0 / 2400.0, rel=CONVERTER_TOLERANCE)


def test_calculate_from_slowness_matches_velocity() -> None:
    density = 2650.0
    p_wave_velocity = 4000.0
    s_wave_velocity = 2400.0

    p_wave_slowness = DynamicElasticPropertiesCalculation.convert_velocity_to_slowness(p_wave_velocity)
    s_wave_slowness = DynamicElasticPropertiesCalculation.convert_velocity_to_slowness(s_wave_velocity)

    from_velocity = DynamicElasticPropertiesCalculation.calculate_from_velocity(p_wave_velocity, s_wave_velocity, density)
    from_slowness = DynamicElasticPropertiesCalculation.calculate_from_slowness(p_wave_slowness, s_wave_slowness, density)

    assert from_slowness.bulk_modulus == pytest.approx(from_velocity.bulk_modulus, rel=1e-9)
    assert from_slowness.youngs_modulus == pytest.approx(from_velocity.youngs_modulus, rel=1e-9)
    assert from_slowness.shear_modulus == pytest.approx(from_velocity.shear_modulus, rel=1e-9)
    assert from_slowness.poissons_ratio == pytest.approx(from_velocity.poissons_ratio, rel=1e-9)


def test_calculate_from_velocity_array() -> None:
    p_wave_velocity = [4000.0, 3500.0]
    s_wave_velocity = [2400.0, 2000.0]
    density = [2650.0, 2550.0]

    calculated_models = DynamicElasticPropertiesCalculation.calculate_from_velocity_array(p_wave_velocity, s_wave_velocity, density)

    assert len(calculated_models) == 2
    for calculated_model, vp, vs, rho in zip(calculated_models, p_wave_velocity, s_wave_velocity, density, strict=True):
        assert isinstance(calculated_model, DynamicElasticProperties)
        assert calculated_model.shear_modulus == pytest.approx(rho * vs**2, rel=CONVERTER_TOLERANCE)
        assert calculated_model.p_wave_modulus == pytest.approx(rho * vp**2, rel=CONVERTER_TOLERANCE)
        assert calculated_model.vp_vs_ratio == pytest.approx(vp / vs, rel=CONVERTER_TOLERANCE)


def test_calculate_from_slowness_array_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        DynamicElasticPropertiesCalculation.calculate_from_slowness_array([76.2, 80.0], [127.0], [2650.0, 2600.0])
