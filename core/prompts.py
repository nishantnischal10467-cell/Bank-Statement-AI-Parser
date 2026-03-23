from typing import Dict
import pandas as pd


def create_generation_prompt(target_bank: str, csv_schema: Dict, sample_text: str) -> str:
    """Create prompt for parser generation"""
    
    return f"""Create a Python parser for {target_bank} bank statement PDFs that EXACTLY matches the expected CSV output.

CRITICAL: The output MUST pass DataFrame.equals() validation with the expected CSV.

PDF SAMPLE TEXT:
{sample_text[:1500]}

EXPECTED CSV FORMAT:
Columns: {csv_schema['columns']}
Sample rows: {csv_schema['sample_data'][:5]}
Total rows expected: {csv_schema['total_rows']}

EXACT REQUIREMENTS:
1. Parse ALL transactions from PDF (must return {csv_schema['total_rows']} rows)
2. Use exact column names: ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']
3. Balance change logic: if balance increases -> Credit, if decreases -> Debit
4. For first row: analyze if it should be debit or credit based on transaction type
5. Clean descriptions by removing all numeric amounts
6. Use None (not NaN or empty string) for missing debit/credit amounts

PARSER CODE:

```python
import pandas as pd
import pdfplumber
import re
import os
from pathlib import Path

def parse(pdf_path: str, save_to_input_folder: bool = True) -> pd.DataFrame:
    \"\"\"
    Parse {target_bank} bank statement PDF and automatically save to input folder
    
    Args:
        pdf_path: Path to the PDF file
        save_to_input_folder: If True, saves CSV to same folder as PDF
    
    Returns:
        DataFrame with parsed transactions
    \"\"\"
    transactions = []
    prev_balance = None
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
                
            for line in text.split('\\n'):
                line = line.strip()
                if not line or 'Date' in line or 'Description' in line:
                    continue
                
                date_match = re.match(r'(\\d{{2}}-\\d{{2}}-\\d{{4}})', line)
                if not date_match:
                    continue
                
                date = date_match.group(1)
                rest = line[10:].strip()
                
                amounts = [float(x.replace(',', '')) for x in re.findall(r'[\\d,]+\\.?\\d*', rest)]
                if len(amounts) < 2:
                    continue
                
                balance = amounts[-1]
                txn_amount = amounts[-2]
                
                desc = rest
                for amt_str in re.findall(r'[\\d,]+\\.?\\d*', rest):
                    desc = desc.replace(amt_str, ' ')
                desc = re.sub(r'\\s+', ' ', desc).strip().rstrip('-').strip()
                
                debit_amt = None
                credit_amt = None
                
                if prev_balance is not None:
                    delta = balance - prev_balance
                    if delta > 0:
                        credit_amt = txn_amount
                    else:
                        debit_amt = txn_amount
                else:
                    debit_amt = txn_amount
                
                transactions.append({{
                    'Date': date,
                    'Description': desc,
                    'Debit Amt': debit_amt,
                    'Credit Amt': credit_amt,
                    'Balance': balance
                }})
                
                prev_balance = balance
    
    # Create DataFrame
    df = pd.DataFrame(transactions, columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
    
    # Auto-save to input folder if requested
    if save_to_input_folder:
        pdf_path_obj = Path(pdf_path)
        input_folder = pdf_path_obj.parent
        
        # Generate output filename based on input PDF name
        pdf_name = pdf_path_obj.stem
        output_filename = f\"{{pdf_name}}_parsed_transactions.csv\"
        output_path = input_folder / output_filename
        
        # Save CSV to input folder
        df.to_csv(output_path, index=False)
        print(f\"Parsed transactions saved to: {{output_path}}\")
        print(f\"Total transactions: {{len(df)}}\")
    
    return df
```

CRITICAL: This parser MUST produce output that passes result_df.equals(expected_df)."""


