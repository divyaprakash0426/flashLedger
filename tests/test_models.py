"""Unit tests for flash_ledger.models."""

import datetime
from flash_ledger.models import Transaction, AuditResult, BatchSummary

def test_transaction_creation():
    txn = Transaction(
        id="txn_001",
        date=datetime.date(2026, 3, 15),
        raw_description="SQ *BLUE BOTTLE SOMA",
        clean_description="Blue Bottle Coffee",
        amount=14.20,
        currency="USD",
        account="Chase Sapphire",
    )
    assert txn.id == "txn_001"
    assert txn.amount == 14.20
    assert txn.clean_description == "Blue Bottle Coffee"
    assert txn.currency == "USD"

def test_transaction_default_clean_description():
    txn = Transaction(
        id="txn_002",
        date=datetime.date(2026, 3, 15),
        raw_description="AWS CLOUD SERVICES",
        amount=120.50,
    )
    assert txn.clean_description == "AWS CLOUD SERVICES"
    assert txn.currency == "USD"

def test_audit_result_model():
    result = AuditResult(
        transaction_id="txn_001",
        gl_code="Meals & Entertainment",
        gl_confidence=0.98,
        is_tax_deductible=True,
        deductible_probability=0.96,
        expense_type="OpEx",
        audit_risk_score=0.08,
        flags=["DE_MINIMIS_MEAL"],
        latency_ms=3.4,
    )
    assert result.gl_code == "Meals & Entertainment"
    assert result.is_tax_deductible is True
    assert result.audit_risk_score == 0.08
    assert "DE_MINIMIS_MEAL" in result.flags
    assert result.latency_ms == 3.4

def test_batch_summary():
    summary = BatchSummary(
        total_transactions=100,
        total_amount=15420.50,
        tax_deductible_amount=14200.00,
        flagged_count=3,
        capex_count=2,
        avg_latency_ms=3.2,
        throughput_tps=312.5,
    )
    assert summary.total_transactions == 100
    assert summary.flagged_count == 3
    assert summary.throughput_tps > 300
