"""Chart of Accounts (COA) Loader and Hierarchy."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field


class AccountDefinition(BaseModel):
    """Definition of a single GL account code."""

    code: str = Field(..., description="Account numeric or alphanumeric code (e.g. 6010)")
    name: str = Field(..., description="Account human-readable label (e.g. Software/SaaS)")
    description: str = Field(..., description="Detailed description and merchant examples")
    tax_deductible_default: bool = Field(default=True, description="Whether usually tax deductible")
    category: str = Field(default="Operating Expenses", description="Parent balance sheet / P&L category")


class ChartOfAccounts(BaseModel):
    """Collection of GL accounts with tax thresholds."""

    name: str = Field(default="Standard COA")
    capex_threshold: float = Field(default=2500.0, description="IRS De Minimis Safe Harbor threshold")
    accounts: list[AccountDefinition] = Field(default_factory=list)

    @classmethod
    def load_default(cls) -> ChartOfAccounts:
        """Load default built-in GAAP/IRS Chart of Accounts."""
        pkg_dir = Path(__file__).parent
        default_path = pkg_dir / "data" / "default_coa.json"
        if not default_path.exists():
            raise FileNotFoundError(f"Default COA data not found at {default_path}")
        return cls.load(default_path)

    @classmethod
    def load(cls, path_or_dict: str | Path | dict[str, Any]) -> ChartOfAccounts:
        """Load COA from JSON file path or dictionary."""
        if isinstance(path_or_dict, (str, Path)):
            p = Path(path_or_dict)
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = path_or_dict
        return cls.model_validate(data)

    @property
    def account_names(self) -> list[str]:
        """List of all account names."""
        return [acc.name for acc in self.accounts]

    def get_account(self, name: str) -> Optional[AccountDefinition]:
        """Find account by name (case-insensitive)."""
        name_lower = name.strip().lower()
        for acc in self.accounts:
            if acc.name.lower() == name_lower or acc.code.lower() == name_lower:
                return acc
        return None

    def get_criteria_mapping(self) -> dict[str, str]:
        """Returns dict suitable for Jev Choice criteria: {AccountName: Description}."""
        return {acc.name: acc.description for acc in self.accounts}
