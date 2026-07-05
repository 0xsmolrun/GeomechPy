import pytest
from geomechpy.overburden_stress import OverburdenStressCalculation

TOLERANCE = 1e-6


class TestOverburdenStressOnshore:
    def test_default_gradient_no_air_gap(self) -> None:
        result = OverburdenStressCalculation.calculate_overburden_stress_onshore(tvd=10000)
        assert result == pytest.approx(10500.0, rel=TOLERANCE)

    def test_below_air_gap_uses_air_gradient(self) -> None:
        result = OverburdenStressCalculation.calculate_overburden_stress_onshore(tvd=50, air_gap=100)
        assert result == pytest.approx(0.0004 * 50, rel=TOLERANCE)

    def test_above_air_gap_includes_air_pressure(self) -> None:
        result = OverburdenStressCalculation.calculate_overburden_stress_onshore(tvd=10000, lithostatic_gradient=1.05, air_gap=100)
        expected = 0.0004 * 100 + 1.05 * (10000 - 100)
        assert result == pytest.approx(expected, rel=TOLERANCE)

    def test_zero_tvd(self) -> None:
        result = OverburdenStressCalculation.calculate_overburden_stress_onshore(tvd=0, air_gap=100)
        assert result == pytest.approx(0.0, abs=TOLERANCE)

    def test_custom_lithostatic_gradient(self) -> None:
        result = OverburdenStressCalculation.calculate_overburden_stress_onshore(tvd=5000, lithostatic_gradient=0.9)
        assert result == pytest.approx(4500.0, rel=TOLERANCE)


class TestOverburdenStressOffshore:
    def test_below_air_gap(self) -> None:
        result = OverburdenStressCalculation.calculate_overburden_stress_offshore(tvd=50, air_gap=100, water_depth=1000)
        assert result == pytest.approx(0.0004 * 50, rel=TOLERANCE)

    def test_within_water_column(self) -> None:
        result = OverburdenStressCalculation.calculate_overburden_stress_offshore(tvd=500, air_gap=100, water_depth=1000)
        expected = 0.0004 * 100 + 0.47 * (500 - 100)
        assert result == pytest.approx(expected, rel=TOLERANCE)

    def test_below_seabed(self) -> None:
        result = OverburdenStressCalculation.calculate_overburden_stress_offshore(tvd=10000, air_gap=100, water_depth=1000)
        expected = 0.0004 * 100 + 0.47 * 1000 + 1.05 * (10000 - 1000 - 100)
        assert result == pytest.approx(expected, rel=TOLERANCE)

    def test_no_water_no_air_matches_onshore(self) -> None:
        offshore = OverburdenStressCalculation.calculate_overburden_stress_offshore(tvd=8000)
        onshore = OverburdenStressCalculation.calculate_overburden_stress_onshore(tvd=8000)
        assert offshore == pytest.approx(onshore, rel=TOLERANCE)

    def test_custom_sea_water_gradient(self) -> None:
        result = OverburdenStressCalculation.calculate_overburden_stress_offshore(
            tvd=500, air_gap=0, water_depth=1000, sea_water_pressure_gradient=0.45
        )
        assert result == pytest.approx(0.45 * 500, rel=TOLERANCE)


class TestDensityIntegratedOverburden:
    def test_constant_density_matches_gradient_method(self) -> None:
        # 2306.66 kg/m3 exerts exactly 1.0 psi/ft under standard gravity
        from geomechpy.units import UnitConverter

        density_kg_m3 = UnitConverter.convert_pressure_gradient(1.0, "psi/ft", "Pa/m") / 9.80665
        tvd = [1000.0, 2000.0, 3000.0]
        result = OverburdenStressCalculation.calculate_overburden_stress_from_density_array(
            tvd=tvd, density=[density_kg_m3] * 3
        )
        expected = OverburdenStressCalculation.calculate_overburden_stress_onshore_array(tvd=tvd, lithostatic_gradient=1.0)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_offshore_water_column_is_added(self) -> None:
        from geomechpy.units import UnitConverter

        onshore = OverburdenStressCalculation.calculate_overburden_stress_from_density_array(
            tvd=[2000.0, 3000.0], density=[2400.0, 2500.0]
        )
        offshore = OverburdenStressCalculation.calculate_overburden_stress_from_density_array(
            tvd=[3000.0, 4000.0], density=[2400.0, 2500.0], water_depth=1000.0, sea_water_density=1025.0
        )
        water_pressure_psi = UnitConverter.convert_pressure(
            1025.0 * 9.80665 * UnitConverter.convert_depth(1000.0, "ft", "m"), "Pa", "psi"
        )
        assert offshore[0] - onshore[0] == pytest.approx(water_pressure_psi, rel=1e-6)
        assert offshore[1] - onshore[1] == pytest.approx(water_pressure_psi, rel=1e-6)

    def test_metric_units(self) -> None:
        field = OverburdenStressCalculation.calculate_overburden_stress_from_density_array(
            tvd=[3280.839895013123], density=[2.5], density_unit="g/cm3"
        )
        metric = OverburdenStressCalculation.calculate_overburden_stress_from_density_array(
            tvd=[1000.0], density=[2500.0], depth_unit="m", pressure_unit="MPa"
        )
        from geomechpy.units import UnitConverter

        assert UnitConverter.convert_pressure(metric[0], "MPa", "psi") == pytest.approx(field[0], rel=1e-6)

    def test_unsorted_tvd_raises(self) -> None:
        with pytest.raises(ValueError, match="sorted"):
            OverburdenStressCalculation.calculate_overburden_stress_from_density_array(
                tvd=[2000.0, 1000.0], density=[2400.0, 2500.0]
            )

    def test_tvd_above_mudline_raises(self) -> None:
        with pytest.raises(ValueError, match="mudline"):
            OverburdenStressCalculation.calculate_overburden_stress_from_density_array(
                tvd=[500.0], density=[2400.0], water_depth=1000.0
            )

    def test_mismatched_lengths_raise(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            OverburdenStressCalculation.calculate_overburden_stress_from_density_array(
                tvd=[1000.0, 2000.0], density=[2400.0]
            )
