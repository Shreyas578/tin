import json
import pytest
from pathlib import Path
from uuid import UUID
from tin_lite.workflow_inputs import normalize_workflow_inputs, WorkflowInputError

PACKAGE_DIR = Path(__file__).parents[1] / "workflow_packages" / "growth.competitive_radar"

def test_package_structure():
    assert PACKAGE_DIR.exists(), "Package directory missing"
    
    manifest_path = PACKAGE_DIR / "workflow.json"
    assert manifest_path.exists(), "Manifest missing"
    
    prompt_path = PACKAGE_DIR / "PROMPT.md"
    assert prompt_path.exists(), "PROMPT.md missing"
    assert len(prompt_path.read_text().strip()) > 50, "PROMPT.md is empty or too short"
    
    skill_path = PACKAGE_DIR / "skills" / "competitive-radar" / "SKILL.md"
    assert skill_path.exists(), "Skill missing"
    assert len(skill_path.read_text().strip()) > 100, "SKILL.md is empty or too short"

def test_manifest_is_valid():
    manifest = json.loads((PACKAGE_DIR / "workflow.json").read_text())
    assert manifest["package_format"] == "tin-workflow-package-v1"
    definition = manifest["definition"]
    assert definition["key"] == "growth.competitive_radar"
    assert definition["executor"] == "codex.procedure"
    assert "input_schema" in definition
    assert "procedure" in definition

def test_valid_input_fixture():
    manifest = json.loads((PACKAGE_DIR / "workflow.json").read_text())
    schema = manifest["definition"]["input_schema"]
    
    valid_input = {
        "competitors": ["Competitor A", "Competitor B"],
        "keywords": ["reporting", "analytics", "dashboard"],
        "core_features": ["works without engineering involvement", "support responds in 2 hours"],
        "icp": "B2B SaaS founders and VP of Ops"
    }
    
    project_id = UUID("12345678-1234-5678-1234-567812345678")
    normalized = normalize_workflow_inputs(schema=schema, project_id=project_id, inputs=valid_input)
    
    # Assert defaults are correctly applied to the returned object
    assert "project_id" not in normalized, "Returned payload should not include internal project_id"
    assert normalized["build_signal_threshold"] == 5
    assert normalized["recency_days"] == 14
    assert normalized["known_weaknesses"] == ""
    assert normalized["historical_gaps"] == []

def test_historical_gaps_fixture():
    manifest = json.loads((PACKAGE_DIR / "workflow.json").read_text())
    schema = manifest["definition"]["input_schema"]
    
    valid_input = {
        "competitors": ["Competitor A"],
        "keywords": ["reporting"],
        "core_features": ["works without engineering involvement"],
        "icp": "B2B SaaS founders and VP of Ops",
        "historical_gaps": [
            "Notion Integration: 4",
            "Slack Alerts: 1"
        ]
    }
    
    project_id = UUID("12345678-1234-5678-1234-567812345678")
    normalized = normalize_workflow_inputs(schema=schema, project_id=project_id, inputs=valid_input)
    assert len(normalized["historical_gaps"]) == 2
    assert "Notion Integration: 4" in normalized["historical_gaps"]

def test_boundary_inputs_fixture():
    manifest = json.loads((PACKAGE_DIR / "workflow.json").read_text())
    schema = manifest["definition"]["input_schema"]
    
    # Test maximum thresholds and explicit assignments
    boundary_input = {
        "competitors": ["C1", "C2", "C3", "C4", "C5"], # Max items 5
        "keywords": ["k1"],
        "core_features": ["works without engineering involvement"],
        "icp": "B2B SaaS founders and VP of Ops",
        "known_weaknesses": "",
        "build_signal_threshold": 50, # Max
        "recency_days": 90 # Max
    }
    
    project_id = UUID("12345678-1234-5678-1234-567812345678")
    normalized = normalize_workflow_inputs(schema=schema, project_id=project_id, inputs=boundary_input)
    assert len(normalized["competitors"]) == 5
    assert normalized["build_signal_threshold"] == 50
    assert normalized["recency_days"] == 90
    
    # Test violation: maximum items
    bad_input_max = boundary_input.copy()
    bad_input_max["competitors"] = ["C1", "C2", "C3", "C4", "C5", "C6"]
    
    with pytest.raises(WorkflowInputError):
        normalize_workflow_inputs(schema=schema, project_id=project_id, inputs=bad_input_max)

    # Test minimum boundary explicitly
    min_boundary_input = boundary_input.copy()
    min_boundary_input["competitors"] = ["Only Competitor"] # Min items 1
    min_boundary_input["recency_days"] = 7
    min_normalized = normalize_workflow_inputs(schema=schema, project_id=project_id, inputs=min_boundary_input)
    assert len(min_normalized["competitors"]) == 1
    assert min_normalized["recency_days"] == 7
    
    # Test violation: pattern validation on historical_gaps
    bad_pattern_input = boundary_input.copy()
    bad_pattern_input["historical_gaps"] = ["Notion Integration - 4"] # Fails regex pattern ^.+: [0-9]+$
    with pytest.raises(WorkflowInputError):
        normalize_workflow_inputs(schema=schema, project_id=project_id, inputs=bad_pattern_input)

def test_invalid_input_fixture():
    manifest = json.loads((PACKAGE_DIR / "workflow.json").read_text())
    schema = manifest["definition"]["input_schema"]
    
    invalid_input = {
        # missing competitors, keywords, etc.
    }
    
    project_id = UUID("12345678-1234-5678-1234-567812345678")
    
    with pytest.raises(WorkflowInputError):
        normalize_workflow_inputs(schema=schema, project_id=project_id, inputs=invalid_input)
