"""Unit tests for flash_ledger.mcp_server."""

import pytest
from flash_ledger.mcp_server import create_mcp_server

@pytest.mark.asyncio
async def test_mcp_server_tools_registered():
    server = create_mcp_server()
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    assert "classify_transaction" in tool_names
    assert "audit_expense_batch" in tool_names
    assert "get_chart_of_accounts" in tool_names

@pytest.mark.asyncio
async def test_mcp_classify_transaction_tool():
    server = create_mcp_server()
    res = await server.call_tool(
        "classify_transaction",
        {"description": "SQ *BLUE BOTTLE SOMA", "amount": 14.20, "currency": "USD"}
    )
    assert res is not None
    # Verify response structure
    text = str(res)
    assert "Meals & Entertainment" in text or "Operating Expenses" in text

@pytest.mark.asyncio
async def test_mcp_get_chart_of_accounts_tool():
    server = create_mcp_server()
    res = await server.call_tool("get_chart_of_accounts", {})
    assert res is not None
    text = str(res)
    assert "Software/SaaS" in text
