# Product Requirements Document (PRD): flashLedger

### Autonomous Bank Feed & Card Auditor Powered by TypeSafe Jev

* **Virality Score:** **9.8 / 10**
* **Target Audience:** CFOs, CPAs, indie hackers, bookkeepers, and FinTech developers.
* **The Relatable Pain:** Every business owner and finance department dreads monthly bookkeeping. Raw bank strings are notoriously cryptic (e.g., `SQ *BLUE BOTTLE SOMA`, `AMZN Mktp US*284J1`, `GITHUB*SPONSOR 877-448`). Standard rule-based engines break constantly, while frontier LLMs (GPT-4o, Claude 3.5) are too slow and expensive to run on thousands of micro-transactions.
* **The Visual "Hook" for LinkedIn:** A side-by-side split screen showing **GPT-4o classifying 50 transactions in 28 seconds (costing $0.45)** while **Jev sorts 1,000 transactions in under 3.5 seconds (costing $0.01)** with a live terminal/web waterfall animation.

---

## 1. Executive Summary

**Project Name:** `flashLedger` (Open Source under Apache 2.0)

**One-Liner:** An ultra-fast, sub-100ms bank feed categorizer and tax auditor powered by TypeSafe Jev. It parses raw financial statements and maps transactions to standard General Ledger (GL) Chart of Accounts (COA) with tax-deductibility flags.

---

## 2. Target Datasets (Open Source & Public)

To train, benchmark, and demonstrate `flashLedger`, use the following open datasets:

1. **Primary Evaluation Dataset:** [mitulshah/transaction-categorization (Hugging Face)](https://huggingface.co/datasets/mitulshah/transaction-categorization)
* **Scale:** 4.5+ million financial transaction records across 5 currencies (USD, GBP, CAD, AUD, INR) and 5 countries.
* **Format:** Parquet / CSV.
* **Fields:** `transaction_description`, `category`, `country`, `currency`.
* **Why it fits:** Features real-world noisy descriptions (merchant abbreviations, point-of-sale codes, trailing numbers) that break traditional regex.

2. **Real-World Corporate Expenditure Dataset:** [UK Government Spending Data (`data.gov.uk` / `publishing.service.gov.uk`)](https://www.data.gov.uk/dataset/64b81d31-c056-40a1-826a-8516951aa9b3/financial-transactions-data-co)
* **Scale:** Hundreds of thousands of corporate B2B transactions.
* **Fields:** Supplier name, amount, expense type, narrative description.
* **Why it fits:** Provides authentic B2B SaaS, vendor invoices, and travel expense patterns.

---

## 3. Core Architecture & Jev Type Integration

`flashLedger` utilizes Jev’s typed primitives (`Choice`, `Noul`, `Score`) in parallel to execute a multi-attribute audit in a single round-trip:

```
[ Raw Bank Transaction String ]
  "SQ *BLUE BOTTLE COFFEE - $14.20"
                │
                ▼
      ┌──────────────────┐
      │   flashLedger    │
      │  Pre-Processor   │ (Strips terminal noise, normalizes currency)
      └─────────┬────────┘
                │
                ▼
      ┌─────────────────────────────────────────────────────────────┐
      │                  Jev Decision Engine                        │
      │                                                             │
      │  1. Choice (GL Account Code):                               │
      │     ["Meals & Entertainment", "Office Supplies",            │
      │      "Software/SaaS", "Travel", "Professional Fees", ...]   │
      │     ──► "Meals & Entertainment"                             │
      │                                                             │
      │  2. Noul (Tax Deductible Business Expense?):                │
      │     ──► Yes (Probability: 0.96)                             │
      │                                                             │
      │  3. Choice (CapEx vs OpEx):                                 │
      │     ──► "OpEx"                                              │
      │                                                             │
      │  4. Score (Audit Flag / Risk Index):                        │
      │     ──► 0.08 (Low risk)                                     │
      └─────────────────────────┬───────────────────────────────────┘
                                │
                                ▼
         [ Structured Output / Export to QBO/Xero/CSV ]
```

---

## 4. Key Functional Features

### Phase 1: Core Engine (CLI & Python Library)

* **`flash-ledger classify <file.csv>`:** Ingests raw bank/credit card CSV exports (Chase, Amex, Mercury, Brex, Stripe) and appends classified GL codes, deductible status, and confidence scores.
* **Custom Chart-of-Accounts (COA) Loader:** Allows companies to supply a custom `coa.json` or `coa.yaml` matching their existing QuickBooks or NetSuite hierarchy.
* **High-Throughput Batching:** Uses asynchronous HTTP workers to process transactions through Jev in batches of 50–100, reaching 200+ transactions per second.

### Phase 2: Accounting Platform Connectors & MCP Server

* **Export Presets:** Formats ready for one-click import into QuickBooks Online (QBO), Xero, and FreshBooks.
* **Model Context Protocol (MCP) Server:** Exposes `classify_transaction` and `audit_expense_batch` tools so Claude Code, Cursor, or Copilot agents can invoke accounting audits natively.

---

## 5. Benchmark & Economics Target

| Metric | Traditional LLM (GPT-4o / Claude 3.5) | `flashLedger` (Jev) |
| --- | --- | --- |
| **Latency per 100 txns** | 15 – 35 seconds | **0.8 – 1.8 seconds** (Parallel) |
| **Cost per 10,000 txns** | ~$15.00 – $35.00 | **<$0.10** |
| **Schema Guarantees** | Prone to JSON parse errors or invalid codes | **100% Typed** (Matches COA enum strictly) |

---

## 6. LinkedIn Launch & Viral Demo Plan

### The Video Concept (35–45 seconds)

* **Format:** 16:9 or 1:1, high-contrast dark-mode terminal animation (built using `rich` / `textual` in Python, or a frontend web view).
* **The Scene:**
* **0:00 - 0:08:** Split screen starts.
* Left side: *Traditional LLM (GPT-4o)*. It streams slowly line-by-line with a spinning loader: `Processing transaction 3 of 50...`
* Right side: *`flashLedger` (Jev)*. A lightning-fast waterfall cascade of transactions resolving into color-coded tags (`[SaaS]`, `[Meals]`, `[CapEx]`, `[Travel]`).
* **0:08 - 0:20:** The right side hits `1,000 / 1,000 processed in 3.42s`. The left side is still at `12 / 50`.
* **0:20 - 0:30:** Zoom into anomalous transactions Jev flagged automatically:
* `CASINO HOTEL LAS VEGAS - $850.00` ➔ `Audit Score: 0.94 (FLAGGED)`
* `APPLE STORE #104 - $3,299.00` ➔ `CapEx Review Required (> $2,500 threshold)`
* **0:30 - 0:40:** Final cost & speed counter graphic. Link to GitHub repository.
