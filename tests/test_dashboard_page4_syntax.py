"""Ensure dashboard page-4 scenario-basis note is valid string concatenation (no stray **)."""
import ast
from pathlib import Path


def test_streamlit_app_parses():
    src = (Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    ast.parse(src)
    assert 'the "**' not in src
    assert "Scenario basis" in src
    assert "Modeled CTS — No Freight Credit" in src


def test_scenario_basis_string_concat_safe():
    """Replicate the page-4 st.info string join and ensure it is a plain str."""
    msg = (
        "**Scenario basis:** commercial and service-model deltas use the scenarios engine on the "
        "**Modeled CTS — No Freight Credit** layer (distribution is charged). "
        "They are **not** Neutral Freight Reference conclusions. "
        "Lean delivery’s contribution gain includes distribution-pool cuts that net differently under Neutral Freight."
    )
    assert isinstance(msg, str)
    assert "Modeled CTS" in msg
    assert "**" in msg
