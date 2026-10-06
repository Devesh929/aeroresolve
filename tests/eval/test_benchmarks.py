"""
tests/eval/test_benchmarks.py
Pytest integration test for AeroResolve Agent Evaluation Benchmark Suite.
Runs all 32 benchmark scenarios and validates pass rates, accuracy, and safety gates.
"""

import pytest
from tests.eval.run_agent_benchmarks import run_benchmark_suite

def test_full_benchmark_suite():
    """
    Executes the comprehensive 32-scenario agent benchmark suite,
    verifying 100% pass rate, zero false alarms, and safety compliance.
    """
    success = run_benchmark_suite()
    assert success is True, "AeroResolve Agent Benchmark suite did not achieve 100% pass rate"
