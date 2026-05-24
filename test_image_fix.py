"""
Quick test to verify the image extraction fix works
Run this to test: python test_image_fix.py
"""

from image_extractor import extract_images_hybrid_method, print_image_summary

def test_extraction():
    pdf_path = 'element/Chirelson_33_TelAviv_05_09_2025.pdf'
    
    print("=" * 70)
    print("Testing Image Extraction Fix")
    print("=" * 70)
    
    try:
        # Extract images
        print(f"\n1. Extracting images from: {pdf_path}")
        images = extract_images_hybrid_method(pdf_path)
        
        if not images:
            print("   ⚠ No images found in PDF")
            return False
        
        print(f"   ✓ Found {len(images)} images")
        
        # Show summary
        print("\n2. Image Summary:")
        print_image_summary(images)
        
        # Test saving the first image
        print("\n3. Testing save functionality:")
        result = images[0].save_image('test_output.png')
        
        if result:
            print(f"   ✓ SUCCESS! Image saved to: {result}")
            
            # Test PIL image retrieval
            print("\n4. Testing PIL image retrieval:")
            pil_img = images[0].get_pil_image()
            if pil_img:
                print(f"   ✓ PIL Image: mode={pil_img.mode}, size={pil_img.size}")
            else:
                print("   ✗ Failed to get PIL image")
                return False
            
            print("\n" + "=" * 70)
            print("✓ ALL TESTS PASSED!")
            print("=" * 70)
            return True
        else:
            print("   ✗ Failed to save image")
            return False
            
    except FileNotFoundError:
        print(f"\n✗ ERROR: PDF file not found: {pdf_path}")
        print("   Please update the pdf_path variable in this script")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_extraction()
    exit(0 if success else 1)
