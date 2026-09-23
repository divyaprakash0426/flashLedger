"""End-to-end integration tests for flashLedger."""

import pytest
from pathlib import Path
from flash_ledger.coa import ChartOfAccounts
from flash_ledger.engine import JevDecisionEngine
from flash_ledger.batch import BatchAuditor
from flash_ledger.preprocessor import parse_statement_csv
from flash_ledger.exporters import export_qbo_csv, export_xero_csv, export_json

@pytest.mark.asyncio
async def test_full_pipeline_with_benchmark_sample(tmp_path):
    # 1. Load Chart of Accounts
    coa = ChartOfAccounts.load_default()
    assert len(coa.accounts) >= 10

    # 2. Parse sample dataset
    sample_csv = Path("data") / "benchmark_sample_1000.csv"
    assert sample_csv.exists()
    transactions = parse_statement_csv(sample_csv)
    assert len(transactions) == 1000

    # 3. Audit batch with mock engine (zero-cost offline)
    engine = JevDecisionEngine(coa=coa, mode="mock")
    auditor = BatchAuditor(engine=engine, max_concurrency=50)
    results, summary = await auditor.audit_batch(transactions[:150])

    assert len(results) == 150
    assert summary.total_transactions == 150
    assert summary.total_amount > 0
    assert summary.tax_deductible_amount > 0
    assert summary.throughput_tps > 100

    # 4. Verify all audited records have valid GL codes strictly in COA
    valid_names = set(coa.account_names)
    for txn, res in results:
        assert res.gl_code in valid_names
        assert 0.0 <= res.deductible_probability <= 1.0
        assert res.expense_type in {"OpEx", "CapEx"}
        assert 0.0 <= res.audit_risk_score <= 1.0

    # 5. Export to QBO, Xero, and JSON
    qbo_out = tmp_path / "e2e_qbo.csv"
    xero_out = tmp_path / "e2e_xero.csv"
    json_out = tmp_path / "e2e_audit.json"

    export_qbo_csv(results, qbo_out)
    export_xero_csv(results, xero_out)
    export_json(results, json_out)

    assert qbo_out.exists() and qbo_out.stat().st_size > 100
    assert xero_out.exists() and xero_out.stat().st_size > 100
    assert json_out.exists() and json_out.stat().st_size > 100
