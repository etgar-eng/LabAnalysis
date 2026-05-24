"""
Example script showing the CORRECT way to extract images from PDFs

The issue: extract_images_with_page_numbers() doesn't actually extract image bytes,
only metadata. Use extract_images_hybrid_method() instead!
"""

from image_extractor import extract_images_with_page_numbers, extract_images_hybrid_method

pdf_path = 'element/Chirelson_33_TelAviv_05_09_2025.pdf'

print("=" * 70)
print("WRONG METHOD: extract_images_with_page_numbers()")
print("=" * 70)
# This DOESN'T work for saving images - only gets metadata
img_wrong = extract_images_with_page_numbers(pdf_path)
print(f"Extracted {len(img_wrong)} images (metadata only)")
if img_wrong:
    print(f"\nTrying to save first image...")
    result = img_wrong[0].save_image('a.png')
    print(f"Result: {result}")
    print(f"Image data size: {len(img_wrong[0].image_data)} bytes")

print("\n" + "=" * 70)
print("CORRECT METHOD: extract_images_hybrid_method()")
print("=" * 70)
# This DOES work - extracts actual image data
img_correct = extract_images_hybrid_method(pdf_path)
print(f"Extracted {len(img_correct)} images (with actual data)")
if img_correct:
    print(f"\nImage info: {img_correct[0]}")
    print(f"Image data size: {len(img_correct[0].image_data)} bytes")
    print(f"Image format: {img_correct[0].image_format}")
    
    print(f"\nSaving first image...")
    result = img_correct[0].save_image('a.png')
    if result:
        print(f"✓ Successfully saved to: {result}")
    else:
        print("✗ Failed to save image")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("Always use: extract_images_hybrid_method()")
print("Don't use:  extract_images_with_page_numbers() for saving images")
print("=" * 70)
