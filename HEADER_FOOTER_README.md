# 📄 PDF Header & Footer Extraction - Complete Solution

## 🎯 Overview

Complete toolkit for extracting **headers**, **footers**, **text**, and **images** from PDF files. Perfect for lab reports, documents with logos, and multi-page PDFs.

## ✨ Features

### Text Extraction
- ✅ Extract header text from top of pages
- ✅ Extract footer text from bottom of pages
- ✅ Smart detection of repeating patterns
- ✅ Keyword-based search
- ✅ Page number extraction
- ✅ Support for Hebrew & English

### Image Extraction
- ✅ Extract logos from headers
- ✅ Extract signatures/images from footers
- ✅ Save images in original format (PNG, JPG, etc.)
- ✅ Get image dimensions and positions
- ✅ Batch processing support

## 📦 What's Included

| File | Description |
|------|-------------|
| `footer_extractor.py` | Main module with all extraction functions |
| `HEADER_FOOTER_QUICKSTART.md` | 30-second quick start guide |
| `HEADER_FOOTER_GUIDE.md` | Complete documentation with examples |
| `test_header_footer.py` | Comprehensive test suite |

## 🚀 Quick Start

### Installation

```bash
pip install pdfplumber pymupdf pillow
```

### Basic Usage

```python
from footer_extractor import HeaderFooterExtractor

# Initialize
extractor = HeaderFooterExtractor('myfile.pdf')

# Extract text
headers = extractor.extract_header_smart()
footers = extractor.extract_footer_smart()

print(headers[1])  # Page 1 header
print(footers[1])  # Page 1 footer

# Extract images
header_images = extractor.extract_header_images_pymupdf()
footer_images = extractor.extract_footer_images_pymupdf()

# Save images
extractor.save_header_footer_images(header_images, 'output/logos', 'logo')
```

## 📊 Real-World Examples

### Example 1: Extract Lab Logo

```python
extractor = HeaderFooterExtractor('lab_report.pdf', header_margin_percent=20)
images = extractor.extract_header_images_pymupdf(page_numbers=[1])

if images.get(1):
    logo = images[1][0]
    with open(f'logo.{logo["ext"]}', 'wb') as f:
        f.write(logo['image_data'])
```

### Example 2: Identify Lab from Header/Footer

```python
extractor = HeaderFooterExtractor('report.pdf')
headers = extractor.extract_header_smart(page_numbers=[1])
footers = extractor.extract_footer_smart(page_numbers=[1])

text = ' '.join([*headers.values(), *footers.values()]).lower()

if 'als' in text:
    lab = 'ALS'
elif 'element' in text:
    lab = 'Element'
```

### Example 3: Batch Extract All Logos

```python
from pathlib import Path

for pdf_file in Path('reports').glob('*.pdf'):
    extractor = HeaderFooterExtractor(str(pdf_file))
    images = extractor.extract_header_images_pymupdf(page_numbers=[1])
    extractor.save_header_footer_images(images, 'logos', pdf_file.stem)
```

### Example 4: Extract Contact Information

```python
import re

extractor = HeaderFooterExtractor('report.pdf')
footers = extractor.extract_footer_smart()
text = '\n'.join(footers.values())

emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
phones = re.findall(r'\+?\d[\d\s\-\(\)]{8,}', text)
websites = re.findall(r'www\.[\w\.-]+\.\w+', text)
```

## 🧪 Testing

Run the test suite to verify everything works:

```bash
# Run all tests
python test_header_footer.py

# Run specific test
python test_header_footer.py 1  # Basic extraction
python test_header_footer.py 3  # Image extraction
python test_header_footer.py 6  # Lab identification
```

### Test Results Format

```
█████████████████████████████████████████████████
HEADER & FOOTER EXTRACTION TEST SUITE
█████████████████████████████████████████████████

TEST 1: Basic Header & Footer Text Extraction
=========================================
✓ Header (Page 1): Element Materials Technology...
✓ Footer (Page 1): Page 1 of 5...

TEST 3: Image Extraction from Headers & Footers
=========================================
✓ Saved 1 header image(s) to: test_output/headers
✓ Saved 2 footer image(s) to: test_output/footers

✓ PASS: Basic Extraction
✓ PASS: Image Extraction
6/6 tests passed 🎉
```

## 📚 API Reference

### Main Class

```python
HeaderFooterExtractor(
    pdf_path: str,
    header_margin_percent: float = 15,  # Top X% of page
    footer_margin_percent: float = 15   # Bottom X% of page
)
```

### Text Extraction Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `extract_header_smart()` | Smart header detection | `Dict[int, str]` |
| `extract_footer_smart()` | Smart footer detection | `Dict[int, str]` |
| `extract_header_pdfplumber()` | Using pdfplumber | `Dict[int, str]` |
| `extract_footer_pymupdf()` | Using PyMuPDF | `Dict[int, str]` |
| `extract_header_by_keyword(keywords)` | Keyword search | `Dict[int, str]` |
| `extract_footer_by_keyword(keywords)` | Keyword search | `Dict[int, str]` |

### Image Extraction Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `extract_header_images_pymupdf()` | Extract header images | `Dict[int, List[Dict]]` |
| `extract_footer_images_pymupdf()` | Extract footer images | `Dict[int, List[Dict]]` |
| `save_header_footer_images(images, dir, prefix)` | Save images | `None` |

