import math

import numpy as np
import pytest

from geomechpy.near_wellbore_stresses import (
    BoreholeWallStresses,
    NearWellboreStressesCalculation,
    PrincipalStresses,
)

TOLERANCE = 1e-6


class TestKirschBoreholeWallStresses:
    def test_returns_borehole_wall_stresses_dataclass(self) -> None:
        result = NearWellboreStressesCalculation.calculate_kirsch_borehole_wall_stresses(
            shmin=10000,
            shmax=12000,
            svert=13000,
            pore_pressure=5000,
            shmax_azimuth=0,
            mud_pressure=5000,
            theta=np.linspace(0, 360, 37),
            poisson_ratio_static=0.25,
            borehole_deviation=0,
            borehole_azimuth=0,
        )
        assert isinstance(result, BoreholeWallStresses)

    def test_output_arrays_have_correct_length(self) -> None:
        theta = np.linspace(0, 360, 37)
        result = NearWellboreStressesCalculation.calculate_kirsch_borehole_wall_stresses(
            shmin=10000,
            shmax=12000,
            svert=13000,
            pore_pressure=5000,
            shmax_azimuth=0,
            mud_pressure=5000,
            theta=theta,
            poisson_ratio_static=0.25,
            borehole_deviation=0,
            borehole_azimuth=0,
        )
        assert len(result.sigma_rr) == len(theta)
        assert len(result.sigma_tt) == len(theta)
        assert len(result.sigma_zz) == len(theta)
        assert len(result.sigma_tz) == len(theta)
        assert len(result.sigma_rt) == len(theta)
        assert len(result.sigma_rz) == len(theta)

    def test_sigma_rr_equals_mud_minus_pore_pressure(self) -> None:
        # sigma_rr is the borehole wall boundary condition; it is constant around the circumference
        mud_pressure = 6000
        pore_pressure = 5000
        theta = np.linspace(0, 360, 37)
        result = NearWellboreStressesCalculation.calculate_kirsch_borehole_wall_stresses(
            shmin=10000,
            shmax=12000,
            svert=13000,
            pore_pressure=pore_pressure,
            shmax_azimuth=0,
            mud_pressure=mud_pressure,
            theta=theta,
            poisson_ratio_static=0.25,
            borehole_deviation=0,
            borehole_azimuth=0,
        )
        assert result.sigma_rr == pytest.approx(np.full(len(theta), mud_pressure - pore_pressure), rel=TOLERANCE)

    def test_sigma_rt_is_zero_on_borehole_wall(self) -> None:
        theta = np.linspace(0, 360, 37)
        result = NearWellboreStressesCalculation.calculate_kirsch_borehole_wall_stresses(
            shmin=10000,
            shmax=12000,
            svert=13000,
            pore_pressure=5000,
            shmax_azimuth=0,
            mud_pressure=5000,
            theta=theta,
            poisson_ratio_static=0.25,
            borehole_deviation=0,
            borehole_azimuth=0,
        )
        assert result.sigma_rt == pytest.approx(np.zeros(len(theta)), abs=TOLERANCE)

    def test_sigma_rz_is_zero_on_borehole_wall(self) -> None:
        theta = np.linspace(0, 360, 37)
        result = NearWellboreStressesCalculation.calculate_kirsch_borehole_wall_stresses(
            shmin=10000,
            shmax=12000,
            svert=13000,
            pore_pressure=5000,
            shmax_azimuth=0,
            mud_pressure=5000,
            theta=theta,
            poisson_ratio_static=0.25,
            borehole_deviation=0,
            borehole_azimuth=0,
        )
        assert result.sigma_rz == pytest.approx(np.zeros(len(theta)), abs=TOLERANCE)

    def test_known_value_sigma_tt_vertical_well_balanced_mud(self) -> None:
        # Vertical borehole, shmax aligned North, balanced mud (mud=pprs), no shear (sxy=sxz=syz=0)
        # Effective tangential stress (Kirsch, Biot=1):
        # At theta=0 (SHmax direction): sigma_tt' = 3*shmin - shmax - 2*pp = 30000 - 12000 - 10000 = 8000
        # At theta=90:                  sigma_tt' = 3*shmax - shmin - 2*pp = 36000 - 10000 - 10000 = 16000
        result = NearWellboreStressesCalculation.calculate_kirsch_borehole_wall_stresses(
            shmin=10000,
            shmax=12000,
            svert=13000,
            pore_pressure=5000,
            shmax_azimuth=0,
            mud_pressure=5000,
            theta=np.array([0.0, 90.0]),
            poisson_ratio_static=0.25,
            borehole_deviation=0,
            borehole_azimuth=0,
        )
        assert result.sigma_tt[0] == pytest.approx(8000, rel=TOLERANCE)
        assert result.sigma_tt[1] == pytest.approx(16000, rel=TOLERANCE)

    def test_known_value_sigma_zz_vertical_well_balanced_mud(self) -> None:
        # Effective axial stress (Biot=1):
        # sigma_zz' at theta=0: svert - pp - pr*(2*(shmax-shmin)) = 13000 - 5000 - 0.25*4000 = 7000
        # sigma_zz' at theta=90: svert - pp + pr*(2*(shmax-shmin)) = 13000 - 5000 + 0.25*4000 = 9000
        result = NearWellboreStressesCalculation.calculate_kirsch_borehole_wall_stresses(
            shmin=10000,
            shmax=12000,
            svert=13000,
            pore_pressure=5000,
            shmax_azimuth=0,
            mud_pressure=5000,
            theta=np.array([0.0, 90.0]),
            poisson_ratio_static=0.25,
            borehole_deviation=0,
            borehole_azimuth=0,
        )
        assert result.sigma_zz[0] == pytest.approx(7000, rel=TOLERANCE)
        assert result.sigma_zz[1] == pytest.approx(9000, rel=TOLERANCE)


