# PDF Header & Footer Extraction Guide

## Overview

The updated `footer_extractor.py` module now extracts **both headers and footers** including:
- Text content
- Images/logos
- Metadata (page numbers, dates, etc.)

## Quick Start

### Extract Header & Footer Text

```python
from footer_extractor import HeaderFooterExtractor

# Initialize extractor
extractor = HeaderFooterExtractor('myfile.pdf', 
                                  header_margin_percent=15,
                                  footer_margin_percent=15)

# Extract headers from all pages
headers = extractor.extract_header_smart()
print(headers[1])  # Header from page 1

# Extract footers from all pages  
footers = extractor.extract_footer_smart()
print(footers[1])  # Footer from page 1
```

### Extract Header & Footer Images

```python
# Extract images from headers
header_images = extractor.extract_header_images_pymupdf()

# Extract images from footers
footer_images = extractor.extract_footer_images_pymupdf()

# Save extracted images to disk
extractor.save_header_footer_images(header_images, 'output/headers', 'header')
extractor.save_header_footer_images(footer_images, 'output/footers', 'footer')
```

## Complete Example: Lab Report Processing

```python
from footer_extractor import HeaderFooterExtractor, print_header_summary, print_footer_summary, print_image_summary
from pathlib import Path

# Initialize
pdf_path = 'element/Chirelson_33_TelAviv_05_09_2025.pdf'
extractor = HeaderFooterExtractor(pdf_path, 
                                  header_margin_percent=12,  # Top 12% of page
                                  footer_margin_percent=10)  # Bottom 10% of page

# Extract text
headers = extractor.extract_header_smart()
footers = extractor.extract_footer_smart()

# Display summaries
print("="*80)
print_header_summary(headers, max_length=100)
print("="*80)
print_footer_summary(footers, max_length=100)

# Extract images
header_images = extractor.extract_header_images_pymupdf()
footer_images = extractor.extract_footer_images_pymupdf()

# Display image summaries
print_image_summary(header_images, "header")
print_image_summary(footer_images, "footer")

# Save images
output_dir = Path('extracted_images')
extractor.save_header_footer_images(header_images, output_dir / 'headers', 'logo')
extractor.save_header_footer_images(footer_images, output_dir / 'footers', 'footer')

print(f"\nImages saved to: {output_dir}")
```

## Available Methods

### Text Extraction

| Method | Description | Best For |
|--------|-------------|----------|
| `extract_header_pdfplumber()` | Uses pdfplumber | Standard PDFs with clear text |
| `extract_footer_pdfplumber()` | Uses pdfplumber | Standard PDFs with clear text |
| `extract_header_pymupdf()` | Uses PyMuPDF | Complex PDFs with images/fonts |
| `extract_footer_pymupdf()` | Uses PyMuPDF | Complex PDFs with images/fonts |
| `extract_header_smart()` | Auto-detection | Recommended - finds repeating patterns |
| `extract_footer_smart()` | Auto-detection | Recommended - finds repeating patterns |
| `extract_header_by_keyword()` | Keyword search | When you know specific header keywords |
| `extract_footer_by_keyword()` | Keyword search | When you know specific footer keywords |

### Image Extraction

| Method | Description |
|--------|-------------|
| `extract_header_images_pymupdf()` | Extract all images from header region |
| `extract_footer_images_pymupdf()` | Extract all images from footer region |
| `save_header_footer_images()` | Save extracted images to disk |

### Utility Methods

| Method | Description |
|--------|-------------|
| `extract_page_numbers_from_header()` | Parse page numbers from header text |
| `extract_page_numbers_from_footer()` | Parse page numbers from footer text |
| `print_header_summary()` | Display header extraction results |
| `print_footer_summary()` | Display footer extraction results |
| `print_image_summary()` | Display image extraction results |

## Practical Examples

### Example 1: Extract Lab Logo from Header

```python
from footer_extractor import HeaderFooterExtractor
from PIL import Image
import io

# Extract header images from first page
extractor = HeaderFooterExtractor('lab_report.pdf', header_margin_percent=20)
header_images = extractor.extract_header_images_pymupdf(page_numbers=[1])

# Get first image (likely the logo)
if header_images.get(1):
    logo_info = header_images[1][0]  # First image on page 1
    
    # Save to file
    with open(f'lab_logo.{logo_info["ext"]}', 'wb') as f:
        f.write(logo_info['image_data'])
    
    # Or open with PIL
    logo_image = Image.open(io.BytesIO(logo_info['image_data']))
    logo_image.show()
    
    print(f"Logo size: {logo_info['width']}x{logo_info['height']}")
    print(f"Logo position: {logo_info['bbox']}")
```

