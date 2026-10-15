"""Integration contracts: reruns do not couple simulator data to tracking."""
import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.ui.analytics import analytics_html

ROOT = Path(__file__).resolve().parents[1]


def test_committed_analytics_is_authorized_and_only_maps_the_public_root():
    config = json.loads((ROOT / "analytics/analytics-config.json").read_text())
    assert config["enabled"] is True
    assert config["measurementId"] == "G-YRNBP3YGN7"
    assert config["pages"] == {"/": "2026年 手取り試算"}
    assert config["origin"] == "https://paycheck-insight-dfnvaodwxttypa7gtdouhj.streamlit.app"


def test_app_widget_rerun_keeps_identical_frameless_tracking_payload():
    at = AppTest.from_file(str(ROOT / "app.py")).run()
    assert not at.exception
    before = [element.proto for element in at.get("html")]
    assert len(before) == 1
    payload = before[0]
    assert payload.unsafe_allow_javascript
    assert payload.body == analytics_html()
    assert not at.get("iframe")
    # The simulator accepts real widget changes; their values never enter analytics HTML.
    at.number_input(key="annual_salary").set_value(7_900_000).run()
    assert not at.exception
    after = [element.proto for element in at.get("html")]
    assert len(after) == 1
    assert after[0].body == payload.body
    assert "7900000" not in after[0].body
    assert not at.get("iframe")


def test_static_config_cannot_break_out_of_its_script(monkeypatch, tmp_path):
    import src.ui.analytics as analytics

    (tmp_path / "analytics-config.json").write_text(json.dumps({"title": "</script><script>alert(1)</script>"}))
    (tmp_path / "analytics.js").write_text("void 0;")
    monkeypatch.setattr(analytics, "_ASSET_ROOT", tmp_path)
    html = analytics.analytics_html()
    assert html.count("</script>") == 1
    assert "\\u003c/script>" in html
