import pandas as pd
import re

def load_data(file_path):
    """
    Load data from CSV or Excel file.
    For CSV, tries utf-8 then gbk encoding.
    """
    if file_path.endswith('.csv'):
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding='gbk')
    elif file_path.endswith(('.xls', '.xlsx')):
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

def clean_footprint(footprint_str):
    """
    Clean footprint string.
    If starts with R or C followed by digits (e.g., R0603), remove first char.
    Otherwise return as is.
    """
    if not isinstance(footprint_str, str):
        return str(footprint_str) if footprint_str is not None else ""
    
    # Check for R or C followed by digits
    if re.match(r'^[RC]\d+', footprint_str):
        return footprint_str[1:]
    return footprint_str

def clean_value(value_str):
    """
    Clean value string.
    Remove suffixes like _1%, _10%, etc.
    """
    if not isinstance(value_str, str):
        return str(value_str) if value_str is not None else ""
    
    # Remove _1%, _10% etc.
    return re.sub(r'_\d+%$', '', value_str)
