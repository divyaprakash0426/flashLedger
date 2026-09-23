# Specification: flashLedger - Autonomous Bank Feed & Card Auditor

**Date:** 2026-09-24  
**License:** Apache 2.0  
**Repository:** `divyaprakash0426/flashLedger`  
**Author:** Divyaprakash (`divyaprakash0426`)  

---

## 1. Problem Statement & Motivation

Every business owner, accountant, and finance department dreads monthly reconciliation. Raw bank and corporate card feeds are full of cryptic abbreviations (`SQ *BLUE BOTTLE SOMA`, `AMZN Mktp US*284J1`, `GITHUB*SPONSOR 877-448`, `UBER *EATS PENDING SAN FRANCISCO`). Standard regex and keyword rules fail whenever a merchant name slightly alters or a trailing POS number changes.

Conversely, frontier Large Language Models (GPT-4o, Claude 3.5 Sonnet) are:
1. **Slow:** 15–35 seconds per batch of 50–100 transactions due to sequential autoregressive token generation.
2. **Expensive:** ~$15–$35 per 10,000 transactions.
3. **Unreliable:** Hallucinating invalid GL account codes, inconsistent casing, and failing JSON parse schemas.

### The Solution: `flashLedger` with TypeSafe Jev
TypeSafe Jev is a calibrated "System One" decision model specifically engineered for fast, structured, probabilistic decisions. It evaluates transactions across four parallel dimensions in a single sub-100ms round-trip:
1. **GL Code (Choice):** Pick from strict Chart of Accounts (COA) categories.
2. **Tax Deductibility (Noul):** High-precision calibrated boolean probability (e.g. 0.96 for business software, 0.05 for personal dining).
3. **Expenditure Type (Choice):** OpEx vs CapEx categorization (with IRS de minimis safe harbor threshold evaluation).
4. **Audit Flag / Risk Index (Score):** Calibrated risk score (0.00 to 1.00) flagging anomalies, compliance risks, or duplicate billings.

---

## 2. System Architecture

```
                                  [ Raw Bank / Credit Card CSV / Parquet ]
                                                     │
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │   flashLedger Pre-Processor  │
                                      │  - Strip terminal POS noise  │
                                      │  - Parse amounts & ISO date  │
                                      │  - Detect card / bank format │
                                      └──────────────┬───────────────┘
                                                     │
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │   Chart of Accounts (COA)    │
                                      │   Default GAAP/IRS or Custom │
                                      └──────────────┬───────────────┘
                                                     │
                                                     ▼
                                  ┌─────────────────────────────────────┐
                                  │    Async Jev Decision Engine        │
                                  │   - Throttled Worker Pool           │
                                  │   - TypeSafe SDK (Choice/Noul/Score)│
                                  │   - Offline Mock Engine Fallback    │
                                  └──────────────────┬──────────────────┘
                                                     │
                         ┌───────────────────────────┴───────────────────────────┐
                         ▼                                                       ▼
            ┌────────────────────────┐                             ┌────────────────────────┐
            │   Auditor & Analytics  │                             │   Exporters & MCP      │
            │  - CapEx Rule Engine   │                             │  - QuickBooks (QBO)    │
            │  - Risk Anomaly Flags  │                             │  - Xero / FreshBooks   │
            │  - Deductibility Stats │                             │  - FastMCP Server      │
            └────────────┬───────────┘                             └────────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────┐
        │  CLI & Viral Visual Waterfall    │
        │  - Split-screen GPT-4o vs Jev    │
        │  - Interactive Rich Terminal UI  │
        │  - Benchmark Report Generator    │
        └──────────────────────────────────┘
```

---

## 3. Core Component Design

### 3.1. Models (`flash_ledger/models.py`)
- `Transaction`:
  - `id`: Unique transaction identifier.
  - `date`: `datetime.date`.
  - `raw_description`: The raw bank string (e.g. `SQ *BLUE BOTTLE SOMA`).
  - `clean_description`: Preprocessed merchant string (e.g. `Blue Bottle Coffee`).
  - `amount`: Signed float (positive for expense, negative for refund/credit).
  - `currency`: ISO currency code (default: `USD`).
  - `account`: Account label (e.g. `Chase Sapphire`, `Brex Corporate Card`).
- `AuditResult`:
  - `gl_code`: Validated GL Account name from COA.
  - `gl_confidence`: Model confidence for chosen GL code (0.0 to 1.0).
  - `is_tax_deductible`: Boolean based on Noul threshold (default >= 0.50).
  - `deductible_probability`: Calibrated probability (0.0 to 1.0).
  - `expense_type`: `"OpEx"` or `"CapEx"`.
  - `audit_risk_score`: Calibrated risk index (0.0 to 1.0).
  - `flags`: List of strings (e.g. `["HIGH_RISK_MERCHANT", "CAPEX_REVIEW_REQUIRED"]`).
  - `latency_ms`: Processing time in milliseconds.
