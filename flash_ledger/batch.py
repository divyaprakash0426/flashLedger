"""High-throughput asynchronous batch auditor with concurrency controls."""

from __future__ import annotations
import asyncio
import time
from typing import Callable, Optional
from flash_ledger.engine import JevDecisionEngine
from flash_ledger.models import Transaction, AuditResult, BatchSummary


class BatchAuditor:
    """Orchestrates high-throughput parallel transaction audits with Jev."""

    def __init__(
        self,
        engine: JevDecisionEngine,
        max_concurrency: int = 50,
        capex_threshold: Optional[float] = None,
    ) -> None:
        """
        :param engine: JevDecisionEngine instance
        :param max_concurrency: Maximum simultaneous in-flight requests (default: 50)
        :param capex_threshold: Override for capitalization threshold (defaults to COA setting)
        """
        self.engine = engine
        self.max_concurrency = max_concurrency
        if capex_threshold is not None:
            self.engine.coa.capex_threshold = capex_threshold

    async def audit_batch(
        self,
        transactions: list[Transaction],
        progress_callback: Optional[Callable[[int, int, AuditResult], None]] = None,
    ) -> tuple[list[tuple[Transaction, AuditResult]], BatchSummary]:
        """
        Audit a batch of transactions concurrently with throttled concurrency.

        :param transactions: List of parsed Transaction objects
        :param progress_callback: Optional callable called after each transaction audit:
                                  callback(completed_count, total_count, latest_result)
        :return: (list of (Transaction, AuditResult) pairs, BatchSummary object)
        """
        total = len(transactions)
        if total == 0:
            return [], BatchSummary()

        semaphore = asyncio.Semaphore(self.max_concurrency)
        completed_count = 0
        total_latency_ms = 0.0
        start_time = time.perf_counter()

        lock = asyncio.Lock()

        async def _process_single(txn: Transaction) -> tuple[Transaction, AuditResult]:
            nonlocal completed_count, total_latency_ms
            async with semaphore:
                res = await self.engine.audit_transaction(txn)
                async with lock:
                    completed_count += 1
                    total_latency_ms += res.latency_ms
                    current_completed = completed_count

                if progress_callback:
                    try:
                        progress_callback(current_completed, total, res)
                    except Exception:
                        pass
                return (txn, res)

        tasks = [_process_single(txn) for txn in transactions]
        results = await asyncio.gather(*tasks)

        total_elapsed_seconds = max(time.perf_counter() - start_time, 0.0001)

        # Aggregate stats
        total_amount = sum(abs(txn.amount) for txn, _ in results)
        tax_deductible_amount = sum(
            abs(txn.amount) for txn, res in results if res.is_tax_deductible
        )
        flagged_count = sum(1 for _, res in results if len(res.flags) > 0)
        capex_count = sum(1 for _, res in results if res.expense_type == "CapEx")
        avg_latency = total_latency_ms / total if total > 0 else 0.0
        throughput = total / total_elapsed_seconds

        summary = BatchSummary(
            total_transactions=total,
            total_amount=round(total_amount, 2),
            tax_deductible_amount=round(tax_deductible_amount, 2),
            flagged_count=flagged_count,
            capex_count=capex_count,
            avg_latency_ms=round(avg_latency, 2),
            throughput_tps=round(throughput, 1),
        )

        return results, summary
