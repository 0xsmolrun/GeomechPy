import pytest

streamlit = pytest.importorskip("streamlit", reason="streamlit extra not installed")
pytest.importorskip("plotly", reason="plotly extra not installed")

from streamlit.testing.v1 import AppTest

APP_PATH = "examples/streamlit_apps/geomechpy_mem_dashboard.py"


def _run_app() -> AppTest:
    app = AppTest.from_file(APP_PATH, default_timeout=180)
    app.run()
    return app


class TestMemDashboard:
    def test_runs_without_exceptions(self) -> None:
        app = _run_app()
        assert not app.exception
        assert len(app.tabs) == 5
        assert len(app.metric) == 4  # mud weight window status metrics

    def test_poroelastic_branch(self) -> None:
        app = _run_app()
        app.sidebar.selectbox[1].select("Poroelastic (Thiercelin & Plumb)")
        app.run()
        assert not app.exception

    def test_calibrated_k0_branch(self) -> None:
        app = _run_app()
        app.sidebar.selectbox[1].select("Calibrated K0")
        app.run()
        assert not app.exception

    def test_manual_input_mode(self) -> None:
        app = _run_app()
        app.sidebar.radio[0].set_value("Manual input")
        app.run()
        assert not app.exception

    def test_pore_pressure_slider_changes_results(self) -> None:
        app = _run_app()
        baseline = app.metric[0].value
        app.sidebar.slider[0].set_value(12.0)  # pore pressure gradient in ppg
        app.run()
        assert not app.exception
        assert app.metric[0].value != baseline  # window at TD moved with the gradient


DASHBOARD_PATH = "examples/streamlit_apps/geomechpy_dashboard.py"


def _run_dashboard() -> AppTest:
    app = AppTest.from_file(DASHBOARD_PATH, default_timeout=180)
    app.run()
    return app


class TestGeomechpyDashboard:
    def test_runs_without_exceptions(self) -> None:
        app = _run_dashboard()
        assert not app.exception
        assert len(app.tabs) == 4
        assert app.session_state["results"] is not None  # results stored per spec

    def test_poroelastic_method_branch(self) -> None:
        app = _run_dashboard()
        app.sidebar.radio[0].set_value("Poroelastic")
        app.run()
        assert not app.exception

    def test_metric_unit_system(self) -> None:
        app = _run_dashboard()
        app.sidebar.selectbox[0].select("Metric (m, MPa, SG)")
        app.run()
        assert not app.exception
        assert any("MPa" in metric.value for metric in app.metric)

    def test_load_example_button(self) -> None:
        app = _run_dashboard()
        app.sidebar.button[0].click()
        app.run()
        assert not app.exception

    def test_pore_pressure_slider_updates_metrics(self) -> None:
        app = _run_dashboard()
        baseline = app.metric[0].value
        app.sidebar.slider[0].set_value(12.0)
        app.run()
        assert not app.exception
        assert app.metric[0].value != baseline