### Example 2: Identify Lab by Header/Footer Content

```python
from footer_extractor import HeaderFooterExtractor

def identify_lab(pdf_path):
    extractor = HeaderFooterExtractor(pdf_path)
    
    # Extract headers and footers from first 3 pages
    headers = extractor.extract_header_smart(page_numbers=[1, 2, 3])
    footers = extractor.extract_footer_smart(page_numbers=[1, 2, 3])
    
    # Combine all text
    all_text = ' '.join([*headers.values(), *footers.values()]).lower()
    
    # Check for lab signatures
    if 'als' in all_text or 'alsglobal' in all_text:
        return 'ALS'
    elif 'element' in all_text or 'element materials' in all_text:
        return 'Element'
    elif 'bactochem' in all_text or 'בקטוכם' in all_text:
        return 'Bactochem'
    elif 'aminolab' in all_text or 'אמינולאב' in all_text:
        return 'Aminolab'
    else:
        return 'Unknown'

lab = identify_lab('test_report.pdf')
print(f"Identified lab: {lab}")
```

### Example 3: Extract Contact Information

```python
import re
from footer_extractor import HeaderFooterExtractor

def extract_contact_info(pdf_path):
    extractor = HeaderFooterExtractor(pdf_path)
    
    # Extract headers and footers
    headers = extractor.extract_header_smart()
    footers = extractor.extract_footer_smart()
    
    # Combine all text
    all_text = '\n'.join([*headers.values(), *footers.values()])
    
    # Extract various contact details
    contact_info = {
        'emails': re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', all_text),
        'phones': re.findall(r'\+?\d[\d\s\-\(\)]{8,}', all_text),
        'websites': re.findall(r'www\.[\w\.-]+\.\w+', all_text),
        'addresses': []  # Could add address extraction logic
    }
    
    # Deduplicate
    contact_info['emails'] = list(set(contact_info['emails']))
    contact_info['phones'] = list(set(contact_info['phones']))
    contact_info['websites'] = list(set(contact_info['websites']))
    
    return contact_info

contacts = extract_contact_info('lab_report.pdf')
print("Contact Information:")
for key, values in contacts.items():
    if values:
        print(f"\n{key.upper()}:")
        for val in values:
            print(f"  - {val}")
```

### Example 4: Batch Extract Logos from Multiple PDFs

```python
from footer_extractor import HeaderFooterExtractor
from pathlib import Path

def batch_extract_logos(pdf_dir, output_dir):
    """Extract logos from all PDFs in directory"""
    pdf_dir = Path(pdf_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(pdf_dir.glob('*.pdf'))
    
    for pdf_file in pdf_files:
        try:
            print(f"\nProcessing: {pdf_file.name}")
            extractor = HeaderFooterExtractor(str(pdf_file), header_margin_percent=20)
            
            # Extract header images from first page only
            header_images = extractor.extract_header_images_pymupdf(page_numbers=[1])
            
            if header_images.get(1):
                # Save all header images
                for idx, img_info in enumerate(header_images[1]):
                    filename = f"{pdf_file.stem}_logo_{idx}.{img_info['ext']}"
                    filepath = output_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(img_info['image_data'])
                    
                    print(f"  Saved: {filename}")
            else:
                print(f"  No logo found")
                
        except Exception as e:
            print(f"  Error: {e}")

# Extract logos from all PDFs
batch_extract_logos('ALS', 'extracted_logos/ALS')
batch_extract_logos('element', 'extracted_logos/Element')
batch_extract_logos('bactochem', 'extracted_logos/Bactochem')
```

### Example 5: Compare Headers Across Pages

```python
from footer_extractor import HeaderFooterExtractor

def find_consistent_header(pdf_path):
    """Find header content that appears on all pages"""
    extractor = HeaderFooterExtractor(pdf_path)
    headers = extractor.extract_header_smart()
    
    if not headers:
        return None
    
    # Split all headers into lines
    all_header_lines = {}
    for page, header in headers.items():
        lines = [line.strip() for line in header.split('\n') if line.strip()]
        for line in lines:
            if line not in all_header_lines:
                all_header_lines[line] = []
            all_header_lines[line].append(page)
    
    # Find lines that appear on ALL pages
    total_pages = len(headers)
    consistent_lines = [
        line for line, pages in all_header_lines.items()
        if len(pages) == total_pages
    ]
    
    return '\n'.join(consistent_lines) if consistent_lines else None

consistent_header = find_consistent_header('lab_report.pdf')
print("Consistent header across all pages:")
print(consistent_header)
```

## Integration with Main Analysis Pipeline

### Add to `main.py`:

