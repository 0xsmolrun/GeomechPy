import math

import pytest
from geomechpy.wellbore_stability import MudWeightWindow, WellboreStabilityCalculation

TOLERANCE = 1e-6


class TestBreakdownPressure:
    def test_known_value(self) -> None:
        result = WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical(
            shmax=12000, shmin=10000, pprs=5000, tstr=500
        )
        # 3*shmin - shmax - pprs + tstr = 30000 - 12000 - 5000 + 500
        assert result == pytest.approx(13500.0, rel=TOLERANCE)

    def test_returns_float(self) -> None:
        result = WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical(
            shmax=12000, shmin=10000, pprs=5000, tstr=500
        )
        assert isinstance(result, float)

    def test_zero_tensile_strength(self) -> None:
        result = WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical(
            shmax=12000, shmin=10000, pprs=5000, tstr=0
        )
        assert result == pytest.approx(13000.0, rel=TOLERANCE)

    def test_breakdown_increases_with_tensile_strength(self) -> None:
        low_tstr_breakdown = WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical(
            shmax=12000, shmin=10000, pprs=5000, tstr=100
        )
        high_tstr_breakdown = WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical(
            shmax=12000, shmin=10000, pprs=5000, tstr=1000
        )
        assert high_tstr_breakdown > low_tstr_breakdown


class TestBreakoutPressure:
    def test_known_value(self) -> None:
        # shmax=12000, shmin=10000, pprs=5000, overburden=13000, ucs=8000, fang=30, pr_sta=0.25
        # q = tan(60)^2 = 3
        # CC = 8000 - 5000*(3-1) = -2000
        # A = 3*12000 - 10000 = 26000
        # B = 13000 + 2*0.25*(12000-10000) = 14000
        # Pw_z_t_r = (14000 - (-2000))/3 = 16000/3
        # Pw_t_z_r = (26000 - (-2000))/4 = 7000
        # Pw_t_r_z = 26000 - (-2000) - 3*14000 = -14000
        # max -> 7000
        result = WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(
            shmax=12000, shmin=10000, pprs=5000, overburden_stress=13000, ucs=8000, fang=30, pr_sta=0.25
        )
        assert result == pytest.approx(7000.0, rel=TOLERANCE)

    def test_returns_float(self) -> None:
        result = WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(
            shmax=12000, shmin=10000, pprs=5000, overburden_stress=13000, ucs=8000, fang=30, pr_sta=0.25
        )
        assert isinstance(result, float)

    def test_breakout_decreases_with_higher_ucs(self) -> None:
        low_ucs_breakout = WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(
            shmax=12000, shmin=10000, pprs=5000, overburden_stress=13000, ucs=2000, fang=30, pr_sta=0.25
        )
        high_ucs_breakout = WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(
            shmax=12000, shmin=10000, pprs=5000, overburden_stress=13000, ucs=15000, fang=30, pr_sta=0.25
        )
        assert low_ucs_breakout > high_ucs_breakout

    def test_picks_maximum_of_three_scenarios(self) -> None:
        # Manually compute the three scenarios and confirm the function returns the max
        shmax = 12000
        shmin = 10000
        pore_pressure = 5000
        overburden_stress = 13000
        ucs = 8000
        friction_angle = 30
        poisson_ratio_static = 0.25

        passive_earth_pressure_coefficient = math.tan(math.radians(45) + math.radians(friction_angle / 2)) ** 2
        cohesion_term = ucs - pore_pressure * (passive_earth_pressure_coefficient - 1)
        tangential_stress_term = 3 * shmax - shmin
        axial_stress_term = overburden_stress + 2 * poisson_ratio_static * (shmax - shmin)

        scenario_pressures = [
            (axial_stress_term - cohesion_term) / passive_earth_pressure_coefficient,
            (tangential_stress_term - cohesion_term) / (1 + passive_earth_pressure_coefficient),
            tangential_stress_term - cohesion_term - passive_earth_pressure_coefficient * axial_stress_term,
        ]
        expected_breakout = max(scenario_pressures)

        result = WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(
            shmax=shmax,
            shmin=shmin,
            pprs=pore_pressure,
            overburden_stress=overburden_stress,
            ucs=ucs,
            fang=friction_angle,
            pr_sta=poisson_ratio_static,
        )
        assert result == pytest.approx(expected_breakout, rel=TOLERANCE)


class TestDeviatedWellBreakout:
    def test_vertical_limit_matches_analytical(self) -> None:
        # A well with zero deviation must reproduce the analytical vertical solution
        analytical = WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(
            shmax=12000.0, shmin=10000.0, pprs=5000.0, overburden_stress=13000.0, ucs=5000.0, fang=30.0, pr_sta=0.25
        )
        numerical = WellboreStabilityCalculation.calculate_breakout_pressure_deviated_well_mohr_coulomb(
            shmax=12000.0, shmin=10000.0, overburden_stress=13000.0, pprs=5000.0, ucs=5000.0, fang=30.0, pr_sta=0.25,
            borehole_deviation=0.0, borehole_azimuth=0.0,
        )
        assert numerical == pytest.approx(analytical, rel=1e-4)

    def test_no_stable_pressure_raises(self) -> None:
        # Extreme stress anisotropy with negligible strength: no mud pressure can stabilize
        with pytest.raises(ValueError, match="No stable mud pressure"):
            WellboreStabilityCalculation.calculate_breakout_pressure_deviated_well_mohr_coulomb(
                shmax=30000.0, shmin=5000.0, overburden_stress=10000.0, pprs=4000.0, ucs=100.0, fang=10.0, pr_sta=0.25,
                borehole_deviation=0.0, borehole_azimuth=0.0,
            )


