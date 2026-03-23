from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

import pdfplumber

from .models import CSV_HEADER, ConfidenceLevel
from .parsers import parse_icici_pdf
from .bank_configs import detect_bank_from_text, get_bank_config


def parse_bank_statement_to_csv(
    pdf_path: str | Path, 
    out_csv: str | Path,
    bank_hint: Optional[str] = None,
    verbose: bool = False
) -> Path:
    pdf_path = Path(pdf_path)
    out_csv = Path(out_csv)
    
    if verbose:
        print(f"Processing: {pdf_path}")
    
    if not bank_hint:
        if verbose:
            print("Auto-detecting bank type...")
        
        with pdfplumber.open(str(pdf_path)) as pdf:
            first_page_text = pdf.pages[0].extract_text() or ""
            bank_hint = detect_bank_from_text(first_page_text)
        
        if verbose:
            print(f"Detected bank: {bank_hint.upper()}")
    
    if bank_hint.lower() == "icici":
        rows = parse_icici_pdf(pdf_path)
    else:
        if verbose:
            print(f"Using ICICI parser for {bank_hint} (specialized parser coming soon)")
        rows = parse_icici_pdf(pdf_path)
    
    if verbose:
        print(f"Extracted {len(rows)} transactions")
        
        confidence_counts = {}
        for row in rows:
            conf = row.confidence or ConfidenceLevel.UNCERTAIN
            confidence_counts[conf.value] = confidence_counts.get(conf.value, 0) + 1
        
        print("Confidence distribution:")
        for conf, count in confidence_counts.items():
            print(f"   {conf}: {count} transactions")
    
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        for r in rows:
            writer.writerow(r.to_csv_row())
    
    if verbose:
        print(f"Saved to: {out_csv}")
    
    return out_csv

