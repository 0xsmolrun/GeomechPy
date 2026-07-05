import pytest
from geomechpy.stress_calculations import HorizontalStresses, HorizontalStressesCalculation

TOLERANCE = 1e-6


class TestHorizontalStressRatio:
    def test_ratio_above_one(self) -> None:
        result = HorizontalStressesCalculation.calculate_horizontal_stress_ratio(shmax=11000, shmin=10000)
        assert result == pytest.approx(1.1, rel=TOLERANCE)

    def test_ratio_equal_one(self) -> None:
        result = HorizontalStressesCalculation.calculate_horizontal_stress_ratio(shmax=10000, shmin=10000)
        assert result == pytest.approx(1.0, rel=TOLERANCE)


class TestShmaxMultiplier:
    def test_default_multiplier(self) -> None:
        assert HorizontalStressesCalculation.calculate_shmax_multiplier(shmin=10000) == pytest.approx(11000.0, rel=TOLERANCE)

    def test_custom_multiplier(self) -> None:
        assert HorizontalStressesCalculation.calculate_shmax_multiplier(shmin=10000, shmax_multiplier=1.2) == pytest.approx(12000.0, rel=TOLERANCE)


class TestStressRegimeQFactor:
    def test_normal_regime(self) -> None:
        # sigv > shmax >= shmin -> 0 <= q_factor <= 1
        q_factor = HorizontalStressesCalculation.calculate_stress_regime_q_factor(sigv=10000, shmax=8000, shmin=6000)
        assert q_factor == pytest.approx(0.5, rel=TOLERANCE)
        assert 0 <= q_factor <= 1

    def test_strike_slip_regime(self) -> None:
        # shmin < sigv <= shmax -> 1 <= q_factor <= 2
        q_factor = HorizontalStressesCalculation.calculate_stress_regime_q_factor(sigv=8000, shmax=10000, shmin=6000)
        assert q_factor == pytest.approx(1.5, rel=TOLERANCE)
        assert 1 <= q_factor <= 2

    def test_reverse_regime(self) -> None:
        # sigv <= shmin < shmax -> 2 <= q_factor <= 3
        q_factor = HorizontalStressesCalculation.calculate_stress_regime_q_factor(sigv=4000, shmax=10000, shmin=6000)
        assert q_factor == pytest.approx(2 + 2 / 6, rel=TOLERANCE)
        assert 2 <= q_factor <= 3

    def test_unclassified_regime_returns_four(self) -> None:
        # shmin > shmax (unphysical) falls into the else branch
        q_factor = HorizontalStressesCalculation.calculate_stress_regime_q_factor(sigv=5000, shmax=4000, shmin=6000)
        assert q_factor == 4


class TestPoroelasticHorizontalStresses:
    def test_returns_horizontal_stresses_dataclass(self) -> None:
        result = HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses(
            overburden_stress=10000,
            pore_pressure=4700,
            poisson_ratio=0.25,
            youngs_modulus=2.0,
        )
        assert isinstance(result, HorizontalStresses)

    def test_default_strains_value(self) -> None:
        result = HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses(
            overburden_stress=10000,
            pore_pressure=4700,
            poisson_ratio=0.25,
            youngs_modulus=2.0,
        )

        # Recompute manually using the same equations as the implementation
        strain_x = 0.0001 / 1e-3
        strain_y = 0.009 / 1e-3
        poisson_factor = 0.25 / (1 - 0.25)
        plane_strain_modulus = 2.0 / (1 - 0.25**2)
        coupling_modulus = (0.25 * 2.0) / (1 - 0.25**2)
        expected_shmin = poisson_factor * 10000 + (1 - poisson_factor) * 1.0 * 4700 + plane_strain_modulus * strain_x + coupling_modulus * strain_y
        expected_shmax = poisson_factor * 10000 + (1 - poisson_factor) * 1.0 * 4700 + plane_strain_modulus * strain_y + coupling_modulus * strain_x

        assert result.shmin == pytest.approx(expected_shmin, rel=TOLERANCE)
        assert result.shmax == pytest.approx(expected_shmax, rel=TOLERANCE)
        assert result.shmax >= result.shmin

    def test_ratio_and_q_factor_are_consistent(self) -> None:
        result = HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses(
            overburden_stress=10000,
            pore_pressure=4700,
            poisson_ratio=0.25,
            youngs_modulus=2.0,
        )
        expected_ratio = result.shmax / result.shmin
        assert result.shmax_shmin_ratio == pytest.approx(expected_ratio, rel=TOLERANCE)
        assert result.q_factor == pytest.approx(
            HorizontalStressesCalculation.calculate_stress_regime_q_factor(0.0, result.shmax, result.shmin),
            rel=TOLERANCE,
        )

    def test_isotropic_strain_yields_equal_stresses(self) -> None:
        result = HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses(
            overburden_stress=10000,
            pore_pressure=4700,
            poisson_ratio=0.25,
            youngs_modulus=2.0,
            EX=0.005,
            EY=0.005,
        )
        assert result.shmin == pytest.approx(result.shmax, rel=TOLERANCE)
        assert result.shmax_shmin_ratio == pytest.approx(1.0, rel=TOLERANCE)