### Utility Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `extract_page_numbers_from_header()` | Parse page numbers | `Dict[int, Optional[int]]` |
| `extract_page_numbers_from_footer()` | Parse page numbers | `Dict[int, Optional[int]]` |

### Helper Functions

```python
# Quick extraction functions
extract_header_simple(pdf_path, page_number=1) -> str
extract_footer_simple(pdf_path, page_number=1) -> str
extract_all_headers(pdf_path, method='smart') -> Dict[int, str]
extract_all_footers(pdf_path, method='smart') -> Dict[int, str]

# Display functions
print_header_summary(headers, max_length=100)
print_footer_summary(footers, max_length=100)
print_image_summary(images, region_type="header")
```

## 🔧 Configuration Options

### Adjust Detection Areas

```python
# Larger header (top 25% of page)
extractor = HeaderFooterExtractor('file.pdf', header_margin_percent=25)

# Smaller footer (bottom 8% of page)
extractor = HeaderFooterExtractor('file.pdf', footer_margin_percent=8)
```

### Extract from Specific Pages

```python
# Only pages 1-3
headers = extractor.extract_header_smart(page_numbers=[1, 2, 3])

# Only first page
images = extractor.extract_header_images_pymupdf(page_numbers=[1])
```

### Choose Extraction Method

```python
# Smart detection (recommended)
headers = extractor.extract_header_smart()

# PDFPlumber (good for text-based PDFs)
headers = extractor.extract_header_pdfplumber()

# PyMuPDF (good for complex PDFs)
headers = extractor.extract_header_pymupdf()

# Keyword search (targeted extraction)
headers = extractor.extract_header_by_keyword(['company', 'logo'])
```

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| **No images found** | Increase `header_margin_percent` to 20-30% |
| **Too much content** | Decrease margin percentages to 8-10% |
| **Wrong content extracted** | Use keyword-based extraction |
| **Empty results** | Try different method (pdfplumber vs pymupdf) |
| **Mixed languages** | Use `smart` method (handles Hebrew/English) |

## 💻 Integration with Main Pipeline

```python
# Add to your main.py
from footer_extractor import HeaderFooterExtractor

class PdfLabAnalysisReader:
    def __init__(self, args=None):
        # ... existing code ...
        
        # Initialize extractor
        self.hf_extractor = HeaderFooterExtractor(self.pdf)
        
        # Extract headers/footers
        self.headers = self.hf_extractor.extract_header_smart()
        self.footers = self.hf_extractor.extract_footer_smart()
        
        # Extract lab logo from first page
        header_images = self.hf_extractor.extract_header_images_pymupdf([1])
        if header_images.get(1):
            logo = header_images[1][0]
            logo_path = f'logos/{self.lab}_logo.{logo["ext"]}'
            with open(logo_path, 'wb') as f:
                f.write(logo['image_data'])
            logger.info(f"Logo saved: {logo_path}")
    
    def get_page_header(self, page_num):
        return self.headers.get(page_num, "")
    
    def get_page_footer(self, page_num):
        return self.footers.get(page_num, "")
```

## 📖 Documentation

- **Quick Start**: `HEADER_FOOTER_QUICKSTART.md` - Get started in 30 seconds
- **Full Guide**: `HEADER_FOOTER_GUIDE.md` - Complete documentation with examples
- **API Docs**: See docstrings in `footer_extractor.py`

## 🎯 Use Cases

1. **Lab Reports**: Extract lab names, logos, and contact info
2. **Document Processing**: Identify document types from headers
3. **Quality Control**: Verify headers/footers are consistent
4. **Data Extraction**: Parse page numbers, dates, reference numbers
5. **Batch Processing**: Extract logos from multiple PDFs
6. **Report Generation**: Include header/footer info in summaries

## 🤝 Example Workflow

```python
# 1. Extract all information
extractor = HeaderFooterExtractor('lab_report.pdf')
headers = extractor.extract_header_smart()
footers = extractor.extract_footer_smart()
images = extractor.extract_header_images_pymupdf()

# 2. Identify lab
text = ' '.join([*headers.values(), *footers.values()])
lab = identify_lab(text)

# 3. Extract contact info
contact_info = extract_contact_info(footers)

# 4. Save logo
if images.get(1):
    extractor.save_header_footer_images(images, f'logos/{lab}', 'logo')

# 5. Log results
logger.info(f"Processed {lab} report with {len(headers)} pages")
```

## 🌟 Key Benefits

- ✅ **No manual configuration** - Smart detection works automatically
- ✅ **Handles multiple formats** - Works with various PDF structures
- ✅ **Batch processing ready** - Process hundreds of files
- ✅ **Language support** - Hebrew, English, and mixed content
- ✅ **Error resilient** - Graceful handling of edge cases
- ✅ **Well tested** - Comprehensive test suite included

## 📝 Notes

- The module uses both **pdfplumber** and **PyMuPDF** for maximum compatibility
- **Smart methods** are recommended for best results
- **Image extraction** requires PyMuPDF (already included)
- All methods support extracting from specific pages to improve performance
- Results are returned as dictionaries mapping page numbers to content

## 🚀 Next Steps

1. Run the test suite: `python test_header_footer.py`
2. Try on your PDFs: `python footer_extractor.py`
3. Read the quick start: `HEADER_FOOTER_QUICKSTART.md`
4. Explore examples: `HEADER_FOOTER_GUIDE.md`
5. Integrate into your pipeline: See integration section above

---

**Questions or issues?** Check the full documentation in `HEADER_FOOTER_GUIDE.md`
