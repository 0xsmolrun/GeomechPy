"""Input validation across the core calculation classes: non-physical inputs raise descriptive errors."""

import pytest
from geomechpy import (
    DynamicElasticPropertiesCalculation,
    HorizontalStressesCalculation,
    OverburdenStressCalculation,
    PorePressureCalculation,
    WellboreStabilityCalculation,
)


class TestDynamicElasticPropertiesValidation:
    def test_negative_density_raises(self) -> None:
        with pytest.raises(ValueError, match="density must be positive"):
            DynamicElasticPropertiesCalculation.calculate_from_velocity(4000.0, 2400.0, -2650.0)

    def test_negative_velocity_raises(self) -> None:
        with pytest.raises(ValueError, match="velocities must be positive"):
            DynamicElasticPropertiesCalculation.calculate_from_velocity(-4000.0, 2400.0, 2650.0)

    def test_non_physical_vp_vs_ratio_raises(self) -> None:
        # Vp/Vs below 2/sqrt(3) implies a negative bulk modulus
        with pytest.raises(ValueError, match="non-physical"):
            DynamicElasticPropertiesCalculation.calculate_from_velocity(2400.0, 2300.0, 2650.0)

    def test_zero_slowness_raises(self) -> None:
        with pytest.raises(ValueError, match="slowness must be positive"):
            DynamicElasticPropertiesCalculation.convert_slowness_to_velocity(0.0)

    def test_zero_velocity_raises(self) -> None:
        with pytest.raises(ValueError, match="velocity must be positive"):
            DynamicElasticPropertiesCalculation.convert_velocity_to_slowness(0.0)


class TestPressureProfileValidation:
    def test_negative_tvd_raises_pore_pressure(self) -> None:
        with pytest.raises(ValueError, match="tvd must be non-negative"):
            PorePressureCalculation.calculate_pore_pressure_onshore(tvd=-100.0)

    def test_negative_air_gap_raises(self) -> None:
        with pytest.raises(ValueError, match="air_gap"):
            PorePressureCalculation.calculate_pore_pressure_onshore(tvd=1000.0, air_gap=-50.0)

    def test_negative_water_depth_raises(self) -> None:
        with pytest.raises(ValueError, match="water_depth"):
            PorePressureCalculation.calculate_pore_pressure_offshore(tvd=1000.0, water_depth=-500.0)

    def test_negative_tvd_raises_overburden(self) -> None:
        with pytest.raises(ValueError, match="tvd must be non-negative"):
            OverburdenStressCalculation.calculate_overburden_stress_onshore(tvd=-100.0)

    def test_negative_water_depth_raises_overburden(self) -> None:
        with pytest.raises(ValueError, match="water_depth"):
            OverburdenStressCalculation.calculate_overburden_stress_offshore(tvd=1000.0, water_depth=-500.0)

    def test_zero_tvd_still_allowed(self) -> None:
        assert PorePressureCalculation.calculate_pore_pressure_onshore(tvd=0.0) == 0.0


class TestStressValidation:
    def test_poisson_at_half_raises_eaton(self) -> None:
        with pytest.raises(ValueError, match="poisson_ratio"):
            HorizontalStressesCalculation.calculate_shmin_eaton(10000.0, 4700.0, poisson_ratio=0.5)

    def test_negative_poisson_raises_eaton(self) -> None:
        with pytest.raises(ValueError, match="poisson_ratio"):
            HorizontalStressesCalculation.calculate_shmin_eaton(10000.0, 4700.0, poisson_ratio=-0.1)

    def test_poisson_at_half_raises_poroelastic(self) -> None:
        with pytest.raises(ValueError, match="poisson_ratio"):
            HorizontalStressesCalculation.calculate_poroelastic_horizontal_stresses(
                overburden_stress=10000.0, pore_pressure=4700.0, poisson_ratio=0.5, youngs_modulus=2.0
            )

    def test_non_positive_k0_raises(self) -> None:
        with pytest.raises(ValueError, match="effective_stress_ratio"):
            HorizontalStressesCalculation.calculate_shmin_effective_stress_ratio(10000.0, 4700.0, effective_stress_ratio=0.0)


class TestWellboreStabilityValidation:
    def test_friction_angle_at_ninety_raises_analytical(self) -> None:
        with pytest.raises(ValueError, match="friction angle"):
            WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(
                shmax=12000.0, shmin=10000.0, pprs=5000.0, overburden_stress=13000.0,
                ucs=5000.0, fang=90.0, pr_sta=0.25,
            )

    def test_negative_friction_angle_raises_numerical(self) -> None:
        with pytest.raises(ValueError, match="friction angle"):
            WellboreStabilityCalculation.calculate_breakout_pressure_deviated_well_mohr_coulomb(
                shmax=12000.0, shmin=10000.0, overburden_stress=13000.0, pprs=5000.0,
                ucs=5000.0, fang=-5.0, pr_sta=0.25, borehole_deviation=0.0, borehole_azimuth=0.0,
            )
