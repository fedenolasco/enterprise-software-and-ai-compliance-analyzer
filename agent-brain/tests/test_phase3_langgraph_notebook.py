import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/phase3-langgraph-hitl-demo.ipynb")


def test_phase3_langgraph_notebook_is_demo_only_and_documents_hitl_flow() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    markdown = "\n".join(
        "".join(cell["source"]) for cell in cells if cell["cell_type"] == "markdown"
    )
    code = "\n".join("".join(cell["source"]) for cell in cells if cell["cell_type"] == "code")

    assert "Phase 3 LangGraph HITL Workflow Demo" in markdown
    assert "demo/education artifact" in markdown
    assert "No LLM calls" in markdown
    assert "No OpenAI Agents SDK" in markdown
    assert "from agent_brain.orchestration.workflow import" in code
    assert "run_langgraph_workflow" in code
    assert "workflow_state_from_agent_state" in code
    assert "HITLDecisionOutcome.APPROVED" in code
    assert "FINALIZED_WITH_HITL" in code
    assert "FINALIZED_WITHOUT_HITL" in code
