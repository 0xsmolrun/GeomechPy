import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
from geomechpy.dynamic_elastic_properties import DynamicElasticPropertiesCalculation
from geomechpy.plotting import (
    plot_elastic_properties,
    plot_mem_profile,
    plot_mud_weight_window,
    plot_stress_polygon,
)
from geomechpy.wellbore_stability import WellboreStabilityCalculation

TVD = [8000.0, 9000.0, 10000.0]


def _windows():
    return WellboreStabilityCalculation.calculate_mud_weight_window_vertical_well_array(
        shmax=[8400.0, 9450.0, 10500.0],
        shmin=[8000.0, 9000.0, 10000.0],
        pprs=[3760.0, 4230.0, 4700.0],
        overburden_stress=[9600.0, 10800.0, 12000.0],
        ucs=[5000.0, 5200.0, 5400.0],
        fang=[30.0, 30.0, 30.0],
        pr_sta=[0.25, 0.25, 0.25],
        tstr=[750.0, 780.0, 810.0],
    )


class TestPlotMudWeightWindow:
    def test_returns_figure_with_expected_curves(self) -> None:
        figure = plot_mud_weight_window(TVD, _windows())
        ax = figure.axes[0]
        labels = [line.get_label() for line in ax.get_lines()]
        assert "Pore pressure (kick)" in labels
        assert "Breakdown" in labels
        assert ax.get_ylabel() == "TVD [ft]"
        assert ax.get_xlabel() == "Pressure [psi]"
        assert ax.yaxis_inverted()
        plt.close(figure)

    def test_as_mud_weight_converts_axis(self) -> None:
        figure = plot_mud_weight_window(TVD, _windows(), as_mud_weight=True, mud_weight_unit="ppg")
        ax = figure.axes[0]
        assert ax.get_xlabel() == "Equivalent mud weight [ppg]"
        # Kick line should sit near the hydrostatic-ish EMW, not near psi magnitudes
        kick_line = next(line for line in ax.get_lines() if line.get_label() == "Pore pressure (kick)")
        assert all(5.0 < value < 15.0 for value in kick_line.get_xdata())
        plt.close(figure)

    def test_mud_pressure_overlay_and_existing_axes(self) -> None:
        _, ax = plt.subplots()
        figure = plot_mud_weight_window(TVD, _windows(), mud_pressure=[4200.0, 4700.0, 5200.0], ax=ax)
        labels = [line.get_label() for line in ax.get_lines()]
        assert "Mud pressure" in labels
        plt.close(figure)

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            plot_mud_weight_window([8000.0], _windows())


class TestPlotMemProfile:
    def test_one_axes_per_track(self) -> None:
        figure = plot_mem_profile(
            TVD,
            tracks={
                "Pressures": {"Pp": [3760.0, 4230.0, 4700.0], "Sv": [9600.0, 10800.0, 12000.0]},
                "Strength": {"UCS": [5000.0, 5200.0, 5400.0]},
            },
            track_units={"Pressures": "psi"},
        )
        assert len(figure.axes) == 2
        assert figure.axes[0].get_xlabel() == "Pressures [psi]"
        assert figure.axes[1].get_xlabel() == "Strength"
        assert figure.axes[0].yaxis_inverted()
        plt.close(figure)

    def test_single_track(self) -> None:
        figure = plot_mem_profile(TVD, tracks={"Pp": {"Pp": [3760.0, 4230.0, 4700.0]}})
        assert len(figure.axes) == 1
        plt.close(figure)

    def test_empty_tracks_raise(self) -> None:
        with pytest.raises(ValueError, match="at least one track"):
            plot_mem_profile(TVD, tracks={})

    def test_curve_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="does not match"):
            plot_mem_profile(TVD, tracks={"Pp": {"Pp": [1.0, 2.0]}})


class TestPlotStressPolygon:
    def test_polygon_contains_regime_annotations_and_state(self) -> None:
        figure = plot_stress_polygon(shmin=8000.0, shmax=9000.0, overburden_stress=10000.0, pore_pressure=4500.0)
        ax = figure.axes[0]
        annotations = [child.get_text() for child in ax.texts]
        assert {"NF", "SS", "RF"} <= set(annotations)
        state_line = next(line for line in ax.get_lines() if line.get_label() == "Stress state")
        assert state_line.get_xdata()[0] == 8000.0
        assert state_line.get_ydata()[0] == 9000.0
        plt.close(figure)

    def test_polygon_geometry_matches_frictional_limits(self) -> None:
        # mu = 0.6 -> q ~ 4.68; NF limit = (Sv-Pp)/q + Pp, RF limit = q*(Sv-Pp) + Pp
        import math

        mu, sv, pp = 0.6, 10000.0, 4500.0
        q = (math.sqrt(mu**2 + 1) + mu) ** 2
        figure = plot_stress_polygon(shmin=8000.0, shmax=9000.0, overburden_stress=sv, pore_pressure=pp, friction_coefficient=mu)
        polygon_line = figure.axes[0].get_lines()[0]
        assert min(polygon_line.get_xdata()) == pytest.approx((sv - pp) / q + pp, rel=1e-9)
        assert max(polygon_line.get_ydata()) == pytest.approx(q * (sv - pp) + pp, rel=1e-9)
        plt.close(figure)