class TestKirschConsistencyWithBreakoutFormula:
    def test_effective_tangential_stress_matches_analytical_breakout_stress(self) -> None:
        # For a vertical well the effective tangential stress at the azimuth of shmin
        # (theta measured from the SHmax direction, theta=90) must equal
        # 3*shmax - shmin - pw - pp, the stress used in the analytical breakout derivation
        # (e.g. Al-Ajmi & Zimmerman 2006).
        shmin, shmax, svert = 10000.0, 12000.0, 13000.0
        pore_pressure, mud_pressure = 5000.0, 6500.0
        result = NearWellboreStressesCalculation.calculate_kirsch_borehole_wall_stresses(
            shmin=shmin,
            shmax=shmax,
            svert=svert,
            pore_pressure=pore_pressure,
            shmax_azimuth=0,
            mud_pressure=mud_pressure,
            theta=np.array([90.0]),
            poisson_ratio_static=0.25,
            borehole_deviation=0,
            borehole_azimuth=0,
        )
        expected_effective_tangential = 3 * shmax - shmin - mud_pressure - pore_pressure
        assert result.sigma_tt[0] == pytest.approx(expected_effective_tangential, rel=TOLERANCE)


class TestPrincipalStressesAnalytical:
    def test_returns_principal_stresses_dataclass(self) -> None:
        result = NearWellboreStressesCalculation.calculate_principal_stresses_analytical(
            sigma_tt=np.array([10000.0]),
            sigma_zz=np.array([8000.0]),
            sigma_tz=np.array([0.0]),
        )
        assert isinstance(result, PrincipalStresses)

    def test_sigma_1_is_greater_than_or_equal_to_sigma_2(self) -> None:
        result = NearWellboreStressesCalculation.calculate_principal_stresses_analytical(
            sigma_tt=np.array([10000.0, 8000.0]),
            sigma_zz=np.array([8000.0, 10000.0]),
            sigma_tz=np.array([1000.0, 1500.0]),
        )
        assert all(result.sigma_1 >= result.sigma_2)

    def test_no_shear_stress_principal_stresses_equal_inputs(self) -> None:
        # When sigma_tz=0 the principal stresses reduce to the input components directly
        result = NearWellboreStressesCalculation.calculate_principal_stresses_analytical(
            sigma_tt=np.array([10000.0]),
            sigma_zz=np.array([8000.0]),
            sigma_tz=np.array([0.0]),
        )
        assert result.sigma_1[0] == pytest.approx(10000.0, rel=TOLERANCE)
        assert result.sigma_2[0] == pytest.approx(8000.0, rel=TOLERANCE)

    def test_known_values(self) -> None:
        # sigma_tt=10000, sigma_zz=8000, sigma_tz=1000
        # sigma_1 = 9000 + 1000*sqrt(2) ≈ 10414.214
        # sigma_2 = 9000 - 1000*sqrt(2) ≈ 7585.786
        # theta_tortuosity = 0.5 * degrees(arctan(2000/2000)) = 0.5 * 45 = 22.5
        result = NearWellboreStressesCalculation.calculate_principal_stresses_analytical(
            sigma_tt=np.array([10000.0]),
            sigma_zz=np.array([8000.0]),
            sigma_tz=np.array([1000.0]),
        )
        assert result.sigma_1[0] == pytest.approx(9000 + 1000 * math.sqrt(2), rel=TOLERANCE)
        assert result.sigma_2[0] == pytest.approx(9000 - 1000 * math.sqrt(2), rel=TOLERANCE)
        assert result.theta_tortuosity[0] == pytest.approx(22.5, rel=TOLERANCE)
