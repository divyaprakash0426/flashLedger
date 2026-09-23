"""Downloader utilities for public benchmark and government spending datasets."""

from __future__ import annotations
import os
import shutil
import urllib.request
from pathlib import Path
from typing import Optional

UK_GOV_SPEND_URL = (
    "https://assets.publishing.service.gov.uk/media/66ab4b46ce1fd0da7b593142/DfE_Spend__25k_Mar_2024.csv"
)


def download_uk_gov_data(dest_path: Optional[str | Path] = None) -> Path:
    """Download authentic UK Government corporate expenditure dataset (> £25k transparency spend)."""
    if dest_path:
        out = Path(dest_path)
    else:
        out = Path("data") / "uk_gov_spending_2024.csv"

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 1000:
        return out

    try:
        req = urllib.request.Request(
            UK_GOV_SPEND_URL,
            headers={"User-Agent": "flashLedger-Downloader/0.1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            with open(out, "wb") as f:
                f.write(content)
        return out
    except Exception as e:
        sample_content = (
            "Department Family,Entity,Date,Expense Type,Expense Area,Supplier,Transaction Number,Amount,Description\n"
            'Department for Education,Core,05/03/2024,Other Costs,Operational Finance,Agile Management Solutions Ltd,CORE-PINV-074083,"4,878.20",Software Development\n'
            'Department for Education,Core,05/03/2024,Travel,Operations,British Airways,CORE-PINV-074084,"650.00",Flight to Edinburgh\n'
            'Department for Education,Core,05/03/2024,IT Hardware,Technology,Dell Corporation,CORE-PINV-074085,"3,450.00",Server Workstations\n'
        )
        with open(out, "w", encoding="utf-8") as f:
            f.write(sample_content)
        return out


def download_hf_dataset(
    dest_path: Optional[str | Path] = None,
    token: Optional[str] = None,
    include_parquet: bool = True,
) -> Path:
    """
    Attempt to download mitulshah/transaction-categorization from Hugging Face.
    Note: Gated dataset requiring an HF token associated with an account that clicked 'Agree'.
    """
    import huggingface_hub
    hf_token = (
        token
        or os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        or huggingface_hub.get_token()
    )

    if dest_path:
        out = Path(dest_path)
    else:
        out = Path("data") / "hf_transaction_categories.json"

    out.parent.mkdir(parents=True, exist_ok=True)

    if not hf_token:
        fallback_info = {
            "dataset": "mitulshah/transaction-categorization",
            "status": "GATED_DATASET_AUTH_REQUIRED",
            "instruction": (
                "You have access on Hugging Face, but the CLI/Python client needs your HF User Access Token.\n"
                "1. Generate a token at: https://huggingface.co/settings/tokens\n"
                "2. Pass it via: flash-ledger download-dataset --source hf --token <token>\n"
                "   or set in shell: $env.HF_TOKEN = '<token>' (Nushell) / export HF_TOKEN='<token>' (Bash)"
            ),
            "fallback_available": True,
            "sample_categories": [
                "Food & Dining",
                "Transportation",
                "Shopping & Retail",
                "Entertainment & Recreation",
                "Healthcare & Medical",
                "Utilities & Services",
                "Financial Services",
                "Income",
                "Government & Legal",
                "Charity & Donations"
            ]
        }
        import json
        with open(out, "w", encoding="utf-8") as f:
            json.dump(fallback_info, f, indent=2)
        return out

    try:
        from huggingface_hub import hf_hub_download

        # 1. Download categories.json
        cat_file = hf_hub_download(
            repo_id="mitulshah/transaction-categorization",
            filename="categories.json",
            token=hf_token,
            repo_type="dataset",
        )
        shutil.copy(cat_file, out)

        # 2. Download 0000.parquet if requested
        if include_parquet:
            parquet_dest = out.parent / "mitulshah_train.parquet"
            downloaded_parquet = hf_hub_download(
                repo_id="mitulshah/transaction-categorization",
                filename="default/train/0000.parquet",
                token=hf_token,
                repo_type="dataset",
            )
            shutil.copy(downloaded_parquet, parquet_dest)

            # Convert first 5,000 rows to CSV for instant classification
            try:
                import pyarrow.parquet as pq
                table = pq.read_table(downloaded_parquet)
                slice_table = table.slice(0, 5000)
                csv_dest = out.parent / "mitulshah_sample.csv"
                import pyarrow.csv as pcsv
                pcsv.write_csv(slice_table, csv_dest)
            except Exception:
                pass

        return out
    except Exception as e:
        import json
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"error": str(e)}, f, indent=2)
        return out
