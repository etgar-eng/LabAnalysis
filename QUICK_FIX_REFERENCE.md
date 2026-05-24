# Quick Fix Reference Card

## 🔴 Error: "cannot identify image file"

### Your Code (BROKEN):
```python
img = extract_images_with_page_numbers('file.pdf')
img[0].save_image('a.png')  # ❌ ERROR!
```

### Fixed Code:
```python
img = extract_images_hybrid_method('file.pdf')  # ← Changed function
img[0].save_image('a.png')  # ✅ WORKS!
```

---

## 🔴 Error: "cannot unpack non-iterable NoneType object"

### Issue
Camelot crashes when PDF table area has no text

### Fix Status
✅ **Already fixed in main.py** - script now skips problematic pages and continues

### What You'll See Now
```
WARNING: No text found in table area for check 1, page 3 - skipping
```

Script continues instead of crashing.

---

## Quick Commands

### Test the fixes:
```bash
python test_image_fix.py
```

### Extract images correctly:
```python
from image_extractor import extract_images_hybrid_method

# Extract all images
images = extract_images_hybrid_method('myfile.pdf')

# Save first image
images[0].save_image('output.png')
```

### Run your main processing:
```bash
python main.py --input "yourfile.pdf"
```

---

## Function Cheat Sheet

| Task | Use This Function |
|------|------------------|
| Save/Display images | `extract_images_hybrid_method()` ✅ |
| Count images only | `extract_images_with_page_numbers()` |
| Extract tables | `camelot.read_pdf()` (now with error handling) |

---

## Need More Info?

- **Detailed guide:** See `IMAGE_EXTRACTION_GUIDE.md`
- **All changes:** See `FIXES_SUMMARY.md`
- **Examples:** See `fix_image_extraction_example.py`
