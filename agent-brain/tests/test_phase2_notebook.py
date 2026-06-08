import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/phase2-risk-to-cost-demo.ipynb")


def test_phase2_notebook_is_documented_and_imports_reusable_demo_module() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    markdown = "\n".join(
        "".join(cell["source"]) for cell in cells if cell["cell_type"] == "markdown"
    )
    code = "\n".join("".join(cell["source"]) for cell in cells if cell["cell_type"] == "code")

    assert "Phase 2 Risk-to-Cost Retrieval Demo" in markdown
    assert "Prerequisites and run order" in markdown
    assert "Limitations and reset instructions" in markdown
    assert "from agent_brain.demo.curated_risk_to_cost import" in code
    assert "run_curated_demo()" in code
    assert "assert_curated_demo_passed(demo_results)" in code
