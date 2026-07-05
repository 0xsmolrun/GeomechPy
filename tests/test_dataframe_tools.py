import pandas as pd
import pytest
from geomechpy.dataframe_tools import add_results_to_dataframe, results_to_dataframe
from geomechpy.dynamic_elastic_properties import DynamicElasticPropertiesCalculation
from geomechpy.wellbore_stability import WellboreStabilityCalculation


class TestResultsToDataframe:
    def test_dataclass_fields_become_columns(self) -> None:
        results = DynamicElasticPropertiesCalculation.calculate_from_velocity_array(
            p_wave_velocity=[4000.0, 3500.0],
            s_wave_velocity=[2400.0, 2000.0],
            density=[2650.0, 2550.0],
        )
        frame = results_to_dataframe(results)

        assert len(frame) == 2
        assert "youngs_modulus" in frame.columns
        assert "vp_vs_ratio" in frame.columns
        assert frame["p_wave_velocity"].tolist() == [4000.0, 3500.0]

    def test_index_from_tvd(self) -> None:
        results = WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well_array(
            shmax=[12000.0, 13000.0], shmin=[10000.0, 11000.0], pprs=[5000.0, 5500.0],
            overburden_stress=[13000.0, 14000.0], ucs=[5000.0, 5000.0], fang=[30.0, 30.0],
            pr_sta=[0.25, 0.25], tstr=[750.0, 750.0],
        )
        frame = results_to_dataframe(results, index=[9000.0, 10000.0])

        assert frame.index.name == "tvd"
        assert frame.index.tolist() == [9000.0, 10000.0]
        assert set(frame.columns) == {"kick_pressure", "breakout_pressure", "loss_pressure", "breakdown_pressure"}

    def test_custom_index_name(self) -> None:
        results = DynamicElasticPropertiesCalculation.calculate_from_velocity_array(
            p_wave_velocity=[4000.0], s_wave_velocity=[2400.0], density=[2650.0]
        )
        frame = results_to_dataframe(results, index=[2500.0], index_name="depth_m")
        assert frame.index.name == "depth_m"

    def test_mismatched_index_raises(self) -> None:
        results = DynamicElasticPropertiesCalculation.calculate_from_velocity_array(
            p_wave_velocity=[4000.0], s_wave_velocity=[2400.0], density=[2650.0]
        )
        with pytest.raises(ValueError, match="same length"):
            results_to_dataframe(results, index=[1000.0, 2000.0])

    def test_non_dataclass_entries_raise(self) -> None:
        with pytest.raises(TypeError, match="dataclass instances"):
            results_to_dataframe([1.0, 2.0])


class TestAddResultsToDataframe:
    def test_columns_are_appended_with_prefix(self) -> None:
        logs = pd.DataFrame(
            {"dtco": [76.2, 80.0], "dtsh": [127.0, 135.5], "rhob": [2650.0, 2600.0]},
            index=pd.Index([2500.0, 2510.0], name="tvd"),
        )
        results = DynamicElasticPropertiesCalculation.calculate_from_slowness_array(
            p_wave_slowness=logs["dtco"].tolist(),
            s_wave_slowness=logs["dtsh"].tolist(),
            density=logs["rhob"].tolist(),
        )
        combined = add_results_to_dataframe(logs, results, prefix="dyn_")

        assert "dyn_youngs_modulus" in combined.columns
        assert "dtco" in combined.columns
        assert combined.index.tolist() == [2500.0, 2510.0]
        # Input frame is not mutated
        assert "dyn_youngs_modulus" not in logs.columns

    def test_length_mismatch_raises(self) -> None:
        logs = pd.DataFrame({"dtco": [76.2, 80.0]})
        results = DynamicElasticPropertiesCalculation.calculate_from_velocity_array(
            p_wave_velocity=[4000.0], s_wave_velocity=[2400.0], density=[2650.0]
        )
        with pytest.raises(ValueError, match="same length"):
            add_results_to_dataframe(logs, results)
