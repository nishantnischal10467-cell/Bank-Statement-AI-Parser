from typing import Dict, Any
import pandas as pd


def validate_dataframe(result_df: pd.DataFrame, expected_df: pd.DataFrame) -> Dict[str, Any]:
    """Validate parsed DataFrame against expected output"""
    try:
        if result_df.shape != expected_df.shape:
            return {
                "passes_validation": False,
                "error": f"Shape mismatch: got {result_df.shape}, expected {expected_df.shape}"
            }
        
        if list(result_df.columns) != list(expected_df.columns):
            return {
                "passes_validation": False,
                "error": f"Column mismatch: got {list(result_df.columns)}, expected {list(expected_df.columns)}"
            }
        
        if result_df.equals(expected_df):
            return {"passes_validation": True, "error": None}
        
        mismatches = []
        detailed_errors = []
        
        for col in result_df.columns:
            diff_mask = result_df[col].fillna('NULL') != expected_df[col].fillna('NULL')
            if diff_mask.any():
                diff_indices = diff_mask[diff_mask].index[:3].tolist()
                diff_count = diff_mask.sum()
                mismatches.append(f"{col}: {diff_count} differences")
                
                for idx in diff_indices:
                    r_val = result_df.iloc[idx][col]
                    e_val = expected_df.iloc[idx][col]
                    detailed_errors.append(f"Row {idx} {col}: got {r_val}, expected {e_val}")
        
        error_msg = f"Data mismatches: {', '.join(mismatches[:3])}"
        if detailed_errors:
            error_msg += f" | Examples: {'; '.join(detailed_errors[:3])}"
        
        return {"passes_validation": False, "error": error_msg}
            
    except Exception as e:
        return {"passes_validation": False, "error": f"Validation error: {e}"}


def calculate_parser_score(result_df: pd.DataFrame, expected_df: pd.DataFrame) -> float:
    """Calculate parser accuracy score out of 100"""
    
    total_score = 0
    
    # Shape accuracy (10 points)
    if result_df.shape == expected_df.shape:
        total_score += 10
    else:
        ratio = min(len(result_df), len(expected_df)) / max(len(result_df), len(expected_df))
        total_score += 10 * ratio
    
    # Column accuracy (10 points)
    if list(result_df.columns) == list(expected_df.columns):
        total_score += 10
    
    # Data accuracy (80 points)
    min_rows = min(len(result_df), len(expected_df))
    if min_rows > 0:
        correct_rows = 0
        
        for i in range(min_rows):
            row_score = 0
            gen_row = result_df.iloc[i]
            exp_row = expected_df.iloc[i]
            
            # Date (20%)
            if gen_row['Date'] == exp_row['Date']:
                row_score += 0.2
            
            # Description (20%)
            if gen_row['Description'] == exp_row['Description']:
                row_score += 0.2
            
            # Debit (30%)
            if pd.isna(gen_row['Debit Amt']) and pd.isna(exp_row['Debit Amt']):
                row_score += 0.3
            elif not pd.isna(gen_row['Debit Amt']) and not pd.isna(exp_row['Debit Amt']):
                if abs(gen_row['Debit Amt'] - exp_row['Debit Amt']) < 0.01:
                    row_score += 0.3
            
            # Credit (30%)
            if pd.isna(gen_row['Credit Amt']) and pd.isna(exp_row['Credit Amt']):
                row_score += 0.3
            elif not pd.isna(gen_row['Credit Amt']) and not pd.isna(exp_row['Credit Amt']):
                if abs(gen_row['Credit Amt'] - exp_row['Credit Amt']) < 0.01:
                    row_score += 0.3
            
            correct_rows += row_score
        
        data_score = 80 * correct_rows / min_rows
        total_score += data_score
    
    return min(100.0, total_score)
