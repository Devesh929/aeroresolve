"""
tests/agents/test_copilot_agent.py
Unit and integration test for AeroResolve Free-Form Conversational Copilot.
Validates grounded Q&A across Cortex Search, Cortex LLM Complete, and Semantic Views.
"""

import pytest
from backend.connection import get_snowflake_connection
from backend.agents.copilot_agent import AeroResolveCopilot

def test_copilot_technical_manual_query():
    """
    Tests Copilot answering a technical manual question about connector X42 and ghost faults.
    """
    conn = get_snowflake_connection()
    copilot = AeroResolveCopilot()
    
    query = "Why did replacing the avionics computer on ABR-017 fail to eliminate FAULT-21-204?"
    res = copilot.answer_query(conn, query)
    conn.close()

    assert res is not None
    assert len(res["answer"]) > 50
    assert "sources" in res
    assert len(res["sources"]) > 0
    # Must mention connector or harness or micro-fretting or temperature/vibration
    ans_lower = res["answer"].lower()
    assert any(w in ans_lower for w in ["connector", "harness", "fretting", "x42", "vibration", "temperature", "intermittent", "ground"])

def test_copilot_parts_inventory_query():
    """
    Tests Copilot answering a parts logistics and station availability question.
    """
    conn = get_snowflake_connection()
    copilot = AeroResolveCopilot()

    query = "Where can we find available stock for PART-X42-CONN to service an aircraft landing in Delhi?"
    res = copilot.answer_query(conn, query)
    conn.close()

    assert res is not None
    assert len(res["answer"]) > 50
    ans_lower = res["answer"].lower()
    # Must mention DEL stockout or BOM/HYD alternate hubs
    assert any(w in ans_lower for w in ["del", "bom", "mumbai", "delhi", "stock", "unit", "reposition"])
