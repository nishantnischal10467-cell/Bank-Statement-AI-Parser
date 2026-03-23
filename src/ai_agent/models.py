from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional
from enum import Enum


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


@dataclass(slots=True)
class Transaction:
    date: str
    description: str
    debit: float | None
    credit: float | None
    balance: float | None
    confidence: Optional[ConfidenceLevel] = None
    parsing_method: Optional[str] = None
    validation_notes: Optional[str] = None

    def to_csv_row(self) -> list[str]:
        def fmt(value: float | None) -> str:
            return "" if value is None else ("%g" % value)

        return [self.date, self.description, fmt(self.debit), fmt(self.credit), fmt(self.balance)]
    
    def get_amount(self) -> float:
        """Get the transaction amount (debit or credit)."""
        return self.debit if self.debit is not None else (self.credit or 0.0)
    
    def is_debit(self) -> bool:
        """Check if this is a debit transaction."""
        return self.debit is not None
    
    def is_credit(self) -> bool:
        """Check if this is a credit transaction."""
        return self.credit is not None


CSV_HEADER = ["Date", "Description", "Debit Amt", "Credit Amt", "Balance"]


def normalize_date(date_text: str) -> str:
    text = date_text.strip().replace(".", "-").replace("/", "-")
    for fmt in ("%d-%m-%Y", "%d-%m-%y", "%d-%b-%Y", "%d-%b-%y", "%d-%m-%Y "):
        try:
            return datetime.strptime(text, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return text


def coerce_float(text: str | None) -> float | None:
    if text is None:
        return None
    s = text.strip().replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def dedupe_contiguous(rows: Iterable[Transaction]) -> list[Transaction]:
    result: list[Transaction] = []
    prev: Transaction | None = None
    for r in rows:
        if prev and (
            prev.date == r.date
            and prev.description == r.description
            and prev.debit == r.debit
            and prev.credit == r.credit
            and prev.balance == r.balance
        ):
            continue
        result.append(r)
        prev = r
    return result

