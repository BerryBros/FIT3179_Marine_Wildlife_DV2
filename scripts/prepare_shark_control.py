"""Download and aggregate the official Queensland Shark Control Program dataset.

Produces data/shark_control_yearly.csv used by Chart 10.
Run from the project root:
    python scripts/prepare_shark_control.py
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
URL = "https://www.data.qld.gov.au/dataset/cdb218fa-6add-48e7-ad42-ed8aaf8bff60/resource/28fefdac-a298-441f-b6bf-4d24126019d2/download/scp_numbers-caught.xlsx"


def clean_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def classify_status(value) -> str:
    s = str(value).strip().lower()
    if "deceased" in s or "dead" in s:
        return "Deceased"
    if "alive" in s:
        return "Alive"
    return "Other / unknown"


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    cols = {clean_name(c): c for c in df.columns}
    year_col = cols.get("year")
    status_col = cols.get("alivedeceased")
    number_col = cols.get("numbercaught")
    if not all([year_col, status_col, number_col]):
        raise ValueError(
            "The Queensland workbook schema has changed. Expected Year, Alive/Deceased and NumberCaught columns. "
            f"Found: {list(df.columns)}"
        )

    work = df[[year_col, status_col, number_col]].copy()
    work.columns = ["year", "raw_status", "number_caught"]
    work["year"] = pd.to_numeric(work["year"], errors="coerce")
    work["number_caught"] = pd.to_numeric(work["number_caught"], errors="coerce").fillna(0)
    work = work[work["year"].between(2010, 2026, inclusive="both")]
    work["year"] = work["year"].astype(int)
    work["status"] = work["raw_status"].map(classify_status)
    out = work.groupby(["year", "status"], as_index=False)["number_caught"].sum()
    return out.sort_values(["year", "status"])


def main() -> None:
    print("Downloading Queensland Shark Control Program catch data...")
    r = requests.get(URL, timeout=90)
    r.raise_for_status()
    sheets = pd.read_excel(BytesIO(r.content), sheet_name=None)
    df = None
    for sheet_name, candidate in sheets.items():
        keys = {clean_name(c) for c in candidate.columns}
        if {"year", "alivedeceased", "numbercaught"}.issubset(keys):
            df = candidate
            print(f"Using workbook sheet: {sheet_name}")
            break
    if df is None:
        raise ValueError("Could not find a worksheet containing Year, Alive/Deceased and NumberCaught.")
    out = aggregate(df)
    DATA.mkdir(exist_ok=True)
    target = DATA / "shark_control_yearly.csv"
    out.to_csv(target, index=False)
    print(f"Wrote {target.relative_to(ROOT)} ({len(out):,} rows; {out['year'].min()}–{out['year'].max()})")
    print("Measure: animals caught, grouped by alive/deceased status recorded at capture; this is not a population trend.")


if __name__ == "__main__":
    main()
