"""flashLedger: Autonomous Bank Feed & Card Auditor powered by TypeSafe Jev."""

__version__ = "0.1.0"
__author__ = "Divyaprakash"
__license__ = "Apache-2.0"

try:
    from flash_ledger.models import Transaction, AuditResult
    from flash_ledger.coa import ChartOfAccounts
    from flash_ledger.engine import JevDecisionEngine
    from flash_ledger.batch import BatchAuditor

    __all__ = [
        "__version__",
        "Transaction",
        "AuditResult",
        "ChartOfAccounts",
        "JevDecisionEngine",
        "BatchAuditor",
    ]
except ImportError:
    __all__ = ["__version__"]
