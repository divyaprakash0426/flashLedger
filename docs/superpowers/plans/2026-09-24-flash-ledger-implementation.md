# flashLedger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `flashLedger`, an ultra-fast, sub-100ms autonomous bank feed categorizer and tax auditor powered by TypeSafe Jev under the Apache 2.0 license, complete with CLI, MCP server, accounting exporters, benchmark split-screen demo, dataset tooling, and comprehensive offline tests.

**Architecture:** Async Python library and CLI using `typesafe-sdk`, `httpx`, `pydantic`, `rich`, `typer`, and `FastMCP`. Employs parallel Jev primitives (`Choice`, `Noul`, `Score`) to audit transactions for GL account classification, tax deductibility, CapEx vs OpEx, and risk score in a single round trip, with high-fidelity local deterministic mock engine for zero-cost offline testing.

**Tech Stack:** Python 3.12+, `uv`, `typesafe-sdk`, `pydantic>=2.0`, `rich>=13.0`, `typer>=0.12`, `httpx>=0.27`, `mcp>=1.0`, `pytest`, `pytest-asyncio`, `respx`.

**Spec:** `docs/superpowers/specs/2026-09-24-flash-ledger-design.md`

## Global Constraints

- Must be licensed under Apache 2.0.
- Public GitHub repository created at `divyaprakash0426/flashLedger`.
- All tests must run 100% locally and offline without requiring paid API keys.
- Strictly adhere to Nushell syntax when providing shell scripts/commands to the user.
- Adhere to TypeSafe Jev primitives: `Choice` (COA classification), `Noul` (Tax deductibility boolean probability), `Choice` (CapEx vs OpEx), `Score` (Audit risk index).

## Review Focus

1. **Missing or Corrupted Bank CSV Columns:** Parser must gracefully fall back across Chase, Amex, Mercury, Brex, and UK Gov spending headers.
2. **CapEx Safe Harbor Threshold:** Any asset purchase exceeding $2,500 must automatically trigger `CAPEX_REVIEW_REQUIRED` flag.
3. **No-API-Key Offline Graceful Mode:** If `TYPESAFE_API_KEY` is unset, CLI and benchmark must clearly explain and operate in deterministic mock mode without throwing unhandled exceptions.
4. **Export Schema Conformance:** Output files for QBO, Xero, and FreshBooks must match the exact expected header columns for those platforms.
5. **High Concurrency Stability:** Async batch processor must handle empty batches, single-item batches, and batches of 1,000+ items without semaphore starvation or race conditions.

---

### Task 1: Project Scaffolding, `pyproject.toml`, Git & GitHub Repo Setup

**Files:**
- Create: `pyproject.toml`
- Create: `flash_ledger/__init__.py`
- Modify: `.gitignore`
- Test: `tests/test_scaffolding.py`

**Interfaces:**
- Produces: Package `flash_ledger` version `0.1.0` importable in virtual environment.

- [ ] **Step 1: Write `pyproject.toml` with uv build configuration and dependencies**
- [ ] **Step 2: Initialize git repository and commit initial baseline (LICENSE, README, docs)**
- [ ] **Step 3: Create public GitHub repo via `gh repo create divyaprakash0426/flashLedger --public --source=. --remote=origin --push`**
- [ ] **Step 4: Create virtual environment using `uv venv` and install dependencies with `uv pip install -e .`**
- [ ] **Step 5: Write `tests/test_scaffolding.py` and run `uv run pytest tests/test_scaffolding.py` to verify package import and version**

---

### Task 2: Core Data Models & Chart of Accounts (COA) Loader

**Files:**
- Create: `flash_ledger/models.py`
- Create: `flash_ledger/coa.py`
- Create: `flash_ledger/data/default_coa.json`
- Test: `tests/test_models.py`
- Test: `tests/test_coa.py`

**Interfaces:**
- Consumes: None
- Produces:
  - `Transaction(id, date, raw_description, clean_description, amount, currency, account)`
  - `AuditResult(gl_code, gl_confidence, is_tax_deductible, deductible_probability, expense_type, audit_risk_score, flags, latency_ms)`
  - `ChartOfAccounts.load(path_or_dict)` providing standard GAAP/IRS accounts and custom loader.

- [ ] **Step 1: Write failing unit test for `Transaction`, `AuditResult`, and `ChartOfAccounts`**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `models.py` and `coa.py` with standard default Chart of Accounts JSON**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit changes**

---

### Task 3: Preprocessor & Bank Statement Parser

**Files:**
- Create: `flash_ledger/preprocessor.py`
- Test: `tests/test_preprocessor.py`

**Interfaces:**
- Consumes: `flash_ledger.models.Transaction`
- Produces:
  - `clean_merchant_string(raw: str) -> str`
  - `parse_amount(val: str | float) -> float`
  - `parse_statement_csv(filepath: str | Path) -> list[Transaction]`

- [ ] **Step 1: Write failing tests for parsing noisy merchant strings (SQ*, AMZN Mktp, GITHUB*, trailing store IDs) and CSV statement formats (Chase, Amex, Brex, Mercury, UK Gov)**
- [ ] **Step 2: Run tests to verify failure**
- [ ] **Step 3: Implement cleaning regexes, normalization, and smart CSV column detector in `preprocessor.py`**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit changes**

---

### Task 4: TypeSafe Jev Decision Engine & Deterministic Mock Engine

**Files:**
- Create: `flash_ledger/engine.py`
- Test: `tests/test_engine.py`

