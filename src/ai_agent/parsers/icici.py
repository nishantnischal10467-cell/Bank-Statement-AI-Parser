from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pdfplumber

from ..models import Transaction, CSV_HEADER, normalize_date, coerce_float, dedupe_contiguous, ConfidenceLevel
from ..pdf_utils import iter_page_images
from ..llm import vision_structured_extract_png
from ..config import get_settings

LINE_RE = re.compile(
    r"^(?P<date>\d{1,2}[-/][A-Za-z0-9]{2,}[-/]\d{2,4})\s+(?P<desc>.+?)\s+(?P<amount>[\d,]+\.?\d*)\s+(?P<balance>-?[\d,]+\.?\d*)\s*$"
)

CREDIT_INDICATORS = [
    'credit', 'deposit', 'salary', 'interest', 'refund', 'cashback', 
    'transfer from', 'neft from', 'imps from', 'rtgs from', 'reversal'
]

DEBIT_INDICATORS = [
    'debit', 'payment', 'purchase', 'withdrawal', 'charge', 'fee',
    'transfer to', 'neft to', 'imps to', 'rtgs to', 'emi', 'bill',
    'shopping', 'atm'
]


def _calculate_confidence(description: str, amount: float, prev_balance: float, curr_balance: float, 
                         parsing_method: str) -> tuple[ConfidenceLevel, str]:
    desc_lower = description.lower()
    confidence_score = 0.5
    notes = []
    
    is_credit_desc = any(indicator in desc_lower for indicator in CREDIT_INDICATORS)
    is_debit_desc = any(indicator in desc_lower for indicator in DEBIT_INDICATORS)
    
    if is_credit_desc or is_debit_desc:
        confidence_score += 0.3
        notes.append("clear_description")
    
    balance_change = curr_balance - prev_balance
    expected_change = amount if is_credit_desc else -amount
    
    if abs(balance_change - expected_change) <= 0.01:
        confidence_score += 0.2
        notes.append("balance_consistent")
    elif abs(balance_change + expected_change) <= 0.01:
        confidence_score += 0.1
        notes.append("balance_inverted")
    else:
        confidence_score -= 0.1
        notes.append("balance_mismatch")
    
    # Adjust for parsing method
    if parsing_method == "text":
        confidence_score += 0.1
    elif parsing_method == "llm":
        confidence_score -= 0.05
    
    # Determine confidence level
    if confidence_score >= 0.9:
        level = ConfidenceLevel.HIGH
    elif confidence_score >= 0.7:
        level = ConfidenceLevel.MEDIUM
    elif confidence_score >= 0.5:
        level = ConfidenceLevel.LOW
    else:
        level = ConfidenceLevel.UNCERTAIN
    
    return level, "; ".join(notes)


def _determine_transaction_type(description: str, amount: float, prev_balance: float, curr_balance: float) -> tuple[float | None, float | None]:
    """
    Determine if transaction is debit or credit based on description and balance change.
    Returns (debit_amount, credit_amount) where one is None.
    """
    desc_lower = description.lower()
    
    # Check description for explicit indicators
    is_credit_desc = any(indicator in desc_lower for indicator in CREDIT_INDICATORS)
    is_debit_desc = any(indicator in desc_lower for indicator in DEBIT_INDICATORS)
    
    # If description is clear, use it
    if is_credit_desc and not is_debit_desc:
        return None, amount
    elif is_debit_desc and not is_credit_desc:
        return amount, None
    
    # Fallback: use balance change (more reliable for edge cases)
    balance_change = curr_balance - prev_balance
    
    # If balance increased, it's likely a credit
    if balance_change > 0:
        return None, amount
    else:
        return amount, None