class TestPlotElasticProperties:
    def test_dynamic_properties_get_vp_vs_track(self) -> None:
        dynamic = DynamicElasticPropertiesCalculation.calculate_from_slowness_array(
            [85.0, 80.0, 76.0], [150.0, 140.0, 132.0], [2500.0, 2550.0, 2600.0], modulus_unit="GPa"
        )
        figure = plot_elastic_properties(TVD, dynamic, modulus_unit="GPa")
        assert len(figure.axes) == 3  # modulus, Poisson's ratio, Vp/Vs
        assert figure.axes[0].get_xlabel() == "Young's modulus [GPa]"
        plt.close(figure)

    def test_static_overlay_adds_curve(self) -> None:
        dynamic = DynamicElasticPropertiesCalculation.calculate_from_slowness_array(
            [85.0, 80.0, 76.0], [150.0, 140.0, 132.0], [2500.0, 2550.0, 2600.0], modulus_unit="GPa"
        )
        static = [entry.youngs_modulus * 0.6 for entry in dynamic]
        figure = plot_elastic_properties(TVD, dynamic, static_youngs_modulus=static, modulus_unit="GPa")
        labels = [line.get_label() for line in figure.axes[0].get_lines()]
        assert "E dynamic" in labels
        assert "E static" in labels
        plt.close(figure)

    def test_length_mismatch_raises(self) -> None:
        dynamic = DynamicElasticPropertiesCalculation.calculate_from_slowness_array([85.0], [150.0], [2500.0])
        with pytest.raises(ValueError, match="same length"):
            plot_elastic_properties(TVD, dynamic)


class TestPlotlyBackend:
    def test_mud_weight_window_plotly(self) -> None:
        plotly = pytest.importorskip("plotly")
        figure = plot_mud_weight_window(TVD, _windows(), as_mud_weight=True, backend="plotly",
                                        mud_pressure=[4200.0, 4700.0, 5200.0])
        import plotly.graph_objects as go
        assert isinstance(figure, go.Figure)
        names = [trace.name for trace in figure.data]
        assert "Safe window" in names
        assert "Breakdown" in names
        assert "Mud pressure" in names
        assert figure.layout.yaxis.autorange == "reversed"

    def test_mem_profile_plotly(self) -> None:
        pytest.importorskip("plotly")
        import plotly.graph_objects as go
        figure = plot_mem_profile(
            TVD,
            tracks={"Pressures": {"Pp": [1.0, 2.0, 3.0]}, "Strength": {"UCS": [4.0, 5.0, 6.0]}},
            track_units={"Pressures": "psi"},
            backend="plotly",
        )
        assert isinstance(figure, go.Figure)
        assert len(figure.data) == 2
        subplot_titles = [annotation.text for annotation in figure.layout.annotations]
        assert "Pressures [psi]" in subplot_titles

    def test_stress_polygon_plotly_geometry(self) -> None:
        pytest.importorskip("plotly")
        import math
        mu, sv, pp = 0.6, 10000.0, 4500.0
        q = (math.sqrt(mu**2 + 1) + mu) ** 2
        figure = plot_stress_polygon(shmin=8000.0, shmax=9000.0, overburden_stress=sv,
                                     pore_pressure=pp, friction_coefficient=mu, backend="plotly")
        polygon = figure.data[0]
        assert min(polygon.x) == pytest.approx((sv - pp) / q + pp, rel=1e-9)
        assert max(polygon.y) == pytest.approx(q * (sv - pp) + pp, rel=1e-9)

    def test_elastic_properties_plotly_passthrough(self) -> None:
        pytest.importorskip("plotly")
        import plotly.graph_objects as go
        dynamic = DynamicElasticPropertiesCalculation.calculate_from_slowness_array(
            [85.0, 80.0, 76.0], [150.0, 140.0, 132.0], [2500.0, 2550.0, 2600.0], modulus_unit="GPa"
        )
        figure = plot_elastic_properties(TVD, dynamic, modulus_unit="GPa", backend="plotly")
        assert isinstance(figure, go.Figure)

    def test_unknown_backend_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported backend"):
            plot_mud_weight_window(TVD, _windows(), backend="bokeh")

    def test_ax_with_plotly_raises(self) -> None:
        pytest.importorskip("plotly")
        _, ax = plt.subplots()
        with pytest.raises(ValueError, match="only applies to the matplotlib backend"):
            plot_mud_weight_window(TVD, _windows(), ax=ax, backend="plotly")
        plt.close("all")