**Interfaces:**
- Consumes: `typesafe_sdk`, `Transaction`, `ChartOfAccounts`, `AuditResult`
- Produces:
  - `JevDecisionEngine(api_key: str | None = None, mode: str = "auto", coa: ChartOfAccounts | None = None)`
  - `async audit_transaction(txn: Transaction) -> AuditResult`

- [ ] **Step 1: Write failing tests for Jev request construction (`Choice`, `Noul`, `Score`), response mapping, and deterministic mock engine fallback**
- [ ] **Step 2: Run tests to verify failure**
- [ ] **Step 3: Implement `JevDecisionEngine` with multi-attribute question payload and high-accuracy mock engine for offline use**
- [ ] **Step 4: Run tests to verify pass**
- [ ] **Step 5: Commit changes**

---

### Task 5: High-Throughput Async Batch Processor & Auditor Rules

**Files:**
- Create: `flash_ledger/batch.py`
- Test: `tests/test_batch.py`

**Interfaces:**
- Consumes: `JevDecisionEngine`, `Transaction`, `AuditResult`
- Produces:
  - `BatchAuditor(engine: JevDecisionEngine, max_concurrency: int = 50, capex_threshold: float = 2500.0)`
  - `async audit_batch(transactions: list[Transaction], progress_callback=None) -> BatchAuditReport`

- [ ] **Step 1: Write failing tests for batch execution, concurrency throttling, CapEx threshold flagging, and progress reporting**
- [ ] **Step 2: Run tests to verify failure**
- [ ] **Step 3: Implement `BatchAuditor` with `asyncio.Semaphore`, CapEx rule evaluations, and statistical summary generation**
- [ ] **Step 4: Run tests to verify pass**
- [ ] **Step 5: Commit changes**

---

### Task 6: Exporters (QuickBooks Online, Xero, FreshBooks, CSV/JSON)

**Files:**
- Create: `flash_ledger/exporters.py`
- Test: `tests/test_exporters.py`

**Interfaces:**
- Consumes: `list[tuple[Transaction, AuditResult]]`
- Produces:
  - `export_qbo_csv(items, output_path)`
  - `export_xero_csv(items, output_path)`
  - `export_freshbooks_csv(items, output_path)`
  - `export_json(items, output_path)`

- [ ] **Step 1: Write failing tests verifying column headers and row formatting for QBO, Xero, and FreshBooks**
- [ ] **Step 2: Run tests to verify failure**
- [ ] **Step 3: Implement export formatters in `exporters.py`**
- [ ] **Step 4: Run tests to verify pass**
- [ ] **Step 5: Commit changes**

---

### Task 7: FastMCP Server Integration

**Files:**
- Create: `flash_ledger/mcp_server.py`
- Test: `tests/test_mcp_server.py`

**Interfaces:**
- Consumes: `flash_ledger.engine.JevDecisionEngine`, `flash_ledger.preprocessor`
- Produces: FastMCP tools: `classify_transaction`, `audit_expense_batch`, `get_chart_of_accounts`, `export_transactions`

- [ ] **Step 1: Write failing test verifying MCP server tool definitions and execution**
- [ ] **Step 2: Run tests to verify failure**
- [ ] **Step 3: Implement MCP server with FastMCP**
- [ ] **Step 4: Run tests to verify pass**
- [ ] **Step 5: Commit changes**

---

### Task 8: Dataset Download Pipeline & Benchmark Data Generator

**Files:**
- Create: `flash_ledger/datasets/download.py`
- Create: `flash_ledger/datasets/synthetic.py`
- Test: `tests/test_datasets.py`

**Interfaces:**
- Consumes: None
- Produces:
  - `download_uk_gov_data(dest_path: Path) -> Path`
  - `download_hf_dataset(dest_path: Path, token: str | None = None) -> Path`
  - `generate_benchmark_dataset(count: int = 1000) -> list[Transaction]`

- [ ] **Step 1: Write failing test for dataset generator and downloader functions**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement UK Gov spending fetcher, HF dataset loader with auth checks, and realistic 1,000-10,000 transaction generator**
- [ ] **Step 4: Run test to verify pass and generate `data/benchmark_sample_1000.csv`**
- [ ] **Step 5: Commit changes**

---

### Task 9: Viral Split-Screen Demo & Rich CLI

**Files:**
- Create: `flash_ledger/demo.py`
- Create: `flash_ledger/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: All `flash_ledger` modules
- Produces:
  - CLI commands: `flash-ledger classify`, `flash-ledger audit`, `flash-ledger benchmark`, `flash-ledger demo`, `flash-ledger download-dataset`, `flash-ledger mcp`
  - Split-screen live terminal waterfall comparing GPT-4o vs Jev

- [ ] **Step 1: Write failing test for Typer CLI commands**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement `demo.py` with `rich.live` split screen and `cli.py` with Typer**
- [ ] **Step 4: Run tests to verify pass**
- [ ] **Step 5: Commit changes**

---

### Task 10: End-to-End Verification, Documentation & GitHub Push

**Files:**
- Create: `README.md`
- Create: `docs/BENCHMARKS.md`
- Create: `tests/test_e2e.py`

**Interfaces:**
- Full suite verification and public repository publication.

- [ ] **Step 1: Run complete test suite with coverage**
- [ ] **Step 2: Run CLI benchmark and demo to verify waterfall animation and performance metrics**
- [ ] **Step 3: Write comprehensive `README.md` with LinkedIn demo guide, architecture, installation, and CLI examples**
- [ ] **Step 4: Commit all files and push to `divyaprakash0426/flashLedger` on GitHub**
