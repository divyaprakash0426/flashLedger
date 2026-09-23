"""Accounting platform exporters for QuickBooks Online, Xero, FreshBooks, CSV, and JSON."""

from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Sequence
from flash_ledger.models import Transaction, AuditResult


def export_qbo_csv(
    items: Sequence[tuple[Transaction, AuditResult]],
    output_path: str | Path,
) -> Path:
    """Export transactions to standard QuickBooks Online (QBO) batch format."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "Date",
        "Description",
        "Amount",
        "Payee",
        "Category",
        "Account",
        "TaxDeductible",
        "ExpenseType",
        "AuditFlags",
    ]

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for txn, res in items:
            writer.writerow([
                txn.date.isoformat(),
                txn.raw_description,
                f"{txn.amount:.2f}",
                txn.clean_description,
                res.gl_code,
                txn.account,
                "Yes" if res.is_tax_deductible else "No",
                res.expense_type,
                "; ".join(res.flags),
            ])
    return out


def export_xero_csv(
    items: Sequence[tuple[Transaction, AuditResult]],
    output_path: str | Path,
) -> Path:
    """Export transactions to standard Xero Bill/Spend format."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "*ContactName",
        "*InvoiceNumber",
        "*InvoiceDate",
        "*DueDate",
        "*Total",
        "*Description",
        "*AccountCode",
        "*TaxType",
    ]

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for txn, res in items:
            tax_type = "Tax Exempt (0%)" if not res.is_tax_deductible else "Standard Rate (0%)"
            writer.writerow([
                txn.clean_description,
                txn.id,
                txn.date.isoformat(),
                txn.date.isoformat(),
                f"{txn.amount:.2f}",
                txn.raw_description,
                res.gl_code,
                tax_type,
            ])
    return out


def export_freshbooks_csv(
    items: Sequence[tuple[Transaction, AuditResult]],
    output_path: str | Path,
) -> Path:
    """Export transactions to FreshBooks expense import format."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "Date",
        "Merchant",
        "Category",
        "Amount",
        "Currency",
        "Tax Deductible",
        "Notes",
    ]

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for txn, res in items:
            notes = f"Flags: {'; '.join(res.flags)}" if res.flags else ""
            writer.writerow([
                txn.date.isoformat(),
                txn.clean_description,
                res.gl_code,
                f"{txn.amount:.2f}",
                txn.currency,
                "true" if res.is_tax_deductible else "false",
                notes,
            ])
    return out


def export_audit_csv(
    items: Sequence[tuple[Transaction, AuditResult]],
    output_path: str | Path,
) -> Path:
    """Export comprehensive audit results with all model signals and metadata."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "TransactionID",
        "Date",
        "RawDescription",
        "CleanMerchant",
        "Amount",
        "Currency",
        "Account",
        "GLCode",
        "GLConfidence",
        "TaxDeductible",
        "DeductibleProbability",
        "ExpenseType",
        "AuditRiskScore",
        "Flags",
        "LatencyMs",
    ]

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for txn, res in items:
            writer.writerow([
                txn.id,
                txn.date.isoformat(),
                txn.raw_description,
                txn.clean_description,
                f"{txn.amount:.2f}",
                txn.currency,
                txn.account,
                res.gl_code,
                f"{res.gl_confidence:.2f}",
                "true" if res.is_tax_deductible else "false",
                f"{res.deductible_probability:.2f}",
                res.expense_type,
                f"{res.audit_risk_score:.2f}",
                ";".join(res.flags),
                f"{res.latency_ms:.1f}",
            ])
    return out


def export_json(
    items: Sequence[tuple[Transaction, AuditResult]],
    output_path: str | Path,
) -> Path:
    """Export comprehensive JSON array of audit records."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    records = [
        {
            "transaction": txn.model_dump(mode="json"),
            "audit": res.model_dump(mode="json"),
        }
        for txn, res in items
    ]

    with open(out, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    return out
