# PDF Image Extraction Guide

## Problem Summary

When using `extract_images_with_page_numbers()`, you get this error:
```
Error saving image: cannot identify image file <_io.BytesIO object at 0x...>
```

## Root Cause

The `extract_images_with_page_numbers()` function uses only **pdfplumber**, which provides image **metadata** (position, size) but NOT the actual image **bytes**. The image_data field is empty (`b""`), so PIL can't open it.

## Solution

Use `extract_images_hybrid_method()` instead, which uses **PyMuPDF (fitz)** to extract actual image data.

## Correct Usage

### ✅ CORRECT - Extract with actual data

```python
from image_extractor import extract_images_hybrid_method

# This extracts actual image bytes
img = extract_images_hybrid_method('element/Chirelson_33_TelAviv_05_09_2025.pdf')
print(img)  # [PDFImageInfo(page=1, index=3, size=118.08x66.12)]

# Now you can save the image
img[0].save_image('a.png')  # ✅ Works!
```

### ❌ WRONG - Extract metadata only

```python
from image_extractor import extract_images_with_page_numbers

# This only extracts metadata, NOT image bytes
img = extract_images_with_page_numbers('element/Chirelson_33_TelAviv_05_09_2025.pdf')
print(img)  # [PDFImageInfo(page=1, index=3, size=118.08x66.12)]

# This will FAIL because image_data is empty
img[0].save_image('a.png')  # ❌ Error!
```

## Complete Working Example

```python
from image_extractor import extract_images_hybrid_method, print_image_summary

# Extract images with actual data
pdf_path = 'element/Chirelson_33_TelAviv_05_09_2025.pdf'
images = extract_images_hybrid_method(pdf_path)

# Show summary
print_image_summary(images)

# Save each image
for i, img_info in enumerate(images):
    filename = f'extracted_image_{i}.png'
    result = img_info.save_image(filename)
    if result:
        print(f"Saved: {result}")

# Display image in matplotlib
images[0].show_image()

# Get PIL Image object
pil_img = images[0].get_pil_image()
if pil_img:
    print(f"Image mode: {pil_img.mode}, Size: {pil_img.size}")
```

## Method Comparison

| Feature | `extract_images_with_page_numbers()` | `extract_images_hybrid_method()` |
|---------|-------------------------------------|----------------------------------|
| Library | pdfplumber only | pdfplumber + PyMuPDF |
| Image Data | ❌ Empty (b"") | ✅ Actual bytes |
| Can Save | ❌ No | ✅ Yes |
| Can Display | ❌ No | ✅ Yes |
| Use Case | Metadata/counting only | Full image extraction |

## Updated Error Handling

The `PDFImageInfo` class now provides helpful error messages:

```python
# If you accidentally use the wrong method:
img = extract_images_with_page_numbers('file.pdf')
img[0].save_image('test.png')

# New error message:
# Error saving image: No image data available.
# Solution: Use extract_images_hybrid_method() instead of extract_images_with_page_numbers().
```

## Quick Reference

```python
# Basic extraction
images = extract_images_hybrid_method('myfile.pdf')

# Save single image
images[0].save_image('output.png')

# Get PIL Image
pil_img = images[0].get_pil_image()

# Display with matplotlib
images[0].show_image()

# Get as numpy array
arr = images[0].get_numpy_array()

# Filter by size
large_images = extract_images_hybrid_method('file.pdf', min_width=100, min_height=100)
```

## Dependencies

Make sure you have:
- `pymupdf` (PyMuPDF) - for actual image extraction
- `pdfplumber` - for PDF structure
- `Pillow` (PIL) - for image handling

Install with:
```bash
pip install pymupdf pdfplumber Pillow
```
