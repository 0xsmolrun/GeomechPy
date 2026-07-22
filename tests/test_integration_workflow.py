"""End-to-end 1D Mechanical Earth Model workflow test.

Exercises the full chain: sonic/density logs -> dynamic moduli -> static calibration ->
rock strength -> pore pressure and overburden -> horizontal stresses -> mud weight
window, checking that every hand-off works and the results are physically ordered."""

import pytest
from geomechpy import (
    DynamicElasticPropertiesCalculation,
    FractureGradientCalculation,
    HorizontalStressesCalculation,
    OverburdenStressCalculation,
    PorePressureCalculation,
    RockStrengthPropertiesConverter,
    StaticElasticPropertiesConverter,
    UnitConverter,
    WellboreStabilityCalculation,
)


def test_full_mem_workflow_produces_physically_ordered_profile() -> None:
    # --- Input logs at three depths (field units) ---
    tvd = [8000.0, 9000.0, 10000.0]  # ft
    dtco = [85.0, 80.0, 76.0]        # us/ft
    dtsh = [150.0, 140.0, 132.0]     # us/ft
    rhob = [2500.0, 2550.0, 2600.0]  # kg/m3

    # --- Dynamic elastic properties from the logs (moduli in Mpsi) ---
    dynamic = DynamicElasticPropertiesCalculation.calculate_from_slowness_array(
        dtco, dtsh, rhob, modulus_unit="Mpsi"
    )
    for entry in dynamic:
        assert 0.0 < entry.poissons_ratio < 0.5
        assert entry.vp_vs_ratio > 1.0

    # --- Static calibration and rock strength ---
    yme_dyn = [entry.youngs_modulus for entry in dynamic]
    pr_dyn = [entry.poissons_ratio for entry in dynamic]
    yme_sta = StaticElasticPropertiesConverter.dyn2sta_yme_najib_array(yme_dyn)
    pr_sta = StaticElasticPropertiesConverter.dyn2sta_poissons_ratio_array(pr_dyn, multiplier=1.0)
    ucs = RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb_array(yme_sta)
    tstr = RockStrengthPropertiesConverter.convert_ucs_to_tstr_array(ucs)
    fang = RockStrengthPropertiesConverter.convert_friction_angle_lal_array(dtco)
    for strength, tensile, friction in zip(ucs, tstr, fang, strict=True):
        assert strength > 0
        assert 0 < tensile < strength
        assert 0 < friction < 90

    # --- Pore pressure and overburden (density-integrated) ---
    pore_pressure = PorePressureCalculation.calculate_pore_pressure_onshore_array(tvd=tvd)
    overburden = OverburdenStressCalculation.calculate_overburden_stress_from_density_array(tvd=tvd, density=rhob)
    for pp, sv in zip(pore_pressure, overburden, strict=True):
        assert 0 < pp < sv

    # --- Horizontal stresses (Eaton Shmin + multiplier SHmax) ---
    shmin = HorizontalStressesCalculation.calculate_shmin_eaton_array(
        overburden_stress=overburden, pore_pressure=pore_pressure, poisson_ratio=pr_sta
    )
    shmax = HorizontalStressesCalculation.calculate_shmax_multiplier_array(shmin=shmin, shmax_multiplier=1.05)
    for pp, sn, sx, sv in zip(pore_pressure, shmin, shmax, overburden, strict=True):
        assert pp < sn <= sx < sv  # normal faulting ordering

    # --- Fracture gradient bracket ---
    frac_min = FractureGradientCalculation.calculate_fracture_pressure_hubbert_willis_min_array(overburden, pore_pressure)
    frac_max = FractureGradientCalculation.calculate_fracture_pressure_hubbert_willis_max_array(overburden, pore_pressure)
    for low, high in zip(frac_min, frac_max, strict=True):
        assert low < high

    # --- Mud weight window at each depth ---
    windows = WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well_array(
        shmax=shmax, shmin=shmin, pprs=pore_pressure, overburden_stress=overburden,
        ucs=ucs, fang=fang, pr_sta=pr_sta, tstr=tstr,
    )
    for window, depth in zip(windows, tvd, strict=True):
        lower = max(window.kick_pressure, window.breakout_pressure)
        upper = min(window.loss_pressure, window.breakdown_pressure)
        assert lower < upper, f"no safe mud window at {depth} ft"

        # And the window expressed as equivalent mud weight is physically sensible
        lower_ppg = UnitConverter.convert_pressure_to_mud_weight(lower, depth)
        upper_ppg = UnitConverter.convert_pressure_to_mud_weight(upper, depth)
        assert 6.0 < lower_ppg < upper_ppg < 20.0


def test_full_workflow_is_unit_system_invariant() -> None:
    # The same workflow computed in field units and SI units must agree
    tvd_ft = 10000.0
    sv_psi = OverburdenStressCalculation.calculate_overburden_stress_onshore(tvd=tvd_ft, lithostatic_gradient=1.0)
    pp_psi = PorePressureCalculation.calculate_pore_pressure_onshore(tvd=tvd_ft)
    shmin_psi = HorizontalStressesCalculation.calculate_shmin_eaton(sv_psi, pp_psi, poisson_ratio=0.25)

    tvd_m = UnitConverter.convert_depth(tvd_ft, "ft", "m")
    sv_mpa = OverburdenStressCalculation.calculate_overburden_stress_onshore(
        tvd=tvd_m, lithostatic_gradient=UnitConverter.convert_pressure_gradient(1.0, "psi/ft", "MPa/m"),
        depth_unit="m", pressure_unit="MPa",
    )
    pp_mpa = PorePressureCalculation.calculate_pore_pressure_onshore(tvd=tvd_m, depth_unit="m", pressure_unit="MPa")
    shmin_mpa = HorizontalStressesCalculation.calculate_shmin_eaton(sv_mpa, pp_mpa, poisson_ratio=0.25)

    assert UnitConverter.convert_pressure(shmin_mpa, "MPa", "psi") == pytest.approx(shmin_psi, rel=1e-6)