def _parse_text_rows(pdf_path: str | Path) -> list[Transaction]:
    rows: list[Transaction] = []
    prev_balance = 0.0
    
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = text.splitlines()
            
            for raw in lines:
                line = raw.strip()
                if not line or "Date" in line or "Description" in line:
                    continue
                    
                m = LINE_RE.match(line)
                if not m:
                    continue

                date = normalize_date(m.group("date"))
                desc = m.group("desc").strip()
                amount = coerce_float(m.group("amount"))
                balance = coerce_float(m.group("balance"))
                
                if amount is None or balance is None:
                    continue
                
                debit, credit = _determine_transaction_type(desc, amount, prev_balance, balance)
                confidence, notes = _calculate_confidence(desc, amount, prev_balance, balance, "text")
                
                rows.append(Transaction(
                    date=date, 
                    description=desc, 
                    debit=debit, 
                    credit=credit, 
                    balance=balance,
                    confidence=confidence,
                    parsing_method="text",
                    validation_notes=notes
                ))
                prev_balance = balance
                
    return rows


def _llm_rows(pdf_path: str | Path) -> list[Transaction]:
    settings = get_settings()
    rows: list[Transaction] = []
    prev_balance = 0.0
    
    for page in iter_page_images(pdf_path, max_pages=settings.max_pages, max_px=settings.image_max_px):
        entries = vision_structured_extract_png(page.image_bytes)
        for e in entries:
            date = normalize_date(str(e.get("date", "")).strip())
            desc = str(e.get("description", "")).strip()
            
            amount = coerce_float(str(e.get("amount")) if e.get("amount") is not None else None)
            balance = coerce_float(str(e.get("balance")) if e.get("balance") is not None else None)
            
            if not desc or not amount or balance is None:
                continue
            
            if amount > 0:
                debit, credit = None, amount
            else:
                debit, credit = abs(amount), None
            
            confidence, notes = _calculate_confidence(desc, amount, prev_balance, balance, "llm")
            
            rows.append(Transaction(
                date=date,
                description=desc,
                debit=debit,
                credit=credit,
                balance=balance,
                confidence=confidence,
                parsing_method="llm",
                validation_notes=notes
            ))
            prev_balance = balance
            
    return rows


def _validate_and_fix_transactions(rows: list[Transaction]) -> list[Transaction]:
    if not rows:
        return rows
    
    validated_rows = []
    
    for i, row in enumerate(rows):
        if not row.description or row.balance is None:
            continue
            
        if i > 0:
            prev_row = validated_rows[-1] if validated_rows else None
            if prev_row and prev_row.balance is not None:
                expected_balance = prev_row.balance
                
                if row.debit:
                    expected_balance -= row.debit
                if row.credit:
                    expected_balance += row.credit
                
                # Check if balance calculation makes sense (allow small rounding differences)
                balance_diff = abs(expected_balance - row.balance)
                if balance_diff > 0.01:
                    # Try to fix by swapping debit/credit if possible
                    if row.debit and not row.credit:
                        # Try as credit
                        test_balance = prev_row.balance + row.debit
                        if abs(test_balance - row.balance) <= 0.01:
                            row = Transaction(
                                date=row.date, 
                                description=row.description, 
                                debit=None, 
                                credit=row.debit, 
                                balance=row.balance,
                                confidence=ConfidenceLevel.MEDIUM,
                                parsing_method=row.parsing_method or "validation_corrected",
                                validation_notes="corrected_debit_to_credit"
                            )
                    elif row.credit and not row.debit:
                        # Try as debit
                        test_balance = prev_row.balance - row.credit
                        if abs(test_balance - row.balance) <= 0.01:
                            row = Transaction(
                                date=row.date, 
                                description=row.description, 
                                debit=row.credit, 
                                credit=None, 
                                balance=row.balance,
                                confidence=ConfidenceLevel.MEDIUM,
                                parsing_method=row.parsing_method or "validation_corrected",
                                validation_notes="corrected_credit_to_debit"
                            )
        
        validated_rows.append(row)
    
    return validated_rows


def parse_icici_pdf(pdf_path: str | Path) -> list[Transaction]:
    """Enhanced parsing with validation and error correction."""
    # Try text parsing first (more accurate)
    rows = _parse_text_rows(pdf_path)
    
    # Fallback to LLM if text parsing fails
    if not rows:
        rows = _llm_rows(pdf_path)
    
    # Validate and fix transactions
    rows = _validate_and_fix_transactions(rows)
    
    # Remove duplicates
    rows = dedupe_contiguous(rows)
    
    return rows

