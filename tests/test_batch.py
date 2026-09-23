"""Unit tests for flash_ledger.batch."""

import pytest
import datetime
from flash_ledger.models import Transaction
from flash_ledger.engine import JevDecisionEngine
from flash_ledger.batch import BatchAuditor

@pytest.mark.asyncio
async def test_batch_auditor_execution():
    engine = JevDecisionEngine(mode="mock")
    auditor = BatchAuditor(engine=engine, max_concurrency=20)

    txns = [
        Transaction(
            id=f"t_{i}",
            date=datetime.date(2026, 3, 1),
            raw_description=f"TEST TRANSACTION {i}",
            clean_description="AWS Cloud Hosting" if i % 2 == 0 else "Starbucks Coffee",
            amount=50.0 + i,
        )
        for i in range(50)
    ]

    # Add a high-risk transaction
    txns.append(
        Transaction(
            id="t_risk",
            date=datetime.date(2026, 3, 2),
            raw_description="CASINO HOTEL LAS VEGAS",
            amount=850.0,
        )
    )

    # Add a CapEx transaction
    txns.append(
        Transaction(
            id="t_capex",
            date=datetime.date(2026, 3, 3),
            raw_description="APPLE STORE #104",
            amount=3299.0,
        )
    )

    progress_updates = []
    def on_progress(completed: int, total: int, res):
        progress_updates.append((completed, total))

    results, summary = await auditor.audit_batch(txns, progress_callback=on_progress)

    assert len(results) == 52
    assert summary.total_transactions == 52
    assert summary.flagged_count >= 2  # Casino + Apple Store
    assert summary.capex_count >= 1
    assert summary.throughput_tps > 50  # Must be fast
    assert len(progress_updates) == 52

@pytest.mark.asyncio
async def test_batch_empty():
    engine = JevDecisionEngine(mode="mock")
    auditor = BatchAuditor(engine=engine)
    results, summary = await auditor.audit_batch([])
    assert len(results) == 0
    assert summary.total_transactions == 0
    assert summary.throughput_tps == 0.0
