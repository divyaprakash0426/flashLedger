"""Unit tests for flash_ledger.engine."""

import pytest
import datetime
from flash_ledger.models import Transaction, AuditResult
from flash_ledger.coa import ChartOfAccounts
from flash_ledger.engine import JevDecisionEngine

@pytest.mark.asyncio
async def test_mock_engine_classifications():
    engine = JevDecisionEngine(mode="mock")

    # SaaS expense
    txn_saas = Transaction(
        id="txn_1",
        date=datetime.date(2026, 3, 15),
        raw_description="GITHUB*SPONSOR 877-448",
        clean_description="GitHub Sponsor",
        amount=100.0,
    )
    res_saas = await engine.audit_transaction(txn_saas)
    assert res_saas.gl_code == "Software/SaaS"
    assert res_saas.is_tax_deductible is True
    assert res_saas.deductible_probability >= 0.90
    assert res_saas.expense_type == "OpEx"
    assert res_saas.audit_risk_score < 0.20

    # Meals expense
    txn_meal = Transaction(
        id="txn_2",
        date=datetime.date(2026, 3, 15),
        raw_description="SQ *BLUE BOTTLE SOMA",
        clean_description="Blue Bottle Coffee",
        amount=14.20,
    )
    res_meal = await engine.audit_transaction(txn_meal)
    assert res_meal.gl_code == "Meals & Entertainment"
    assert res_meal.is_tax_deductible is True
    assert res_meal.expense_type == "OpEx"

    # High-Risk Personal / Non-Deductible expense (Casino)
    txn_casino = Transaction(
        id="txn_3",
        date=datetime.date(2026, 3, 15),
        raw_description="CASINO HOTEL LAS VEGAS NV",
        clean_description="Casino Hotel Las Vegas",
        amount=850.0,
    )
    res_casino = await engine.audit_transaction(txn_casino)
    assert res_casino.gl_code == "Personal / Non-Deductible"
    assert res_casino.is_tax_deductible is False
    assert res_casino.audit_risk_score >= 0.80
    assert any("RISK" in f or "PERSONAL" in f for f in res_casino.flags)

    # CapEx purchase exceeding $2,500 threshold
    txn_capex = Transaction(
        id="txn_4",
        date=datetime.date(2026, 3, 15),
        raw_description="APPLE STORE #104",
        clean_description="Apple Store",
        amount=3299.00,
    )
    res_capex = await engine.audit_transaction(txn_capex)
    assert res_capex.gl_code == "Hardware & Equipment"
    assert res_capex.expense_type == "CapEx"
    assert "CAPEX_REVIEW_REQUIRED" in res_capex.flags

@pytest.mark.asyncio
async def test_engine_question_building():
    engine = JevDecisionEngine(mode="mock")
    questions = engine._build_jev_questions()
    assert "gl_code" in questions
    assert "tax_deductible" in questions
    assert "expense_type" in questions
    assert "audit_risk" in questions
