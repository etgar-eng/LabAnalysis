# Header & Footer Extraction - Quick Start

## 🚀 Quick Start (30 seconds)

```python
from footer_extractor import HeaderFooterExtractor

# Initialize
extractor = HeaderFooterExtractor('myfile.pdf')

# Extract text
headers = extractor.extract_header_smart()  # All headers
footers = extractor.extract_footer_smart()  # All footers

print(headers[1])  # Header from page 1
print(footers[1])  # Footer from page 1

# Extract images (logos, signatures, etc.)
header_images = extractor.extract_header_images_pymupdf()
footer_images = extractor.extract_footer_images_pymupdf()

# Save images
extractor.save_header_footer_images(header_images, 'output/headers', 'logo')
extractor.save_header_footer_images(footer_images, 'output/footers', 'footer')
```

## 📊 What's New

| Feature | Description |
|---------|-------------|
| ✅ **Header Text** | Extract text from top of pages |
| ✅ **Footer Text** | Extract text from bottom of pages |
| ✅ **Header Images** | Extract logos/images from headers |
| ✅ **Footer Images** | Extract signatures/images from footers |
| ✅ **Smart Detection** | Auto-detect repeating patterns |
| ✅ **Keyword Search** | Find headers/footers by keywords |
| ✅ **Page Numbers** | Parse page numbers from text |

## 🎯 Common Use Cases

### 1. Extract Lab Logo

```python
from footer_extractor import HeaderFooterExtractor

extractor = HeaderFooterExtractor('lab_report.pdf', header_margin_percent=20)
header_images = extractor.extract_header_images_pymupdf(page_numbers=[1])

if header_images.get(1):
    logo = header_images[1][0]
    with open(f'logo.{logo["ext"]}', 'wb') as f:
        f.write(logo['image_data'])
    print(f"Logo saved: {logo['width']}x{logo['height']}")
```

### 2. Identify Lab

```python
extractor = HeaderFooterExtractor('report.pdf')
headers = extractor.extract_header_smart(page_numbers=[1])
footers = extractor.extract_footer_smart(page_numbers=[1])

text = ' '.join([*headers.values(), *footers.values()]).lower()

if 'als' in text:
    lab = 'ALS'
elif 'element' in text:
    lab = 'Element'
elif 'bactochem' in text:
    lab = 'Bactochem'

print(f"Identified: {lab}")
```

### 3. Extract Contact Info

```python
import re

extractor = HeaderFooterExtractor('report.pdf')
footers = extractor.extract_footer_smart()

all_text = '\n'.join(footers.values())

emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', all_text)
phones = re.findall(r'\+?\d[\d\s\-\(\)]{8,}', all_text)
websites = re.findall(r'www\.[\w\.-]+\.\w+', all_text)

print(f"Emails: {emails}")
print(f"Phones: {phones}")
print(f"Websites: {websites}")
```

## 🧪 Test the Code

```bash
# Run all tests
python test_header_footer.py

# Run specific test
python test_header_footer.py 3  # Image extraction test
```

## 📖 Key Methods

```python
# Text extraction
extractor.extract_header_smart()              # Recommended
extractor.extract_footer_smart()              # Recommended
extractor.extract_header_pdfplumber()         # Alternative
extractor.extract_footer_pymupdf()            # Alternative
extractor.extract_header_by_keyword(['logo']) # Search by keyword

# Image extraction
extractor.extract_header_images_pymupdf()     # Get header images
extractor.extract_footer_images_pymupdf()     # Get footer images
extractor.save_header_footer_images(...)      # Save to disk

# Utilities
extractor.extract_page_numbers_from_footer()  # Parse page numbers
```

## ⚙️ Configuration

```python
# Adjust detection areas
HeaderFooterExtractor(
    'myfile.pdf',
    header_margin_percent=20,  # Top 20% of page
    footer_margin_percent=10   # Bottom 10% of page
)

# Extract from specific pages only
headers = extractor.extract_header_smart(page_numbers=[1, 2, 3])
images = extractor.extract_header_images_pymupdf(page_numbers=[1])
```

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| No images found | Increase `header_margin_percent` or `footer_margin_percent` |
| Too much content | Decrease margin percentages |
| Wrong content | Use `extract_by_keyword()` instead |
| Empty results | Try different method: pdfplumber vs pymupdf |

## 📚 Full Documentation

- **Complete Guide**: See `HEADER_FOOTER_GUIDE.md`
- **API Reference**: See `footer_extractor.py` docstrings
- **Examples**: Run `python footer_extractor.py`

## 💡 Integration Example

```python
# Add to your main.py
from footer_extractor import HeaderFooterExtractor

class PdfLabAnalysisReader:
    def __init__(self, args=None):
        # ... existing code ...
        
        # Extract headers/footers
        self.hf_extractor = HeaderFooterExtractor(self.pdf)
        self.headers = self.hf_extractor.extract_header_smart()
        self.footers = self.hf_extractor.extract_footer_smart()
        
        # Extract and save lab logo
        header_images = self.hf_extractor.extract_header_images_pymupdf([1])
        if header_images.get(1):
            logo = header_images[1][0]
            with open(f'logos/{self.lab}_logo.{logo["ext"]}', 'wb') as f:
                f.write(logo['image_data'])
```

## 🎉 Quick Win

Extract all lab logos in your directory:

```python
from footer_extractor import HeaderFooterExtractor
from pathlib import Path

for pdf_file in Path('ALS').glob('*.pdf'):
    extractor = HeaderFooterExtractor(str(pdf_file), header_margin_percent=20)
    images = extractor.extract_header_images_pymupdf(page_numbers=[1])
    extractor.save_header_footer_images(images, 'logos/ALS', pdf_file.stem)
    print(f"✓ {pdf_file.name}")
```

---

**Questions?** Check `HEADER_FOOTER_GUIDE.md` for detailed documentation.
