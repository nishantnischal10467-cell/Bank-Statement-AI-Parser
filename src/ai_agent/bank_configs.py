"""
Multi-bank support configuration system.
Defines parsing patterns and indicators for different banks.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Pattern
import re


@dataclass
class BankConfig:
    """Configuration for a specific bank's statement format."""
    name: str
    line_patterns: List[Pattern]
    credit_indicators: List[str]
    debit_indicators: List[str]
    date_formats: List[str]
    currency_symbol: str = "₹"
    
    
# ICICI Bank Configuration
ICICI_CONFIG = BankConfig(
    name="ICICI",
    line_patterns=[
        re.compile(r"^(?P<date>\d{1,2}[-/][A-Za-z0-9]{2,}[-/]\d{2,4})\s+(?P<desc>.+?)\s+(?P<amount>[\d,]+\.?\d*)\s+(?P<balance>-?[\d,]+\.?\d*)\s*$"),
        re.compile(r"^(?P<date>\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\s+(?P<desc>.+?)\s+(?P<amount>[\d,]+\.?\d*)\s+(?P<balance>-?[\d,]+\.?\d*)\s*$")
    ],
    credit_indicators=[
        'credit', 'deposit', 'salary', 'interest', 'refund', 'cashback', 
        'transfer from', 'neft from', 'imps from', 'rtgs from', 'reversal'
    ],
    debit_indicators=[
        'debit', 'payment', 'purchase', 'withdrawal', 'charge', 'fee',
        'transfer to', 'neft to', 'imps to', 'rtgs to', 'emi', 'bill',
        'shopping', 'atm'
    ],
    date_formats=["%d-%m-%Y", "%d/%m/%Y", "%d-%b-%Y", "%d/%b/%Y"]
)

# HDFC Bank Configuration
HDFC_CONFIG = BankConfig(
    name="HDFC",
    line_patterns=[
        re.compile(r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\s+(?P<desc>.+?)\s+(?P<amount>[\d,]+\.?\d*)\s+(?P<balance>[\d,]+\.?\d*)\s*$")
    ],
    credit_indicators=[
        'cr', 'credit', 'sal', 'int', 'dep', 'trf in', 'cash dep'
    ],
    debit_indicators=[
        'dr', 'debit', 'atm', 'pos', 'emi', 'trf out', 'chq'
    ],
    date_formats=["%d/%m/%Y", "%d/%m/%y"]
)

# SBI Bank Configuration  
SBI_CONFIG = BankConfig(
    name="SBI",
    line_patterns=[
        re.compile(r"^(?P<date>\d{1,2}-\d{1,2}-\d{4})\s+(?P<desc>.+?)\s+(?P<amount>[\d,]+\.?\d*)\s+(?P<balance>[\d,]+\.?\d*)\s*$")
    ],
    credit_indicators=[
        'credit', 'dep', 'salary', 'interest', 'dividend', 'tds refund'
    ],
    debit_indicators=[
        'debit', 'withdrawal', 'purchase', 'charges', 'sms', 'annual fee'
    ],
    date_formats=["%d-%m-%Y"]
)

# Bank registry
BANK_CONFIGS: Dict[str, BankConfig] = {
    "icici": ICICI_CONFIG,
    "hdfc": HDFC_CONFIG, 
    "sbi": SBI_CONFIG
}


def detect_bank_from_text(text: str) -> str:
    """Auto-detect bank from statement text."""
    text_lower = text.lower()
    
    if any(keyword in text_lower for keyword in ["icici", "chatgpt powered karbon bannk"]):
        return "icici"
    elif any(keyword in text_lower for keyword in ["hdfc", "housing development"]):
        return "hdfc"
    elif any(keyword in text_lower for keyword in ["sbi", "state bank", "भारतीय स्टेट बैंक"]):
        return "sbi"
    
    # Default to ICICI for unknown formats
    return "icici"


def get_bank_config(bank_name: str) -> BankConfig:
    """Get configuration for a specific bank."""
    return BANK_CONFIGS.get(bank_name.lower(), ICICI_CONFIG)
