from typing import Any
import PyPDF2
import pandas as pd
import json
import os
from pathlib import Path
import re
import logging
from logging_config import setup_logging, suppress_warnings
# Setup logging first thing
logger = setup_logging(
    log_level=logging.INFO,  # Change to DEBUG for more verbose
    log_file="lab_analysis.log"  # Optional
)


def read_file(df: pd.DataFrame) -> pd.DataFrame | None:
    """
    Filters DataFrame to keep only rows containing measurement units.

    Args:
        df: Input DataFrame to search

    Returns:
        DataFrame with only rows containing units, or None if no units found
    """
    print(df)

    # Define units to search for (case-insensitive)
    units_pattern = r"mg/[lL]|µg/[lL]|ug/[lL]|mmol/[lL]|[Cc]elsius|NTU|mV|mS/cm|µS/cm|cm|g/[lL]"

    # Search for units across all columns
    mask = df.astype(str).apply(
        lambda x: x.str.contains(units_pattern, na=False, regex=True, case=False)
    ).any(axis=1)

    if mask.any():
        # Return only rows where mask is True
        return df[mask].reset_index(drop=True)
    else:
        print(f"Warning: No rows containing measurement units found")
        print(f"Searched for pattern: {units_pattern}")
        return None

def _coef(dict_unit, pdf_unit):
    lst = [('mg/L', 'µg/L', 1000),
           ('µg/L', 'mg/L', 0.001)]

    for check in lst:
        lst_1, lst2 = check[0], check[1]

        if lst_1 == dict_unit and lst2 == pdf_unit:
            return  check[2]
        else:
            continue
    return  1


def _extract_number(value):
    """Extract numeric value from string"""
    import re
    if isinstance(value, (int, float)):
        return float(value)

    # Remove common non-numeric characters and extract number
    clean_value = re.sub(r'[^\d.,]', '', str(value))
    clean_value = clean_value.replace(',', '')  # Remove thousand separators

    try:
        return float(clean_value)
    except ValueError:
        return 0.0


def _is_numeric(value):
    """Check if a value is numeric or contains a number"""
    if value is None:
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        # Try to extract number from string
        import re
        if isinstance(value, str):
            number_match = re.search(r'[\d,]+\.?\d*', str(value))
            return number_match is not None
        return False

def fix_hebrew_text_advanced(text):
    if pd.isna(text):
        return text

    # Hebrew Unicode range
    hebrew_pattern = r'[\u0590-\u05FF]+'

    def reverse_hebrew_match(match):
        return match.group()[::-1]

    # Find and reverse only Hebrew text segments
    fixed_text = re.sub(hebrew_pattern, reverse_hebrew_match, str(text))
    return fixed_text



