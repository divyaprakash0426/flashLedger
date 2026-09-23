"""Unit tests for flash_ledger.exporters."""

import csv
import json
import datetime
from pathlib import Path
from flash_ledger.models import Transaction, AuditResult
from flash_ledger.exporters import (
    export_qbo_csv,
    export_xero_csv,
    export_freshbooks_csv,
    export_json,
    export_audit_csv,
)

def make_sample_data():
    txn1 = Transaction(
        id="t_1",
        date=datetime.date(2026, 3, 15),
        raw_description="GITHUB*SPONSOR 877-448",
        clean_description="GitHub Sponsor",
        amount=100.0,
        currency="USD",
        account="Chase Sapphire",
    )
    res1 = AuditResult(
        transaction_id="t_1",
        gl_code="Software/SaaS",
        gl_confidence=0.98,
        is_tax_deductible=True,
        deductible_probability=0.97,
        expense_type="OpEx",
        audit_risk_score=0.04,
        flags=[],
        latency_ms=3.2,
    )

    txn2 = Transaction(
        id="t_2",
        date=datetime.date(2026, 3, 16),
        raw_description="APPLE STORE #104",
        clean_description="Apple Store",
        amount=3299.0,
        currency="USD",
        account="Brex Card",
    )
    res2 = AuditResult(
        transaction_id="t_2",
        gl_code="Hardware & Equipment",
        gl_confidence=0.95,
        is_tax_deductible=True,
        deductible_probability=0.92,
        expense_type="CapEx",
        audit_risk_score=0.12,
        flags=["CAPEX_REVIEW_REQUIRED"],
        latency_ms=3.5,
    )

    return [(txn1, res1), (txn2, res2)]

def test_export_qbo_csv(tmp_path):
    data = make_sample_data()
    out = tmp_path / "qbo.csv"
    export_qbo_csv(data, out)

    with open(out, newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert "Date" in headers
        assert "Category" in headers
        assert "Payee" in headers
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0][headers.index("Category")] == "Software/SaaS"
        assert rows[1][headers.index("ExpenseType")] == "CapEx"

def test_export_xero_csv(tmp_path):
    data = make_sample_data()
    out = tmp_path / "xero.csv"
    export_xero_csv(data, out)

    with open(out, newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert "*ContactName" in headers
        assert "*Total" in headers
        assert "*Description" in headers
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0][headers.index("*ContactName")] == "GitHub Sponsor"

def test_export_freshbooks_csv(tmp_path):
    data = make_sample_data()
    out = tmp_path / "freshbooks.csv"
    export_freshbooks_csv(data, out)

    with open(out, newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert "Merchant" in headers
        assert "Tax Deductible" in headers
        rows = list(reader)
        assert len(rows) == 2

def test_export_json(tmp_path):
    data = make_sample_data()
    out = tmp_path / "audit.json"
    export_json(data, out)

    with open(out) as f:
        payload = json.load(f)
    assert len(payload) == 2
    assert payload[0]["audit"]["gl_code"] == "Software/SaaS"
    assert payload[1]["audit"]["flags"] == ["CAPEX_REVIEW_REQUIRED"]
