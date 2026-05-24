import sys
import re
import json
import logging
import os
from pathlib import Path
from typing import Optional

import PyPDF2
import pandas as pd

from logging_config import setup_logging

logger = setup_logging(
    log_level=logging.INFO,
    log_file="lab_analysis.log"
)

# ---------------------------------------------------------------------------
# Unit conversion
# ---------------------------------------------------------------------------

# (source_unit, target_unit) → multiplication factor
_UNIT_CONVERSIONS: dict[tuple[str, str], float] = {
    ("mg/L",  "µg/L"): 1000.0,
    ("µg/L",  "mg/L"): 0.001,
    ("ug/L",  "µg/L"): 1.0,
    ("mg/l",  "mg/L"): 1.0,
    ("ug/l",  "µg/L"): 1.0,
    ("ppb",   "µg/L"): 1.0,
    ("ppm",   "mg/L"): 1.0,
}


def conversion_factor(source_unit: str, target_unit: str) -> float:
    """Return the factor to multiply a value in source_unit to get target_unit."""
    if source_unit == target_unit:
        return 1.0
    return _UNIT_CONVERSIONS.get((source_unit, target_unit), 1.0)


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def fix_hebrew_rtl(text) -> str:
    """Reverse every Hebrew word that camelot extracted in RTL order.

    camelot reads PDF text streams left-to-right, so Hebrew words appear
    reversed (e.g. 'ןדיס' instead of 'סידן').
    This reverses only Hebrew segments; ASCII and digits are untouched.
    """
    if pd.isna(text):
        return str(text)
    return re.sub(r'[\u0590-\u05FF]+', lambda m: m.group()[::-1], str(text))


def letters_only(text: str) -> str:
    """Keep only Hebrew and ASCII letters – strip digits, punctuation, spaces."""
    return re.sub(r'[^a-zA-Z\u0590-\u05FF]', '', str(text))


def extract_numeric(value) -> Optional[float]:
    """Return the first number found in value, or None."""
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r'[\d,]+\.?\d*', str(value))
    if m:
        try:
            return float(m.group().replace(',', ''))
        except ValueError:
            pass
    return None


def is_numeric(value) -> bool:
    """True if value contains a parseable number."""
    return extract_numeric(value) is not None


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

def get_page_count(pdf_path: str) -> int:
    """Return the number of pages in a PDF file."""
    try:
        with open(pdf_path, 'rb') as fh:
            return len(PyPDF2.PdfReader(fh).pages)
    except FileNotFoundError as exc:
        logger.error("PDF not found: %s", exc)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Row filtering
# ---------------------------------------------------------------------------

_UNITS_RE = re.compile(
    r'mg/[lL]|µg/[lL]|ug/[lL]|mmol/[lL]|[Cc]elsius|NTU|mV|mS/cm|µS/cm|cm|g/[lL]',
    re.IGNORECASE,
)