def get_page_count(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        return len(pdf_reader.pages)


class Extractor:

    def __init__(self, args=None):
        self.args = args
        main_dir = Path(os.getcwd())
        child_dir  = main_dir / self.args.lab
        with open(child_dir / 'params.json', 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        self.df_format = pd.read_csv(main_dir /'format.csv')

    @staticmethod
    def extruct_col_from_lab(dfs: list[pd.DataFrame], lab) -> pd.DataFrame:
        if lab == 'ALS':

            # Create empty DataFrame with proper structure
            df_all = pd.DataFrame(columns=['test', 'units', 'value'])

            for df_file in dfs:
                try:
                    df = read_file(df_file)  # Your file reading function

                    if len(df.columns) in [4, 5, 6]:
                        df = df.iloc[:, [0, 3, 4]]

                    elif len(df.columns) == 8:
                        df = df.iloc[:, [0, 4, 5]]


                    elif len(df.columns) == 10:
                        df = df.iloc[:, [0, 3, 4]]

                    # Check if DataFrame is empty
                    if df.empty:
                        print(f"Warning: {df_file} is empty, skipping...")
                        continue

                    # Set standardized column names
                    df.columns = ['test', 'units', 'value']

                    # Concatenate to main DataFrame
                    df_all = pd.concat([df_all, df], ignore_index=True)


                    print(f"Processed {df_file}: {df.shape[0]} rows added")


                except Exception as e:
                    logger.error(f"Error processing file: {str(e)}")  # Don't print the df_file
                    continue

            # Clean up: Remove any completely empty rows
            df_all = df_all.dropna(how='all').reset_index(drop=True)

            # Remove '<' and '>' symbols and extract only numeric values
            df_all['value'] = df_all['value'].str.replace(r'[<>]', '', regex=True)

            # replace (cid:181)g/L -> with µg/L
            df_all['units'] = df_all['units'].str.replace('(cid:181)g/L', 'µg/L', regex=False)

            print(f"\nFinal combined DataFrame shape: {df_all.shape}")
            print(f"Total rows: {len(df_all)}")
            return df_all

        if lab == 'Bactochem':

            # Create empty DataFrame with proper structure
            df_all = pd.DataFrame(columns=['units','value','test'])

            for i, df_file in enumerate(dfs):
                try:
                    df = read_file(df_file)  # Your file reading function

                    # Check if DataFrame is empty
                    if df.empty or len(df.columns) == 6:
                        print(f"Warning: {df_file} is empty, skipping...")
                        continue

                    # Use positional indexing based on column count
                    if len(df.columns) == 8:
                        # Keep columns at positions 0, 1, 4
                        df = df.iloc[:, [3, 5, 7]]

                    if len(df.columns) == 5:
                        # Keep columns at positions 0, 1, 4
                        df = df.iloc[:, [0, 2, 4]]

                    elif len(df.columns) == 3:
                        # Keep columns at positions 0, 5, 8
                        df = df.iloc[:, [0, 1, 2]]
                    else:
                        print(f"Warning: {df_file} has {len(df.columns)} columns (expected 5 or 9), skipping...")
                        continue

                        # Set standardized column names
                    df.columns = ['units','value','test']

                    # Concatenate to main DataFrame
                    df_all = pd.concat([df_all, df], ignore_index=True)

                    print(f"Processed {df_file}: {df.shape[0]} rows added")

                except Exception as e:
                    logger.error(f"Error processing file: {str(e)}")  # Don't print the df_file
                    continue

            #  specifically, targets Hebrew characters and reverses only
            #  those portions while leaving English text and numbers intact
            df_all['test'] = df_all['test'].apply(fix_hebrew_text_advanced)
            # Keep English and Hebrew letters
            df_all['test'] = df_all['test'].str.replace(r'[^a-zA-Z\u0590-\u05FF]', '', regex=True)
            # Clean up: Remove any completely empty rows
            df_all = df_all.dropna(how='all').reset_index(drop=True)

            df_all['value'] = df_all['value'].apply(
                lambda x: x if x == "Not Detected" else re.sub(r'[<>]', '', str(x)) if pd.notna(x) else x
            )

            print(f"\nFinal combined DataFrame shape: {df_all.shape}")
            print(f"Total rows: {len(df_all)}")
            return df_all

        if lab == 'Element':

            df_all = pd.concat(dfs)
            df_all.drop(columns=[2, 4], axis=1, inplace=True)
            df_all.columns = ['test','value','units']
            # Extract numeric value (without '<' symbol)
            df_all['value'] = df_all['value'].str.extract(r'<?(\d+\.?\d*)')

            df_all['value'] = pd.to_numeric(df_all['value'], errors='coerce')
            df_all['test'] = df_all['test'].str.replace('#', '', regex=False).str.replace(
                '(', '', regex=False).str.replace(
                ')', '', regex=False)
            df_all['test'] = df_all['test'].str.replace('#', '', regex=False)

            # replace ug/L -> with µg/L
            #     and mg/l -> with mg/L
            df_all['units'] = df_all['units'].str.replace('ug/l', 'µg/L', regex=False)
            df_all['units'] = df_all['units'].str.replace('mg/l', 'mg/L', regex=False)

            return df_all

        if lab == 'Aminolab':

            # Create empty DataFrame with proper structure
            df_all = pd.DataFrame(columns=['value', 'units', 'test'])

            for i, df_file in enumerate(dfs):
                try:
                    if i <= 2:
                        df = read_file(df_file)  # Your file reading function
                        df.drop(columns=[2], axis=1, inplace=True)
                        # Set standardized column names
                        df.columns = ['value', 'units', 'test']
                        # Check if DataFrame is empty
                        if df.empty:
                            logger.warning(f"DataFrame at index {i} is empty, skipping...")
                            continue
                        else:
                            logger.info(f"Processed DataFrame {i}: {df.shape[0]} rows, {df.shape[1]} columns")

                    elif i >= 3:
                        df_file.drop(columns=[1], axis=1, inplace=True)
                        df_file = df_file.assign(units='ppb')
                        df_file.columns = ['test', 'value', 'units']
                        df = df_file[['test', 'units', 'value']]
                        logger.info(
                            f"Processed DataFrame {i}: {df.shape[0]} rows added with 'ppb' units")

                    # Concatenate to main DataFrame
                    df_all = pd.concat([df_all, df], ignore_index=True)
                    df_all = df_all[['test','value','units']]

                except Exception as e:
                    logger.error(f"Error processing DataFrame at index {i}: {str(e)}")
                    continue

            # Data cleaning steps
            logger.info("Starting data cleaning...")

            # specifically, targets Hebrew characters and reverses only
            # those portions while leaving English text and numbers intact
            df_all['test'] = df_all['test'].apply(fix_hebrew_text_advanced)
            logger.debug("Applied Hebrew text fixing")

            # Keep English and Hebrew letters
            df_all['test'] = df_all['test'].str.replace(r'[^a-zA-Z\u0590-\u05FF]', '', regex=True)
            logger.debug("Cleaned test column - kept only letters")

            # Extract numeric value (without '<' symbol)
            df_all['value'] = df_all['value'].str.extract(r'<?(\d+\.?\d*)')
            df_all['value'] = pd.to_numeric(df_all['value'], errors='coerce')
            logger.debug("Extracted and converted numeric values")

            # Clean test column symbols
            df_all['test'] = df_all['test'].str.replace('#', '', regex=False)
            logger.debug("Removed # symbols from test column")

            # Fix units encoding
            df_all['units'] = df_all['units'].str.replace('¥g/L', 'µg/L', regex=False)
            logger.debug("Fixed units encoding")

            # Extract only the valid units
            df_all['units'] = df_all['units'].str.extract(r'(mg/L|µg/L|mg/l|ug/l|cfu/100mL|ppm|ppb|NTU)', expand=False)
            logger.debug("Extracted valid units only")

            logger.info(f"Data processing completed. Final DataFrame shape: {df_all.shape}")
            logger.info(
                f"Non-null values - test: {df_all['test'].notna().sum()}, value: {df_all['value'].notna().sum()}, units: {df_all['units'].notna().sum()}")

            return df_all


    def search_for_value(self, df, i):
        try:
            # Get parameter info from the JSON data
            param_info = self.data.get(i, {})
            values = param_info.get('values', [])

            # Check if values array has content
            if not values or len(values) < 2:
                return None

            dict_unit = values[0]  # First element is the unit from JSON
            synonym = values[1]  # Second element is the parameter name
            pdf_unit = param_info.get('unit')  # Original unit from JSON structure

            # Calculate conversion coefficient
            c = _coef(dict_unit, pdf_unit)

            # Search for the parameter in the dataframe
            # Try different column names that might contain the parameter
            possible_columns = ['test', 'parameter', 'analyte', 'compound', 'substance']
            found_value = None

            for col_name in possible_columns:
                if col_name in df.columns:
                    # Look for exact match first
                    mask = df[col_name].str.contains(synonym, case=False, na=False)
                    if mask.any():
                        matching_rows = df[mask]
                        if not matching_rows.empty and 'value' in df.columns:
                            found_value = matching_rows['value'].iloc[0]
                            break

            # If not found, try broader search across all text columns
            if found_value is None:
                for col in df.columns:
                    if df[col].dtype == 'object':  # Text columns
                        mask = df[col].astype(str).str.contains(synonym, case=False, na=False)
                        if mask.any():
                            # Look for value in adjacent columns
                            row_idx = df[mask].index[0]
                            for val_col in df.columns:
                                if val_col != col:
                                    potential_val = df.loc[row_idx, val_col]
                                    if _is_numeric(potential_val):
                                        found_value = potential_val
                                        break
                            if found_value is not None:
                                break

            if found_value is not None:
                # CHECK FOR 'Not detected' BEFORE numeric processing
                if isinstance(found_value, str) and 'not detected' in found_value.lower():
                    return 'Not detected'

                # Convert to float if it's a string
                if isinstance(found_value, str):
                    found_value = _extract_number(found_value)

                result = float(found_value) * c
                return result
            else:
                return 'Not detected'

        except (TypeError, KeyError, IndexError, ValueError) as e:
            print(f"Error processing parameter {i}: {e}")
            return None