```python
# In your PdfLabAnalysisReader class

from footer_extractor import HeaderFooterExtractor

class PdfLabAnalysisReader:
    def __init__(self, args=None):
        # ... existing code ...
        
        # Add header/footer extraction
        self.hf_extractor = HeaderFooterExtractor(self.pdf)
        self.headers = self.hf_extractor.extract_header_smart()
        self.footers = self.hf_extractor.extract_footer_smart()
        
        # Extract logos/images
        self.header_images = self.hf_extractor.extract_header_images_pymupdf([1])
        
        # Save logo if found
        if self.header_images.get(1):
            logo_data = self.header_images[1][0]['image_data']
            logo_ext = self.header_images[1][0]['ext']
            logo_path = f'output/logo_{self.lab}.{logo_ext}'
            with open(logo_path, 'wb') as f:
                f.write(logo_data)
            logger.info(f"Lab logo saved to: {logo_path}")
        
        logger.info(f"Extracted headers from {len(self.headers)} pages")
        logger.info(f"Extracted footers from {len(self.footers)} pages")
    
    def get_page_header(self, page_num):
        """Get header for specific page"""
        return self.headers.get(page_num, "")
    
    def get_page_footer(self, page_num):
        """Get footer for specific page"""
        return self.footers.get(page_num, "")
```

## Advanced Configuration

### Adjust Detection Areas

```python
# Larger header area (top 25% of page)
extractor = HeaderFooterExtractor('myfile.pdf', 
                                  header_margin_percent=25,
                                  footer_margin_percent=10)

# Smaller footer area (bottom 8% of page)
extractor = HeaderFooterExtractor('myfile.pdf',
                                  header_margin_percent=15,
                                  footer_margin_percent=8)
```

### Extract from Specific Pages Only

```python
# Extract from pages 1-5 only
headers = extractor.extract_header_smart(page_numbers=[1, 2, 3, 4, 5])
footers = extractor.extract_footer_smart(page_numbers=[1, 2, 3, 4, 5])

# Extract images from first page only
header_images = extractor.extract_header_images_pymupdf(page_numbers=[1])
```

## Troubleshooting

### Issue: No Images Found

**Solution**: Increase the margin percentage or check if images are embedded differently

```python
# Try larger header area
extractor = HeaderFooterExtractor('myfile.pdf', header_margin_percent=30)
header_images = extractor.extract_header_images_pymupdf()
```

### Issue: Too Much Content Extracted

**Solution**: Reduce margin percentage or use keyword-based extraction

```python
# Smaller header area
extractor = HeaderFooterExtractor('myfile.pdf', header_margin_percent=10)

# Or use keywords
headers = extractor.extract_header_by_keyword(['company', 'logo', 'title'])
```

### Issue: Mixed Languages (Hebrew/English)

**Solution**: Use smart detection which handles both

```python
headers = extractor.extract_header_smart()  # Handles mixed content
footers = extractor.extract_footer_smart()  # Handles mixed content
```

## Performance Tips

1. **Extract from specific pages** when possible (faster)
2. **Use smart methods** for consistent results
3. **Cache results** if processing same PDF multiple times
4. **Adjust margins** based on your PDF layout

## API Reference Summary

```python
HeaderFooterExtractor(
    pdf_path: str,
    header_margin_percent: float = 15,  # Top X% of page
    footer_margin_percent: float = 15   # Bottom X% of page
)

# Text extraction methods
.extract_header_pdfplumber(page_numbers=None) -> Dict[int, str]
.extract_footer_pdfplumber(page_numbers=None) -> Dict[int, str]
.extract_header_pymupdf(page_numbers=None) -> Dict[int, str]
.extract_footer_pymupdf(page_numbers=None) -> Dict[int, str]
.extract_header_smart(page_numbers=None) -> Dict[int, str]
.extract_footer_smart(page_numbers=None) -> Dict[int, str]
.extract_header_by_keyword(keywords, page_numbers=None) -> Dict[int, str]
.extract_footer_by_keyword(keywords, page_numbers=None) -> Dict[int, str]

# Image extraction methods
.extract_header_images_pymupdf(page_numbers=None) -> Dict[int, List[Dict]]
.extract_footer_images_pymupdf(page_numbers=None) -> Dict[int, List[Dict]]
.save_header_footer_images(images, output_dir, prefix) -> None

# Utility methods
.extract_page_numbers_from_header(headers) -> Dict[int, Optional[int]]
.extract_page_numbers_from_footer(footers) -> Dict[int, Optional[int]]
```

## Next Steps

- See example usage in the `__main__` section of `footer_extractor.py`
- Run test script: `python test_header_footer.py`
- Integrate with your existing pipeline
