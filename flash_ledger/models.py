"""Core data models for flashLedger."""

from __future__ import annotations
import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class Transaction(BaseModel):
    """Represents a single bank or credit card transaction."""

    id: str = Field(..., description="Unique transaction ID")
    date: datetime.date = Field(default_factory=datetime.date.today, description="Transaction post date")
    raw_description: str = Field(..., description="Raw bank feed string")
    clean_description: str = Field(default="", description="Preprocessed merchant string")
    amount: float = Field(..., description="Transaction amount (positive = debit/expense, negative = credit/refund)")
    currency: str = Field(default="USD", description="ISO 4217 currency code")
    account: str = Field(default="Default Account", description="Bank/Credit card account name")

    @model_validator(mode="after")
    def populate_clean_description(self) -> Transaction:
        if not self.clean_description:
            self.clean_description = self.raw_description
        return self


class AuditResult(BaseModel):
    """Audit analysis produced by Jev for a transaction."""

    transaction_id: str = Field(..., description="Associated transaction ID")
    gl_code: str = Field(..., description="Assigned General Ledger Chart of Accounts category")
    gl_confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence of GL code selection")
    is_tax_deductible: bool = Field(default=True, description="Whether transaction is a deductible business expense")
    deductible_probability: float = Field(default=1.0, ge=0.0, le=1.0, description="Calibrated Noul probability")
    expense_type: str = Field(default="OpEx", description="Expense classification: 'OpEx' or 'CapEx'")
    audit_risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Audit risk index (0=safe, 1=critical)")
    flags: list[str] = Field(default_factory=list, description="Audit flags (e.g. CAPEX_REVIEW_REQUIRED, HIGH_RISK)")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Classification latency in milliseconds")


class BatchSummary(BaseModel):
    """Aggregate summary statistics for a batch audit."""

    total_transactions: int = Field(default=0, ge=0)
    total_amount: float = Field(default=0.0)
    tax_deductible_amount: float = Field(default=0.0)
    flagged_count: int = Field(default=0, ge=0)
    capex_count: int = Field(default=0, ge=0)
    avg_latency_ms: float = Field(default=0.0, ge=0.0)
    throughput_tps: float = Field(default=0.0, ge=0.0)
