# PDF Footer Extraction Guide

## Overview

The `footer_extractor.py` module provides multiple methods to extract footer text from PDF files, supporting various use cases and PDF structures.

## Installation

Ensure you have the required libraries:
```bash
pip install pdfplumber pymupdf
```

## Quick Start

### Simple Single Page Extraction

```python
from footer_extractor import extract_footer_simple

# Extract footer from page 1
footer = extract_footer_simple('myfile.pdf', page_number=1)
print(footer)
```

### Extract All Pages

```python
from footer_extractor import extract_all_footers, print_footer_summary

# Extract from all pages
footers = extract_all_footers('myfile.pdf', method='smart')
print_footer_summary(footers)
```

## Extraction Methods

### 1. **PDFPlumber Method** (Default)
Best for text-based PDFs with clear structure.

```python
from footer_extractor import FooterExtractor

extractor = FooterExtractor('myfile.pdf', footer_margin_percent=15)
footers = extractor.extract_footer_pdfplumber()

# For specific pages only
footers = extractor.extract_footer_pdfplumber(page_numbers=[1, 2, 3])
```

### 2. **PyMuPDF Method**
More robust for complex PDFs, better handling of images and fonts.

```python
footers = extractor.extract_footer_pymupdf()
```

### 3. **Smart Detection Method** (Recommended)
Automatically detects repeating footer patterns across pages.

```python
footers = extractor.extract_footer_smart()
```

### 4. **Keyword-Based Method**
Search for specific keywords in footer area.

```python
keywords = ['page', 'דף', 'copyright', '©', 'footer']
footers = extractor.extract_footer_by_keyword(keywords)
```

## Advanced Usage

### Adjust Footer Detection Area

```python
# Increase footer area to 20% of page height
extractor = FooterExtractor('myfile.pdf', footer_margin_percent=20)
footers = extractor.extract_footer_pdfplumber()
```

### Extract Page Numbers from Footers

```python
extractor = FooterExtractor('myfile.pdf')
footers = extractor.extract_footer_smart()

# Extract page numbers
page_numbers = extractor.extract_page_numbers_from_footer(footers)

for page, num in page_numbers.items():
    print(f"Page {page} footer shows: {num}")
```

### Custom Search Height

```python
# Search in bottom 30% of page
footers = extractor.extract_footer_by_keyword(
    keywords=['copyright'],
    search_height_percent=30
)
```

## Complete Examples

### Example 1: Lab Report Footer Extraction

```python
from footer_extractor import FooterExtractor, print_footer_summary

# Initialize extractor
pdf_path = 'ALS/Arba_artsot_Tel_aviv_29_01_2025.pdf'
extractor = FooterExtractor(pdf_path, footer_margin_percent=12)

# Extract footers from all pages
footers = extractor.extract_footer_smart()

# Display summary
print_footer_summary(footers, max_length=150)

# Save to file
with open('footers_output.txt', 'w', encoding='utf-8') as f:
    for page, footer in sorted(footers.items()):
        f.write(f"=== Page {page} ===\n")
        f.write(f"{footer}\n\n")
```

### Example 2: Extract Common Footer Template

```python
from footer_extractor import FooterExtractor

extractor = FooterExtractor('myfile.pdf')
all_footers = extractor.extract_footer_pdfplumber()

# Find common footer text (appears on most pages)
from collections import Counter

footer_lines = []
for footer in all_footers.values():
    if footer:
        footer_lines.extend([line.strip() for line in footer.split('\n')])

# Most common lines
common_lines = Counter(footer_lines).most_common(10)
print("Most common footer lines:")
for line, count in common_lines:
    print(f"{count:3d}x: {line}")
```

### Example 3: Remove Footers from DataFrame