def filter_unit_rows(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Keep only rows that contain a measurement unit in at least one cell."""
    mask = df.astype(str).apply(
        lambda col: col.str.contains(_UNITS_RE, na=False)
    ).any(axis=1)

    if not mask.any():
        logger.warning("No rows with measurement units found")
        return None

    return df[mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Lab-specific column extraction
# ---------------------------------------------------------------------------
#
# Bactochem camelot output (5 columns, all pages):
#   col 0 → units      e.g. "mg/L"
#   col 1 → limit      e.g. "X≤ 0.005" or ""
#   col 2 → value      e.g. "0.060", "<0.010", "Not Detected"
#   col 3 → note       e.g. "1/", "2/"
#   col 4 → test name  Hebrew (RTL-reversed) + English symbol
#
# Normalised output columns: ['test', 'value', 'units']


def _bactochem_clean_table(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Normalise one camelot table from a Bactochem page."""
    df = filter_unit_rows(df)
    if df is None:
        return None

    ncols = len(df.columns)

    if ncols == 5:
        out = df.iloc[:, [4, 2, 0]].copy()
    elif ncols == 8:
        out = df.iloc[:, [7, 5, 3]].copy()
    elif ncols == 3:
        out = df.iloc[:, [2, 1, 0]].copy()
    else:
        logger.warning("Bactochem: unexpected %d columns – skipping table", ncols)
        return None

    out.columns = ['test', 'value', 'units']

    # Fix RTL-reversed Hebrew words
    out['test'] = out['test'].apply(fix_hebrew_rtl)
    # Strip everything except letters (Hebrew + ASCII) for clean matching
    out['test'] = out['test'].apply(letters_only)

    # Keep "Not Detected" as-is; strip < > from numeric values
    def _clean_value(x):
        if pd.isna(x):
            return x
        s = str(x).strip()
        if s.lower() == 'not detected':
            return 'Not Detected'
        return re.sub(r'[<>]', '', s).strip()

    out['value'] = out['value'].apply(_clean_value)

    return out.dropna(how='all').reset_index(drop=True)


def _als_clean_table(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Normalise one camelot table from an ALS page."""
    df = filter_unit_rows(df)
    if df is None:
        return None

    ncols = len(df.columns)

    if ncols in (4, 5, 6):
        out = df.iloc[:, [0, 3, 4]].copy()
    elif ncols == 8:
        out = df.iloc[:, [0, 4, 5]].copy()
    elif ncols == 10:
        out = df.iloc[:, [0, 3, 4]].copy()
    else:
        logger.warning("ALS: unexpected %d columns – skipping table", ncols)
        return None

    out.columns = ['test', 'units', 'value']
    out['value'] = out['value'].str.replace(r'[<>]', '', regex=True)
    out['units'] = out['units'].str.replace('(cid:181)g/L', 'µg/L', regex=False)
    return out.dropna(how='all').reset_index(drop=True)


def _element_clean_tables(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Combine and normalise camelot tables from an Element report."""
    df = pd.concat(dfs, ignore_index=True)
    df.drop(columns=[2, 4], axis=1, inplace=True, errors='ignore')
    df.columns = ['test', 'value', 'units']
    df['value'] = df['value'].str.extract(r'<?([\d.]+)')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df['test'] = (
        df['test']
        .str.replace('#', '', regex=False)
        .str.replace(r'[()]', '', regex=True)
    )
    df['units'] = (
        df['units']
        .str.replace('ug/l', 'µg/L', regex=False)
        .str.replace('mg/l', 'mg/L', regex=False)
    )
    return df


def _aminolab_clean_tables(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Combine and normalise camelot tables from an Aminolab report."""
    rows: list[pd.DataFrame] = []

    for i, raw in enumerate(dfs):
        try:
            if i <= 2:
                df = filter_unit_rows(raw)
                if df is None or df.empty:
                    continue
                df = df.drop(columns=[2], axis=1, errors='ignore')
                df.columns = ['value', 'units', 'test']
                df = df[['test', 'value', 'units']]
            else:
                raw = raw.drop(columns=[col for col in [1, 3] if col in raw.columns], errors='ignore')
                raw = raw.assign(units='ppb')
                raw.columns = ['test', 'value', 'units']
                df = raw

            rows.append(df)

        except Exception as exc:
            logger.error("Aminolab: error processing table %d: %s", i, exc)

    if not rows:
        return pd.DataFrame(columns=['test', 'value', 'units'])

    result = pd.concat(rows, ignore_index=True)
    result['test'] = result['test'].apply(fix_hebrew_rtl).apply(letters_only)
    result['value'] = result['value'].str.extract(r'<?([\d.]+)')
    result['value'] = pd.to_numeric(result['value'], errors='coerce')
    result['test'] = result['test'].str.replace('#', '', regex=False)
    result['units'] = (
        result['units']
        .str.replace('¥g/L', 'µg/L', regex=False)
        .str.extract(
            r'(mg/L|µg/L|mg/l|ug/l|cfu/100mL|ppm|ppb|NTU)', expand=False
        )
    )
    return result.dropna(how='all').reset_index(drop=True)


# ---------------------------------------------------------------------------
# Main extractor class
# ---------------------------------------------------------------------------


class Extractor:
    """Loads params.json and format.csv for a given lab.

    Public interface
    ----------------
    extruct_col_from_lab(dfs, lab) → pd.DataFrame
        Combines raw camelot DataFrames into a normalised ['test','value','units'] table.

    search_for_value(df, test_name) → float | str | None
        Looks up a format.csv test name in the normalised table and returns
        the unit-converted value.
    """

    def __init__(self, args=None):
        self.args = args
        main_dir = Path(os.getcwd())
        lab_dir = main_dir / self.args.lab

        with open(lab_dir / 'params.json', 'r', encoding='utf-8') as fh:
            self.params: dict = json.load(fh)

        self.df_format: pd.DataFrame = pd.read_csv(main_dir / 'format.csv')

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    @staticmethod
    def extruct_col_from_lab(dfs: list[pd.DataFrame], lab: str) -> pd.DataFrame:
        """Convert raw camelot tables into a unified normalised table."""

        if lab == 'Bactochem':
            cleaned = [_bactochem_clean_table(raw) for raw in dfs]
            valid = [df for df in cleaned if df is not None and not df.empty]
            if not valid:
                return pd.DataFrame(columns=['test', 'value', 'units'])
            result = pd.concat(valid, ignore_index=True)
            logger.info("Bactochem: %d total rows extracted", len(result))
            return result

        if lab == 'ALS':
            cleaned = [_als_clean_table(raw) for raw in dfs]
            valid = [df for df in cleaned if df is not None and not df.empty]
            if not valid:
                return pd.DataFrame(columns=['test', 'units', 'value'])
            result = pd.concat(valid, ignore_index=True)
            logger.info("ALS: %d total rows extracted", len(result))
            return result

        if lab == 'Element':
            return _element_clean_tables(dfs)

        if lab == 'Aminolab':
            return _aminolab_clean_tables(dfs)

        raise ValueError(f"Unknown lab: {lab!r}")

    # ------------------------------------------------------------------
    # Value lookup
    # ------------------------------------------------------------------

    def search_for_value(self, df: pd.DataFrame, test_name: str):
        """Return the value for test_name from the normalised DataFrame.

        Lookup logic
        ------------
        1. Read params.json entry for test_name.
           Entry format: {"unit": <target_unit>, "values": [<source_unit>, <synonym>]}
        2. Search for synonym in the 'test' column (case-insensitive contains).
        3. Multiply found value by conversion_factor(source_unit, target_unit).
        4. Return numeric result, 'Not Detected', or None.
        """
        param = self.params.get(test_name, {})
        mapping = param.get('values', [])

        if not mapping or len(mapping) < 2:
            return None

        source_unit: str = mapping[0]   # unit the PDF lab uses
        synonym: str = mapping[1]       # text fragment to match in 'test' column
        target_unit: str = param.get('unit', source_unit)
        factor = conversion_factor(source_unit, target_unit)

        found = self._find_value(df, synonym)

        if found is None:
            return None

        if isinstance(found, str) and 'not detected' in found.lower():
            return 'Not Detected'

        numeric = extract_numeric(found)
        if numeric is None:
            logger.warning("Cannot parse value %r for '%s'", found, test_name)
            return None

        return numeric * factor

    def _find_value(self, df: pd.DataFrame, synonym: str):
        """Search synonym in every text column; return the associated value."""

        # Primary search: 'test' column
        if 'test' in df.columns:
            mask = df['test'].astype(str).str.contains(synonym, case=False, na=False)
            if mask.any():
                row = df[mask].iloc[0]
                val_col = 'value' if 'value' in df.columns else df.columns[-1]
                return row[val_col]

        # Fallback: search every text column, look for value in adjacent columns
        for col in df.select_dtypes(include='object').columns:
            mask = df[col].astype(str).str.contains(synonym, case=False, na=False)
            if mask.any():
                row_idx = df[mask].index[0]
                for vcol in df.columns:
                    if vcol == col:
                        continue
                    candidate = df.loc[row_idx, vcol]
                    candidate_str = str(candidate).strip().lower()
                    if is_numeric(candidate) or candidate_str == 'not detected':
                        return candidate

        return None
