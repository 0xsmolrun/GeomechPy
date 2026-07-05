import pytest
from geomechpy.fracture_gradient import FractureGradientCalculation
from geomechpy.stress_calculations import HorizontalStressesCalculation

TOLERANCE = 1e-6


class TestHubbertWillis:
    def test_min_known_value(self) -> None:
        # (Sv + 2*Pp)/3 = (9000 + 2*4000)/3 = 5666.67
        result = FractureGradientCalculation.calculate_fracture_pressure_hubbert_willis_min(overburden_stress=9000.0, pore_pressure=4000.0)
        assert result == pytest.approx((9000 + 2 * 4000) / 3, rel=TOLERANCE)

    def test_max_known_value(self) -> None:
        # (Sv + Pp)/2 = (9000 + 4000)/2 = 6500
        result = FractureGradientCalculation.calculate_fracture_pressure_hubbert_willis_max(overburden_stress=9000.0, pore_pressure=4000.0)
        assert result == pytest.approx(6500.0, rel=TOLERANCE)

    def test_max_exceeds_min(self) -> None:
        low = FractureGradientCalculation.calculate_fracture_pressure_hubbert_willis_min(overburden_stress=9000.0, pore_pressure=4000.0)
        high = FractureGradientCalculation.calculate_fracture_pressure_hubbert_willis_max(overburden_stress=9000.0, pore_pressure=4000.0)
        assert high > low

    def test_hydrostatic_equals_overburden_when_pp_equals_sv(self) -> None:
        result = FractureGradientCalculation.calculate_fracture_pressure_hubbert_willis_min(overburden_stress=9000.0, pore_pressure=9000.0)
        assert result == pytest.approx(9000.0, rel=TOLERANCE)


class TestMatthewsKelly:
    def test_known_value(self) -> None:
        # Ki*(Sv - Pp) + Pp = 0.6*5000 + 4000 = 7000
        result = FractureGradientCalculation.calculate_fracture_pressure_matthews_kelly(
            overburden_stress=9000.0, pore_pressure=4000.0, matrix_stress_coefficient=0.6
        )
        assert result == pytest.approx(7000.0, rel=TOLERANCE)

    def test_ki_of_one_returns_overburden(self) -> None:
        result = FractureGradientCalculation.calculate_fracture_pressure_matthews_kelly(
            overburden_stress=9000.0, pore_pressure=4000.0, matrix_stress_coefficient=1.0
        )
        assert result == pytest.approx(9000.0, rel=TOLERANCE)


class TestEaton:
    def test_known_value(self) -> None:
        # v/(1-v)*(Sv - Pp) + Pp = (0.25/0.75)*5000 + 4000 = 5666.67
        result = FractureGradientCalculation.calculate_fracture_pressure_eaton(
            overburden_stress=9000.0, pore_pressure=4000.0, poisson_ratio=0.25
        )
        assert result == pytest.approx(4000 + 5000 / 3, rel=TOLERANCE)

    def test_equals_eaton_shmin(self) -> None:
        fracture = FractureGradientCalculation.calculate_fracture_pressure_eaton(
            overburden_stress=9000.0, pore_pressure=4000.0, poisson_ratio=0.3
        )
        shmin = HorizontalStressesCalculation.calculate_shmin_eaton(
            overburden_stress=9000.0, pore_pressure=4000.0, poisson_ratio=0.3
        )
        assert fracture == pytest.approx(shmin, rel=TOLERANCE)


class TestArrayVersions:
    def test_matthews_kelly_array(self) -> None:
        result = FractureGradientCalculation.calculate_fracture_pressure_matthews_kelly_array(
            overburden_stress=[9000.0, 10000.0],
            pore_pressure=[4000.0, 4700.0],
            matrix_stress_coefficient=[0.6, 0.7],
        )
        assert result == pytest.approx([7000.0, 8410.0], rel=TOLERANCE)

    def test_eaton_array_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError):
            FractureGradientCalculation.calculate_fracture_pressure_eaton_array(
                overburden_stress=[9000.0], pore_pressure=[4000.0, 4700.0], poisson_ratio=[0.25, 0.25]
            )