```python
from footer_extractor import FooterExtractor
import pandas as pd
import camelot

# Extract footers
pdf_path = 'myfile.pdf'
extractor = FooterExtractor(pdf_path)
footers = extractor.extract_footer_smart()

# Extract table with camelot
tables = camelot.read_pdf(pdf_path, pages='1')
df = tables[0].df

# Remove footer text from dataframe
footer_text = footers.get(1, "")
if footer_text:
    footer_keywords = footer_text.split()[:5]  # First 5 words
    # Filter out rows containing footer keywords
    for keyword in footer_keywords:
        df = df[~df.astype(str).apply(lambda x: x.str.contains(keyword, na=False)).any(axis=1)]

print(df)
```

## Handling Different PDF Types

### Hebrew/RTL PDFs

```python
extractor = FooterExtractor('hebrew_pdf.pdf')
footers = extractor.extract_footer_pdfplumber()

# Hebrew page number pattern
import re
for page, footer in footers.items():
    match = re.search(r'דף\s+(\d+)', footer)
    if match:
        page_num = int(match.group(1))
        print(f"Page {page}: Hebrew page number = {page_num}")
```

### Multi-Lab PDFs

```python
from footer_extractor import FooterExtractor

pdf_path = 'multi_lab_report.pdf'
extractor = FooterExtractor(pdf_path)

# Extract footers to identify lab sections
footers = extractor.extract_footer_smart()

# Identify different lab sections by footer patterns
lab_sections = {}
for page, footer in footers.items():
    if 'ALS' in footer:
        lab_sections[page] = 'ALS'
    elif 'Element' in footer:
        lab_sections[page] = 'Element'
    elif 'Bactochem' in footer:
        lab_sections[page] = 'Bactochem'

print("Lab sections:")
for page, lab in sorted(lab_sections.items()):
    print(f"Page {page}: {lab}")
```

## Integration with Existing Code

### Add to Main Processing Pipeline

```python
# In your main.py

from footer_extractor import FooterExtractor

class PdfLabAnalysisReader:
    def __init__(self, args=None):
        # ... existing init code ...
        
        # Add footer extraction
        self.footer_extractor = FooterExtractor(self.pdf)
        self.footers = self.footer_extractor.extract_footer_smart()
        
        # Log footer info
        logger.info(f"Extracted footers from {len(self.footers)} pages")
    
    def get_page_footer(self, page_num):
        """Get footer for specific page"""
        return self.footers.get(page_num, "")
```

## Troubleshooting

### Footer Not Detected

**Problem:** Footer area is too small or too large

**Solution:** Adjust `footer_margin_percent`

```python
# Try larger footer area
extractor = FooterExtractor('myfile.pdf', footer_margin_percent=25)
```

### Mixed Content in Footer

**Problem:** Tables or main content included in footer

**Solution:** Use keyword-based extraction

```python
# Only extract if specific keywords present
footers = extractor.extract_footer_by_keyword(['page', 'copyright'])
```

### Empty Footers

**Problem:** PDF has image-based footers

**Solution:** Use PyMuPDF method or OCR

```python
# Try PyMuPDF
footers = extractor.extract_footer_pymupdf()

# If still empty, may need OCR (not included in this module)
```

## API Reference

### FooterExtractor Class

```python
FooterExtractor(pdf_path: str, footer_margin_percent: float = 15)
```

**Methods:**
- `extract_footer_pdfplumber(page_numbers=None)` - Extract using pdfplumber
- `extract_footer_pymupdf(page_numbers=None)` - Extract using PyMuPDF
- `extract_footer_smart(page_numbers=None)` - Smart detection method
- `extract_footer_by_keyword(keywords, page_numbers=None)` - Keyword-based
- `extract_page_numbers_from_footer(footers)` - Extract page numbers

### Utility Functions

```python
extract_footer_simple(pdf_path, page_number=1, footer_height_percent=15)
extract_all_footers(pdf_path, method='smart')
print_footer_summary(footers, max_length=100)
```

## Performance Tips

1. **Process specific pages only** when possible
2. **Use smart method** for consistent results
3. **Cache results** if processing same PDF multiple times
4. **Adjust footer_margin_percent** based on your PDF layout

## Next Steps

- See `footer_extraction_examples.py` for more examples
- Check `test_footer_extraction.py` for test cases
- Integrate with your existing lab analysis pipeline