- `ChartOfAccounts`:
  - Container for GL categories, parent hierarchies, IRS tax schedules, and CapEx thresholds (default: $2,500 de minimis safe harbor).

### 3.2. Preprocessor (`flash_ledger/preprocessor.py`)
- Cleans common merchant prefixes: `SQ *`, `TST*`, `PAYPAL *`, `AMZN Mktp`, `STRIPE *`, `GITHUB*`, `DRI*`, `SP *`.
- Strips trailing store IDs, terminal codes, phone numbers, state/city trailing tags (e.g., `#104`, `*284J1`, `877-448-0000`, `SAN FRANCISCO CA`).
- Normalizes amounts (handles parenthesized negatives `(12.50)`, commas `1,299.00`, currencies `$`, `£`, `€`).
- Detects format schemas: Chase, Amex, Brex, Mercury, Stripe, UK Gov Spending CSV.

### 3.3. Jev Decision Engine (`flash_ledger/engine.py`)
- High-level interface `JevDecisionEngine`.
- Configurable:
  - `api_key`: `TYPESAFE_API_KEY` or fallback to mock mode.
  - `mode`: `"api"` (real TypeSafe API) or `"mock"` (high-fidelity local deterministic engine for testing, CI, and zero-cost local benchmarks).
- Multi-attribute Jev question mapping:
  - `Choice`: Criteria dictionary populated from `ChartOfAccounts.accounts`.
  - `Noul`: Instructions: "Is this transaction a tax-deductible business expense under IRS / GAAP rules?"
  - `Choice`: `{"OpEx": "Operating Expense", "CapEx": "Capital Expenditure exceeding asset threshold"}`
  - `Score`: Criteria: `["Very Low Risk", "Low Risk", "Medium Risk", "High Risk", "Critical Risk"]`.

### 3.4. High-Throughput Batch Processor (`flash_ledger/batch.py`)
- Asynchronous batch execution with configurable concurrency (default: 50 concurrent requests).
- Rate-limiting protection with exponential backoff.
- Progress reporting hook for rich terminal animations.

### 3.5. Exporters (`flash_ledger/exporters.py`)
- QuickBooks Online (QBO) standard format: `Date,Description,Amount,Payee,Category,Account,TaxDeductible`.
- Xero format: `*ContactName,*InvoiceNumber,*InvoiceDate,*DueDate,*Total,*Description,*AccountCode,*TaxType`.
- FreshBooks format.
- Comprehensive CSV / JSON format with full audit metadata.

### 3.6. MCP Server (`flash_ledger/mcp_server.py`)
- Built using `FastMCP` from the official MCP Python SDK.
- Tools:
  - `classify_transaction(description: str, amount: float, currency: str = "USD") -> dict`
  - `audit_expense_batch(transactions: list[dict], capex_threshold: float = 2500.0) -> list[dict]`
  - `get_chart_of_accounts() -> dict`
  - `export_audit_results(results: list[dict], format: str = "qbo") -> str`

### 3.7. Viral Split-Screen Demo (`flash_ledger/demo.py`)
- Visual terminal animation demonstrating:
  - Split screen: Left side shows slow frontier LLM (GPT-4o) simulating 50 txns in ~28s ($0.45).
  - Right side shows `flashLedger` (Jev) cascading 1,000 transactions in ~3.5s ($0.01).
  - Highlighted anomalies:
    - `CASINO HOTEL LAS VEGAS - $850.00` ➔ `Audit Score: 0.94 (FLAGGED)`
    - `APPLE STORE #104 - $3,299.00` ➔ `CapEx Review Required (> $2,500 threshold)`
- Generates markdown / ASCII benchmark table ready for LinkedIn.

### 3.8. Dataset Tooling (`flash_ledger/datasets/`)
- `scripts/download_datasets.py`:
  - UK Government Corporate Spending data downloader (fetching authentic public £25k+ spend CSVs).
  - Hugging Face downloader for `mitulshah/transaction-categorization` (with clear instructions and token support).
  - High-fidelity synthetic realistic dataset generator (1,000 to 10,000 transactions across USD, GBP, EUR with authentic messy bank strings).

---

## 4. Testing Strategy (100% Offline & Zero-Cost)

- **Local Mocking:** All tests run locally using `pytest` without connecting to external paid APIs.
- **Unit Tests:**
  - `test_preprocessor.py`: Regex cleansing, merchant extraction, amount parsing.
  - `test_coa.py`: Default COA, custom YAML/JSON loading, schema validation.
  - `test_engine.py`: Jev client request formatting, response parsing, mock engine behavior.
  - `test_batch.py`: Async batch throughput, concurrency control, error handling.
  - `test_exporters.py`: QBO, Xero, FreshBooks CSV generation.
  - `test_mcp.py`: MCP tool invocation and responses.
  - `test_cli.py`: Typer CLI command execution (`classify`, `audit`, `benchmark`).
- **Performance Test:** Assert batch processor throughput exceeds 150 txns/sec in local mode.
