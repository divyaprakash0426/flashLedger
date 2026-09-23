"""flashLedger: Autonomous Bank Feed & Card Auditor powered by TypeSafe Jev."""

__version__ = "0.1.0"
__author__ = "Divyaprakash"
__license__ = "Apache-2.0"

from flash_ledger.models import Transaction, AuditResult, BatchSummary
from flash_ledger.coa import ChartOfAccounts, AccountDefinition
from flash_ledger.engine import JevDecisionEngine
from flash_ledger.batch import BatchAuditor
from flash_ledger.preprocessor import clean_merchant_string, parse_amount, parse_statement_csv
from flash_ledger.mcp_server import create_mcp_server

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "Transaction",
    "AuditResult",
    "BatchSummary",
    "ChartOfAccounts",
    "AccountDefinition",
    "JevDecisionEngine",
    "BatchAuditor",
    "clean_merchant_string",
    "parse_amount",
    "parse_statement_csv",
    "create_mcp_server",
]
