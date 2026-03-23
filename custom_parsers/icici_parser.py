import pandas as pd
import pdfplumber
import re
from pathlib import Path

def parse(pdf_path: str, save_to_input_folder: bool = True) -> pd.DataFrame:
    """
    Parse ICICI bank statement PDF and automatically save to input folder
    
    Args:
        pdf_path: Path to the PDF file
        save_to_input_folder: If True, saves CSV to same folder as PDF
    
    Returns:
        DataFrame with parsed transactions
    """
    transactions = []
    prev_balance = None
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
                
            for line in text.split('\n'):
                line = line.strip()
                if not line or 'Date' in line or 'Description' in line:
                    continue
                
                date_match = re.match(r'(\d{2}-\d{2}-\d{4})', line)
                if not date_match:
                    continue
                
                date = date_match.group(1)
                rest = line[10:].strip()
                
                amounts = [float(x.replace(',', '')) for x in re.findall(r'[\d,]+\.?\d*', rest)]
                if len(amounts) < 2:
                    continue
                
                balance = amounts[-1]
                txn_amount = amounts[-2]
                
                desc = rest
                for amt_str in re.findall(r'[\d,]+\.?\d*', rest):
                    desc = desc.replace(amt_str, ' ')
                desc = re.sub(r'\s+', ' ', desc).strip().rstrip('-').strip()
                
                debit_amt = None
                credit_amt = None
                
                if prev_balance is not None:
                    delta = balance - prev_balance
                    if delta > 0:
                        credit_amt = txn_amount
                    else:
                        debit_amt = txn_amount
                else:
                    # For the first transaction, determine based on description
                    if 'Credit' in desc:
                        credit_amt = txn_amount
                    else:
                        debit_amt = txn_amount
                
                transactions.append({
                    'Date': date,
                    'Description': desc,
                    'Debit Amt': debit_amt,
                    'Credit Amt': credit_amt,
                    'Balance': balance
                })
                
                prev_balance = balance
    
    # Create DataFrame
    df = pd.DataFrame(transactions, columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
    
    # Auto-save to input folder if requested
    if save_to_input_folder:
        pdf_path_obj = Path(pdf_path)
        input_folder = pdf_path_obj.parent
        
        # Generate output filename based on input PDF name
        pdf_name = pdf_path_obj.stem
        output_filename = f"{pdf_name}_parsed_transactions.csv"
        output_path = input_folder / output_filename
        
        # Save CSV to input folder
        df.to_csv(output_path, index=False)
        print(f"Parsed transactions saved to: {output_path}")
        print(f"Total transactions: {len(df)}")
    
    return df