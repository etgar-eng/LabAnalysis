# Lab Analysis – PDF to Water Authority Excel Report

Automated pipeline that reads chemical analysis PDF reports from certified Israeli laboratories, maps the results to the **Israel Water Authority reporting format**, checks compliance against **Israel Drinking Water Regulations 2013** (תקנות בריאות העם, תשע"ג), and produces a styled Excel report.

---

## Supported Laboratories

| Lab | Language | Format |
|-----|----------|--------|
| **Bactochem** (בקטוכם) | Hebrew / English | ICP-MS + VOC (5-page) |
| **Aminolab** (אמינולאב) | Hebrew | ICP-MS + VOC (8-page) |
| **ALS** | English | ICP-MS + VOC (multi-page) |
| **Element** | English | ICP-MS |

---

## Project Structure

```
lab_analysis/
│
├── main.py            # CLI orchestrator – runs the full pipeline
├── functions.py       # Table extraction & unit conversion (Extractor class)
├── regulations.py     # Regulation limits database (תקנות 2013)
├── report.py          # Styled Excel report generator (ReportBuilder)
├── identifier.py      # CNN logo classifier – detects lab from PDF images
├── image_extractor.py # PDF image extraction (PyMuPDF + pdfplumber)
├── logging_config.py  # Logging setup
├── app.py             # Streamlit web UI
│
├── format.csv                  # Water Authority parameter list (94 tests)
├── lab_logo_classifier.h5      # Trained CNN model for lab identification
│
├── Bactochem/
│   ├── params.json             # Parameter mapping for Bactochem
│   └── *.pdf                   # Lab report PDFs
├── Aminolab/
│   ├── params.json
│   └── *.pdf
├── ALS/
│   ├── params.json
│   └── *.pdf
└── Element/
    ├── params.json
    └── *.pdf
```

---

## How It Works

```
PDF file
   │
   ├─▶  identifier.py   ──  CNN (lab_logo_classifier.h5)
   │         │                detects which lab issued the report
   │         ▼
   ├─▶  image_extractor.py  extracts images from PDF pages
   │
   ├─▶  camelot            reads tables from PDF pages
   │         │
   ▼         ▼
functions.py / Extractor
   │    ┌─────────────────────────────────────┐
   │    │  fix_hebrew_rtl()                   │
   │    │  filter_unit_rows()                 │
   │    │  _bactochem_clean_table()  etc.     │
   │    └─────────────────────────────────────┘
   │         │
   │    Normalised DataFrame: [test | value | units]
   │         │
   ├─▶  params.json      maps lab synonyms → format.csv test names
   │         │
   ├─▶  regulations.py   looks up limit for each test
   │         │
   ▼         ▼
report.py / ReportBuilder
        Styled Excel with 2 sheets:
        1. "דוח רשות המים"  – full parameter table
        2. "סיכום תקינות"  – compliance summary
```

---

## Installation

### System requirements

```bash
# Ubuntu / Debian
sudo apt-get install ghostscript libgl1 libglib2.0-0

# macOS
brew install ghostscript
```

### Python packages

Dependencies are declared in `pyproject.toml` and managed with [uv](https://docs.astral.sh/uv/).

```bash
# Install uv (if not already installed)
pip install uv

# Sync the environment (creates .venv automatically)
uv sync
```

All subsequent commands should be run with `uv run` so they use the managed environment.

---

## Usage

### Command line

```bash
# Minimal
uv run main.py --lab Bactochem --input bactochem/report.pdf

# With metadata
uv run main.py \
    --lab     Aminolab \
    --input   aminolab/big_petah_tikva.pdf \
    --output  petah_tikva_results \
    --site    "ביג פתח תקוה" \
    --date    "10/05/2026" \
    --time    "09:30"

# PDF containing pages from multiple labs (auto-detect)
uv run main.py --lab Bactochem --input mixed.pdf --multi true
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `--lab` | ✅ | `Bactochem`, `Aminolab`, `ALS`, or `Element` |
| `--input` | ✅ | Path to PDF file |
| `--output` | — | Output filename prefix (default: lab name) |
| `--multi` | — | `true` if the PDF contains pages from multiple labs |
| `--site` | — | Sampling site (appears in report header) |
| `--date` | — | Sampling date |
| `--time` | — | Sampling time |

**Output files:**

| File | Contents |
|------|----------|
| `df_summary.xlsx` | Raw extracted tables, one sheet per check |
| `{output}.xlsx` | Flat mapped values (legacy format) |
| `{output}_Check1.xlsx` | Full styled Water Authority report |

### Streamlit web UI

```bash
uv run streamlit run app.py
# Open http://localhost:8501
```

Upload a PDF, select the lab, click **Run Analysis**. Download the raw data or the formatted report from the Downloads tab.

---

## Docker

```bash
# Build image
docker build -t lab-analysis .

# Run (mount a folder for PDFs and output)
docker run -p 8501:8501 \
    -v $(pwd)/data:/app/data \
    lab-analysis
```

The container exposes the Streamlit UI on port 8501.

---

## Configuration – params.json

Each lab folder contains a `params.json` mapping Water Authority test names to lab-specific synonyms and units.

```json
{
  "CALCIUM AS CA": {
    "unit":   "mg/L",
    "values": ["mg/L", "סידןCa"]
  },
  "ALUMINUM (Al)": {
    "unit":   "µg/L",
    "values": ["mg/L", "אלומיניוםAl"]
  },
  "BENZENE": {
    "unit":   "µg/L",
    "values": ["mg/L", "Benzene"]
  }
}
```

| Field | Meaning |
|-------|---------|
| `unit` | Target unit (Water Authority format) |
| `values[0]` | Unit used by the lab in the PDF |
| `values[1]` | Text fragment matched in the extracted `test` column |

Unit conversion is applied automatically when `values[0]` differs from `unit` (e.g. mg/L → µg/L ×1000).

---

## Regulation Limits (regulations.py)

Limits are sourced from **תקנות בריאות העם (איכותם התברואית של מי שתייה), תשע"ג-2013**.

```python
from regulations import get_limit, compliance_status

get_limit("ARSENIC AS AS")             # Limit(10, "µg/L", "≤10 µg/L")
compliance_status("ZINC AS ZN", 7400)  # "חריג!"
compliance_status("BENZENE", "not detected")  # "תקין"
```

**Status values:**

| Status | Meaning |
|--------|---------|
| `תקין` | Within limit |
| `חריג!` | Exceeds regulatory limit |
| `בגבול גילוי` | Within limit but above 90% of it — monitor |
| `לא ניתן לאמת` | LOQ may be above the regulatory limit |
| `לא נבדק` | Parameter not found in the report |

---

## Report Output

### Sheet 1 — "דוח רשות המים"

| Column | Content |
|--------|---------|
| פרמטר (רשות המים) | Water Authority test name |
| פרמטר (מעבדה) | Lab-specific name from params.json |
| תוצאה (מקורית) | Value as reported in PDF |
| יחידה (מקורית) | Unit as reported in PDF |
| תוצאה (רש"מ) | Converted value |
| יחידות (רש"מ) | Target unit |
| גבול תקנות 2013 | Regulatory limit |
| סטטוס | Compliance status (colour-coded) |

Row colours: green = compliant, yellow = near limit or LOQ concern, red = exceedance.

### Sheet 2 — "סיכום תקינות"

Parameters grouped by severity:

- 🔴 Exceedances — requires immediate action
- 🟡 Near-limit values / LOQ concerns — requires monitoring
- ✅ Compliant values that have a defined regulatory limit

---

## Hebrew Text Handling

Lab PDFs store Hebrew text in left-to-right byte order inside the PDF stream. `camelot` reads this as-is, so Hebrew words appear reversed (e.g. `ןדיס` instead of `סידן`).

`functions.fix_hebrew_rtl()` reverses only Hebrew Unicode segments while leaving ASCII, digits, and chemical symbols untouched. `functions.letters_only()` then strips punctuation and spaces to produce a clean key for synonym matching.

---

## Adding a New Lab

1. Create a folder and add a PDF:
   ```bash
   mkdir NewLab
   cp report.pdf NewLab/
   ```

2. Create `NewLab/params.json` with a mapping entry for each parameter the lab reports.

3. Add the lab config to `_LAB_CONFIG` in `main.py`:
   ```python
   "NewLab": {
       "tables_area": (["x1,y1,x2,y2"], ...),
       "pages":       ["1", "2", ...],
       "row_tol":     [7, 12],   # optional
   }
   ```

4. Add a branch for the new lab in `Extractor.extruct_col_from_lab()` in `functions.py`.

5. Collect logo images in `Logo/lab_new/` and retrain the classifier in `identifier.py`.

---

## Known Limitations

| Parameter | Issue |
|-----------|-------|
| Vinyl chloride | Regulation limit 0.5 µg/L; typical laboratory LOQ = 1 µg/L. A "Not Detected" result does not guarantee compliance — a dedicated low-LOQ method is required. |
| EDB (ethylene dibromide) | Regulation limit 0.05 µg/L; typical LOQ = 1 µg/L. Same issue. |
| 1,4-Dioxane (Aminolab) | Reported in ppm (LOQ = 5 ppm = 5000 µg/L). A specific µg/L method is needed for meaningful monitoring. |
| Bicarbonate (Aminolab) | Reported as mg/L CaCO₃ — converted to mg/L HCO₃ by ×1.22. |
| Mercury | Not included in Bactochem's standard ICP scan — must be requested separately. |
| Multi-lab PDFs | Logo classification accuracy depends on the quantity and quality of training images in `Logo/`. |

---

## License

Internal use — Geo Danya Engineering Ltd.
