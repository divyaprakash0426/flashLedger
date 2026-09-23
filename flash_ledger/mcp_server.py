"""Model Context Protocol (MCP) server for flashLedger."""

from __future__ import annotations
import asyncio
import datetime
import uuid
from typing import Any, Optional
from mcp.server.mcpserver import MCPServer
from flash_ledger.coa import ChartOfAccounts
from flash_ledger.engine import JevDecisionEngine
from flash_ledger.batch import BatchAuditor
from flash_ledger.models import Transaction
from flash_ledger.preprocessor import clean_merchant_string


def create_mcp_server(
    engine: Optional[JevDecisionEngine] = None,
    coa: Optional[ChartOfAccounts] = None,
) -> MCPServer:
    """Create and configure the flashLedger MCP server."""
    server = MCPServer(
        name="flash-ledger",
        instructions="Autonomous financial bank feed categorizer and tax auditor powered by TypeSafe Jev.",
    )

    active_coa = coa or ChartOfAccounts.load_default()
    active_engine = engine or JevDecisionEngine(coa=active_coa, mode="auto")
    batch_auditor = BatchAuditor(engine=active_engine)

    @server.tool(name="classify_transaction", description="Audit and classify a single bank or card transaction into Chart of Accounts.")
    async def classify_transaction(
        description: str,
        amount: float,
        currency: str = "USD",
        account: str = "Corporate Account",
    ) -> dict[str, Any]:
        """
        Audit a single transaction.

        :param description: Raw or clean merchant transaction description (e.g. 'SQ *BLUE BOTTLE SOMA')
        :param amount: Transaction amount (positive for expense/debit, negative for refund/credit)
        :param currency: Currency code (default 'USD')
        :param account: Account name or card label
        :return: Structured audit result including GL code, tax deductibility, CapEx/OpEx, and audit risk score
        """
        clean_desc = clean_merchant_string(description)
        txn = Transaction(
            id=f"mcp_{uuid.uuid4().hex[:8]}",
            date=datetime.date.today(),
            raw_description=description,
            clean_description=clean_desc,
            amount=amount,
            currency=currency,
            account=account,
        )
        res = await active_engine.audit_transaction(txn)
        return {
            "transaction": txn.model_dump(mode="json"),
            "audit": res.model_dump(mode="json"),
        }

    @server.tool(name="audit_expense_batch", description="Audit a batch of financial transactions at high throughput with IRS/GAAP rules.")
    async def audit_expense_batch(
        transactions: list[dict[str, Any]],
        capex_threshold: float = 2500.0,
    ) -> dict[str, Any]:
        """
        Audit multiple transactions in parallel.

        :param transactions: List of transaction objects with 'description', 'amount', optional 'date', 'currency'
        :param capex_threshold: De minimis capitalization threshold (default: $2,500)
        :return: Audit results for all transactions and aggregate batch summary metrics
        """
        parsed_txns: list[Transaction] = []
        for idx, item in enumerate(transactions):
            raw_desc = str(item.get("description") or item.get("raw_description") or "")
            clean_desc = clean_merchant_string(raw_desc)
            amount = float(item.get("amount", 0.0))
            curr = str(item.get("currency", "USD"))
            acc = str(item.get("account", "Batch Account"))
            parsed_txns.append(
                Transaction(
                    id=f"batch_{idx:04d}_{uuid.uuid4().hex[:6]}",
                    date=datetime.date.today(),
                    raw_description=raw_desc,
                    clean_description=clean_desc,
                    amount=amount,
                    currency=curr,
                    account=acc,
                )
            )

        auditor = BatchAuditor(engine=active_engine, capex_threshold=capex_threshold)
        results, summary = await auditor.audit_batch(parsed_txns)

        return {
            "summary": summary.model_dump(mode="json"),
            "items": [
                {
                    "transaction": txn.model_dump(mode="json"),
                    "audit": res.model_dump(mode="json"),
                }
                for txn, res in results
            ],
        }

    @server.tool(name="get_chart_of_accounts", description="Retrieve the active General Ledger Chart of Accounts (COA) hierarchy.")
    async def get_chart_of_accounts() -> dict[str, Any]:
        """Retrieve all supported GL categories, tax rules, and IRS thresholds."""
        return {
            "name": active_coa.name,
            "capex_threshold": active_coa.capex_threshold,
            "accounts": [acc.model_dump(mode="json") for acc in active_coa.accounts],
        }

    return server


def main() -> None:
    """Run the MCP server over standard I/O."""
    server = create_mcp_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
