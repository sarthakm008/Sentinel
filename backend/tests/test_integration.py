"""Integration tests for Sentinel API endpoints."""

import pytest

# Use client fixture from conftest


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_risk_score_endpoint(client):
    """Test scoring a refund event."""
    response = client.post("/api/risk/score", json={"refund_id": "REF_0000001"})
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "risk_band" in data
    assert "recommended_action" in data
    assert "evidence" in data
    assert "case_id" in data
    assert 0 <= data["risk_score"] <= 1
    assert data["risk_band"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert data["recommended_action"] in ["approve", "verify", "review", "hold"]


def test_risk_score_invalid_refund(client):
    """Test scoring a non-existent refund."""
    response = client.post("/api/risk/score", json={"refund_id": "REF_INVALID"})
    assert response.status_code == 404


def test_cases_list_endpoint(client):
    """Test listing cases."""
    # First create a case
    client.post("/api/risk/score", json={"refund_id": "REF_0000001"})
    
    response = client.get("/api/cases")
    assert response.status_code == 200
    data = response.json()
    assert "cases" in data
    assert "total" in data
    assert data["total"] >= 1


def test_cases_list_with_filters(client):
    """Test listing cases with filters."""
    response = client.get("/api/cases?band=LOW")
    assert response.status_code == 200
    data = response.json()
    for case in data["cases"]:
        assert case["risk_band"] == "LOW"


def test_case_detail_endpoint(client):
    """Test getting a specific case."""
    # Create a case first
    score_response = client.post("/api/risk/score", json={"refund_id": "REF_0000001"})
    case_id = score_response.json()["case_id"]
    
    response = client.get(f"/api/cases/{case_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == case_id
    assert "evidence" in data


def test_case_decision_endpoint(client):
    """Test recording a decision on a case."""
    # Create a case first
    score_response = client.post("/api/risk/score", json={"refund_id": "REF_0000001"})
    case_id = score_response.json()["case_id"]
    
    # Record decision
    response = client.post(f"/api/cases/{case_id}/decision", json={"decision": "approve"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["decision"] == "approve"
    assert data["case_id"] == case_id
    
    # Verify case status updated
    case_response = client.get(f"/api/cases/{case_id}")
    assert case_response.json()["status"] == "decided"
    assert case_response.json()["decision"] == "approve"


def test_case_decision_invalid(client):
    """Test recording an invalid decision."""
    score_response = client.post("/api/risk/score", json={"refund_id": "REF_0000001"})
    case_id = score_response.json()["case_id"]
    
    response = client.post(f"/api/cases/{case_id}/decision", json={"decision": "invalid"})
    assert response.status_code == 400


def test_evaluation_endpoint(client):
    """Test evaluation metrics endpoint."""
    response = client.get("/api/evaluation")
    assert response.status_code == 200
    data = response.json()
    assert "production_candidate" in data
    assert "ablation" in data
    assert "type_f" in data
    assert "future_period" in data
    assert "phase5_experiment" in data
    assert "thresholds" in data
    
    # Check production candidate
    prod = data["production_candidate"]
    assert prod["model_name"] == "Full Sentinel (Production)"
    assert 0 <= prod["pr_auc"] <= 1
    
    # Check phase 5 experiment
    phase5 = data["phase5_experiment"]
    assert phase5["decision"] == "STOP"


def test_demo_scenario_endpoint(client):
    """Test demo scenario configuration."""
    response = client.get("/api/demo/scenario")
    assert response.status_code == 200
    data = response.json()
    assert "refund_ids" in data
    assert len(data["refund_ids"]) == 5


def test_demo_reset_endpoint(client):
    """Test demo reset."""
    # Create some cases first
    client.post("/api/risk/score", json={"refund_id": "REF_0000001"})
    
    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify cases cleared
    cases_response = client.get("/api/cases")
    assert cases_response.json()["total"] == 0


def test_demo_run_endpoint(client):
    """Test running the demo scenario."""
    # Reset first
    client.post("/api/demo/reset")
    
    response = client.post("/api/demo/run")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Demo completed:" in data["message"]
    assert len(data["cases"]) == 5
    
    # Verify cases created
    cases_response = client.get("/api/cases")
    assert cases_response.json()["total"] == 5
    
    # Check risk bands vary
    bands = set(c["risk_band"] for c in data["cases"])
    assert len(bands) > 1  # Should have variety