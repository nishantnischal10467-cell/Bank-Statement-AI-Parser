from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Optional

from .pipeline import parse_bank_statement_to_csv


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


def print_progress(message: str, step: int = 0, total: int = 0) -> None:
    if total > 0:
        progress = f"[{step}/{total}] "
    else:
        progress = ""
    print(f"{progress}{message}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bank Statement Parser - Convert PDF statements to CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py statement.pdf
  python main.py statement.pdf --out results.csv
  python main.py statement.pdf --bank hdfc --confidence-report
        """
    )
    
    parser.add_argument("pdf", type=str, help="Path to input PDF")
    parser.add_argument("--out", type=str, default=None, help="Output CSV path")
    parser.add_argument("--bank", type=str, choices=["icici", "hdfc", "sbi", "auto"], 
                       default="auto", help="Bank type (auto-detect if not specified)")
    parser.add_argument("--confidence-report", action="store_true", 
                       help="Generate confidence report for parsed transactions")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Validate input
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"Error: Input PDF not found: {pdf_path}")
    
    out = Path(args.out) if args.out else pdf_path.with_suffix("")
    out_csv = out if out.suffix.lower() == ".csv" else out.with_suffix(".csv")
    
    print("Bank Statement Parser")
    print(f"Input: {pdf_path}")
    print(f"Output: {out_csv}")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set; using text-only parsing")
    
    # Start processing
    start_time = time.time()
    
    try:
        print_progress("Starting PDF analysis...")
        
        res = parse_bank_statement_to_csv(
            pdf_path, 
            out_csv,
            bank_hint=args.bank if args.bank != "auto" else None,
            verbose=args.verbose
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Success! Wrote: {res}")
        print(f"Processing time: {format_duration(duration)}")
        
        if out_csv.exists():
            with open(out_csv, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                transaction_count = len(lines) - 1
                print(f"Extracted {transaction_count} transactions")
        
        if args.confidence_report:
            print_progress("Generating confidence report...")
            print("Confidence report: Feature coming soon!")
            
    except Exception as e:
        print(f"Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