class TestDeviatedWellBreakdown:
    def test_vertical_limit_matches_analytical(self) -> None:
        analytical = WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical(
            shmax=12000.0, shmin=10000.0, pprs=5000.0, tstr=750.0
        )
        numerical = WellboreStabilityCalculation.calculate_breakdown_pressure_deviated_well(
            shmax=12000.0, shmin=10000.0, overburden_stress=13000.0, pprs=5000.0, tstr=750.0, pr_sta=0.25,
            borehole_deviation=0.0, borehole_azimuth=0.0,
        )
        assert numerical == pytest.approx(analytical, rel=1e-4)


class TestMudWeightWindow:
    def test_vertical_window_fields(self) -> None:
        window = WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well(
            shmax=12000.0, shmin=10000.0, pprs=5000.0, overburden_stress=13000.0,
            ucs=5000.0, fang=30.0, pr_sta=0.25, tstr=750.0,
        )
        assert isinstance(window, MudWeightWindow)
        assert window.kick_pressure == pytest.approx(5000.0)
        assert window.loss_pressure == pytest.approx(10000.0)
        assert window.breakout_pressure == pytest.approx(
            WellboreStabilityCalculation.calculate_breakout_calculation_vertical_well_mohr_coulomb_analytical(
                shmax=12000.0, shmin=10000.0, pprs=5000.0, overburden_stress=13000.0, ucs=5000.0, fang=30.0, pr_sta=0.25
            ),
            rel=1e-9,
        )
        assert window.breakdown_pressure == pytest.approx(
            WellboreStabilityCalculation.calculate_breakdown_calculation_vertical_well_analytical(
                shmax=12000.0, shmin=10000.0, pprs=5000.0, tstr=750.0
            ),
            rel=1e-9,
        )
        # For this case a safe window exists
        assert max(window.kick_pressure, window.breakout_pressure) < min(window.loss_pressure, window.breakdown_pressure)

    def test_deviated_window_matches_vertical_at_zero_deviation(self) -> None:
        vertical = WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well(
            shmax=12000.0, shmin=10000.0, pprs=5000.0, overburden_stress=13000.0,
            ucs=5000.0, fang=30.0, pr_sta=0.25, tstr=750.0,
        )
        deviated = WellboreStabilityCalculation.calculate_mud_weight_window_deviated_well(
            shmax=12000.0, shmin=10000.0, pprs=5000.0, overburden_stress=13000.0,
            ucs=5000.0, fang=30.0, pr_sta=0.25, tstr=750.0,
            borehole_deviation=0.0, borehole_azimuth=0.0,
        )
        assert deviated.breakout_pressure == pytest.approx(vertical.breakout_pressure, rel=1e-4)
        assert deviated.breakdown_pressure == pytest.approx(vertical.breakdown_pressure, rel=1e-4)

    def test_highly_deviated_well_narrows_the_window(self) -> None:
        # In a normal faulting regime a highly deviated well is harder to keep stable:
        # the breakout pressure rises and the breakdown pressure falls
        vertical = WellboreStabilityCalculation.calculate_mud_weight_window_deviated_well(
            shmax=8500.0, shmin=8000.0, pprs=4500.0, overburden_stress=10000.0,
            ucs=4000.0, fang=30.0, pr_sta=0.25, tstr=500.0,
            borehole_deviation=0.0, borehole_azimuth=0.0,
        )
        deviated = WellboreStabilityCalculation.calculate_mud_weight_window_deviated_well(
            shmax=8500.0, shmin=8000.0, pprs=4500.0, overburden_stress=10000.0,
            ucs=4000.0, fang=30.0, pr_sta=0.25, tstr=500.0,
            borehole_deviation=70.0, borehole_azimuth=90.0,
        )
        vertical_window = min(vertical.loss_pressure, vertical.breakdown_pressure) - max(vertical.kick_pressure, vertical.breakout_pressure)
        deviated_window = min(deviated.loss_pressure, deviated.breakdown_pressure) - max(deviated.kick_pressure, deviated.breakout_pressure)
        assert deviated.breakout_pressure > vertical.breakout_pressure
        assert deviated_window < vertical_window

    def test_vertical_window_array(self) -> None:
        windows = WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well_array(
            shmax=[12000.0, 13000.0], shmin=[10000.0, 11000.0], pprs=[5000.0, 5500.0],
            overburden_stress=[13000.0, 14000.0], ucs=[5000.0, 5000.0], fang=[30.0, 30.0],
            pr_sta=[0.25, 0.25], tstr=[750.0, 750.0],
        )
        assert len(windows) == 2
        assert all(isinstance(w, MudWeightWindow) for w in windows)