def create_fix_prompt(parser_code: str, csv_path: str, test_results: Dict) -> str:
    """Create prompt for parser debugging and fixing"""
    try:
        expected_df = pd.read_csv(csv_path)
        sample_expected = expected_df.head(5).to_dict('records')
    except:
        sample_expected = []
    
    return f"""Fix the parser that failed DataFrame.equals() validation. The output must EXACTLY match the expected CSV.

CURRENT FAILING CODE:
```python
{parser_code}
```

VALIDATION ERROR: {test_results.get('error', 'Unknown error')}

EXPECTED OUTPUT (first 5 rows):
{sample_expected}

CRITICAL FIX REQUIREMENTS:
1. Output must pass result_df.equals(expected_df) - no tolerance allowed
2. Exact column names: ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']
3. Use None (not NaN/empty string) for missing debit/credit amounts
4. Balance change logic: delta > 0 = Credit, delta < 0 = Debit
5. Clean descriptions by removing ALL numeric patterns
6. Must return exactly {len(expected_df) if 'expected_df' in locals() else 'expected'} transactions

DEBUGGING STEPS:
- Check if first transaction debit/credit assignment is correct
- Verify balance calculation matches expected values
- Ensure description cleaning removes all amounts but preserves text
- Confirm None vs NaN handling in debit/credit columns

CORRECTED PARSER:

```python
import pandas as pd
import pdfplumber
import re
import os
from pathlib import Path

def parse(pdf_path: str, save_to_input_folder: bool = True) -> pd.DataFrame:
    \"\"\"
    Parse bank statement PDF and automatically save to input folder
    
    Args:
        pdf_path: Path to the PDF file
        save_to_input_folder: If True, saves CSV to same folder as PDF
    
    Returns:
        DataFrame with parsed transactions
    \"\"\"
    transactions = []
    prev_balance = None
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
                
            for line in text.split('\\n'):
                line = line.strip()
                if not line or 'Date' in line or 'Description' in line:
                    continue
                
                date_match = re.match(r'(\\d{{2}}-\\d{{2}}-\\d{{4}})', line)
                if not date_match:
                    continue
                
                date = date_match.group(1)
                rest = line[10:].strip()
                
                amounts = [float(x.replace(',', '')) for x in re.findall(r'[\\d,]+\\.?\\d*', rest)]
                if len(amounts) < 2:
                    continue
                
                balance = amounts[-1]
                txn_amount = amounts[-2]
                
                desc = rest
                for amt_str in re.findall(r'[\\d,]+\\.?\\d*', rest):
                    desc = desc.replace(amt_str, ' ')
                desc = re.sub(r'\\s+', ' ', desc).strip().rstrip('-').strip()
                
                debit_amt = None
                credit_amt = None
                
                if prev_balance is not None:
                    delta = balance - prev_balance
                    if delta > 0:
                        credit_amt = txn_amount
                    else:
                        debit_amt = txn_amount
                else:
                    debit_amt = txn_amount
                
                transactions.append({{
                    'Date': date,
                    'Description': desc,
                    'Debit Amt': debit_amt,
                    'Credit Amt': credit_amt,
                    'Balance': balance
                }})
                
                prev_balance = balance
    
    # Create DataFrame
    df = pd.DataFrame(transactions, columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
    
    # Auto-save to input folder if requested
    if save_to_input_folder:
        pdf_path_obj = Path(pdf_path)
        input_folder = pdf_path_obj.parent
        
        # Generate output filename based on input PDF name
        pdf_name = pdf_path_obj.stem
        output_filename = f\"{{pdf_name}}_parsed_transactions.csv\"
        output_path = input_folder / output_filename
        
        # Save CSV to input folder
        df.to_csv(output_path, index=False)
        print(f\"Parsed transactions saved to: {{output_path}}\")
        print(f\"Total transactions: {{len(df)}}\")
    
    return df
```

CRITICAL: This must produce EXACTLY the same output as the expected CSV AND automatically save to input folder."""
