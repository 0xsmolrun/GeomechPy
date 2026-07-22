import pytest
from geomechpy import (
    DynamicElasticPropertiesCalculation,
    HorizontalStressesCalculation,
    MechanicalEarthModel,
    MudWeightWindow,
    OverburdenStressCalculation,
    PorePressureCalculation,
    RockStrengthPropertiesConverter,
    StaticElasticPropertiesConverter,
    UnitConverter,
    WellboreStabilityCalculation,
)

TOLERANCE = 1e-9

TVD = [8000.0, 9000.0, 10000.0]
DTCO = [85.0, 80.0, 76.0]
DTSH = [150.0, 140.0, 132.0]
RHOB = [2500.0, 2550.0, 2600.0]


def _model() -> MechanicalEarthModel:
    return MechanicalEarthModel(tvd=TVD, dtco=DTCO, dtsh=DTSH, rhob=RHOB)


class TestConstruction:
    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            MechanicalEarthModel(tvd=TVD, dtco=DTCO[:2], dtsh=DTSH, rhob=RHOB)

    def test_single_sample_raises(self) -> None:
        with pytest.raises(ValueError, match="two depth samples"):
            MechanicalEarthModel(tvd=[8000.0], dtco=[85.0], dtsh=[150.0], rhob=[2500.0])

    def test_unsorted_tvd_raises(self) -> None:
        with pytest.raises(ValueError, match="sorted"):
            MechanicalEarthModel(tvd=[9000.0, 8000.0], dtco=[85.0, 80.0], dtsh=[150.0, 140.0], rhob=[2500.0, 2550.0])

    def test_metric_inputs_convert_to_field_units(self) -> None:
        field = _model()
        metric = MechanicalEarthModel(
            tvd=UnitConverter.convert_depth_array(TVD, "ft", "m"),
            dtco=UnitConverter.convert_slowness_array(DTCO, "us/ft", "us/m"),
            dtsh=UnitConverter.convert_slowness_array(DTSH, "us/ft", "us/m"),
            rhob=[2.5, 2.55, 2.6],
            depth_unit="m", slowness_unit="us/m", density_unit="g/cm3",
        )
        assert metric.tvd == pytest.approx(field.tvd, rel=TOLERANCE)
        assert metric.dtco == pytest.approx(field.dtco, rel=TOLERANCE)
        assert metric.rhob == pytest.approx(field.rhob, rel=TOLERANCE)


class TestWorkflowOrdering:
    def test_rock_strength_before_elastic_raises(self) -> None:
        with pytest.raises(RuntimeError, match="sta_youngs_modulus"):
            _model().calculate_rock_strength()

    def test_stresses_before_pressures_raises(self) -> None:
        with pytest.raises(RuntimeError, match="pore_pressure"):
            _model().calculate_elastic_properties().calculate_stresses()

    def test_stability_before_stresses_raises(self) -> None:
        with pytest.raises(RuntimeError, match="shmin"):
            (_model().calculate_elastic_properties().calculate_rock_strength()
             .calculate_pore_pressure().calculate_overburden().calculate_wellbore_stability())

    def test_unknown_calibration_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown calibration"):
            _model().calculate_elastic_properties(calibration="not-a-calibration")

    def test_unknown_stress_method_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown stress method"):
            (_model().calculate_elastic_properties().calculate_pore_pressure()
             .calculate_overburden().calculate_stresses(method="magic"))


class TestWorkflowResults:
    def test_methods_chain_and_return_self(self) -> None:
        mem = _model()
        assert mem.calculate_elastic_properties() is mem

    def test_calculate_all_matches_manual_chain(self) -> None:
        mem = _model().calculate_all(pore_pressure_gradient=9.0, gradient_unit="ppg")

        # Rebuild the same chain by hand with the individual classes
        dynamic = DynamicElasticPropertiesCalculation.calculate_from_slowness_array(DTCO, DTSH, RHOB, modulus_unit="Mpsi")
        yme_sta = StaticElasticPropertiesConverter.dyn2sta_yme_najib_array([d.youngs_modulus for d in dynamic])
        pr_sta = [d.poissons_ratio for d in dynamic]
        ucs = RockStrengthPropertiesConverter.convert_yme_sta_to_ucs_plumb_array(yme_sta)
        pp = PorePressureCalculation.calculate_pore_pressure_onshore_array(tvd=TVD, formation_pore_pressure_gradient=9.0, gradient_unit="ppg")
        sv = OverburdenStressCalculation.calculate_overburden_stress_from_density_array(tvd=TVD, density=RHOB)
        shmin = HorizontalStressesCalculation.calculate_shmin_eaton_array(sv, pp, pr_sta)

        assert mem.results["sta_youngs_modulus"] == pytest.approx(yme_sta, rel=TOLERANCE)
        assert mem.results["ucs"] == pytest.approx(ucs, rel=TOLERANCE)
        assert mem.results["pore_pressure"] == pytest.approx(pp, rel=TOLERANCE)
        assert mem.results["overburden"] == pytest.approx(sv, rel=TOLERANCE)
        assert mem.results["shmin"] == pytest.approx(shmin, rel=TOLERANCE)

    def test_mud_weight_window_populated(self) -> None:
        mem = _model().calculate_all(pore_pressure_gradient=9.0, gradient_unit="ppg")
        assert len(mem.mud_weight_window) == len(TVD)
        assert all(isinstance(window, MudWeightWindow) for window in mem.mud_weight_window)
        assert all(low < high for low, high in zip(mem.results["emw_lower"], mem.results["emw_upper"], strict=True))

    def test_stress_method_k0(self) -> None:
        mem = (_model().calculate_elastic_properties().calculate_rock_strength()
               .calculate_pore_pressure().calculate_overburden()
               .calculate_stresses(method="k0", effective_stress_ratio=0.8))
        expected = HorizontalStressesCalculation.calculate_shmin_effective_stress_ratio_array(
            mem.results["overburden"], mem.results["pore_pressure"], effective_stress_ratio=0.8
        )
        assert mem.results["shmin"] == pytest.approx(expected, rel=TOLERANCE)

    def test_stress_method_poroelastic_gives_anisotropy(self) -> None:
        mem = (_model().calculate_elastic_properties().calculate_rock_strength()
               .calculate_pore_pressure().calculate_overburden()
               .calculate_stresses(method="poroelastic", strain_x=0.0001, strain_y=0.0009))
        assert all(sx > sn for sn, sx in zip(mem.results["shmin"], mem.results["shmax"], strict=True))

    def test_to_dataframe(self) -> None:
        pytest.importorskip("pandas")
        mem = _model().calculate_all(pore_pressure_gradient=9.0, gradient_unit="ppg")
        frame = mem.to_dataframe()
        assert frame.index.name == "tvd"
        assert len(frame) == len(TVD)
        for column in ("dtco", "dyn_youngs_modulus", "ucs", "shmin", "emw_lower"):
            assert column in frame.columns
