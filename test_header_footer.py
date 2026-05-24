"""
Test Script for Header & Footer Extraction
------------------------------------------
Run this to test the header/footer extraction functionality
"""

from footer_extractor import (
    HeaderFooterExtractor,
    print_header_summary,
    print_footer_summary,
    print_image_summary,
    extract_header_simple,
    extract_footer_simple
)
from pathlib import Path
import sys


def test_basic_extraction():
    """Test 1: Basic text extraction"""
    print("="*80)
    print("TEST 1: Basic Header & Footer Text Extraction")
    print("="*80)
    
    # Find a test PDF
    test_pdfs = [
        'element/Chirelson_33_TelAviv_05_09_2025.pdf',
        'ALS/Arba_artsot_Tel_aviv_29_01_2025.pdf',
        'bactochem/Ainshtein15_Tel_Aviv_13_02_2025.pdf'
    ]
    
    pdf_path = None
    for pdf in test_pdfs:
        if Path(pdf).exists():
            pdf_path = pdf
            break
    
    if not pdf_path:
        print("❌ No test PDF found. Please provide a PDF path.")
        return False
    
    print(f"\nTesting with: {pdf_path}")
    
    try:
        # Simple extraction
        header = extract_header_simple(pdf_path, page_number=1)
        footer = extract_footer_simple(pdf_path, page_number=1)
        
        print(f"\n✓ Header (Page 1):")
        print(f"  {header[:150] if header else '[Empty]'}")
        
        print(f"\n✓ Footer (Page 1):")
        print(f"  {footer[:150] if footer else '[Empty]'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_smart_extraction():
    """Test 2: Smart extraction with pattern detection"""
    print("\n" + "="*80)
    print("TEST 2: Smart Extraction (Multi-Page)")
    print("="*80)
    
    test_pdfs = [
        'element/Chirelson_33_TelAviv_05_09_2025.pdf',
        'ALS/Arba_artsot_Tel_aviv_29_01_2025.pdf'
    ]
    
    pdf_path = None
    for pdf in test_pdfs:
        if Path(pdf).exists():
            pdf_path = pdf
            break
    
    if not pdf_path:
        print("❌ No test PDF found")
        return False
    
    print(f"\nTesting with: {pdf_path}")
    
    try:
        extractor = HeaderFooterExtractor(pdf_path, 
                                          header_margin_percent=15, 
                                          footer_margin_percent=15)
        
        # Extract from first 3 pages
        print("\n--- Headers (Pages 1-3) ---")
        headers = extractor.extract_header_smart(page_numbers=[1, 2, 3])
        print_header_summary(headers, max_length=80)
        
        print("\n--- Footers (Pages 1-3) ---")
        footers = extractor.extract_footer_smart(page_numbers=[1, 2, 3])
        print_footer_summary(footers, max_length=80)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_extraction():
    """Test 3: Image extraction from headers/footers"""
    print("\n" + "="*80)
    print("TEST 3: Image Extraction from Headers & Footers")
    print("="*80)
    
    test_pdfs = [
        'element/Chirelson_33_TelAviv_05_09_2025.pdf',
        'ALS/Arba_artsot_Tel_aviv_29_01_2025.pdf',
        'bactochem/Ainshtein15_Tel_Aviv_13_02_2025.pdf'
    ]
    
    pdf_path = None
    for pdf in test_pdfs:
        if Path(pdf).exists():
            pdf_path = pdf
            break
    
    if not pdf_path:
        print("❌ No test PDF found")
        return False
    
    print(f"\nTesting with: {pdf_path}")
    
    try:
        extractor = HeaderFooterExtractor(pdf_path,
                                          header_margin_percent=20,
                                          footer_margin_percent=15)
        
        # Extract images from first 2 pages
        print("\n--- Header Images (Pages 1-2) ---")
        header_images = extractor.extract_header_images_pymupdf(page_numbers=[1, 2])
        print_image_summary(header_images, "header")
        
        total_header_imgs = sum(len(imgs) for imgs in header_images.values())
        
        print("\n--- Footer Images (Pages 1-2) ---")
        footer_images = extractor.extract_footer_images_pymupdf(page_numbers=[1, 2])
        print_image_summary(footer_images, "footer")
        
        total_footer_imgs = sum(len(imgs) for imgs in footer_images.values())
        
        # Save if images found
        if total_header_imgs > 0:
            output_dir = Path('test_output/headers')
            extractor.save_header_footer_images(header_images, output_dir, 'test_header')
            print(f"\n✓ Saved {total_header_imgs} header image(s) to: {output_dir}")
        
        if total_footer_imgs > 0:
            output_dir = Path('test_output/footers')
            extractor.save_header_footer_images(footer_images, output_dir, 'test_footer')
            print(f"✓ Saved {total_footer_imgs} footer image(s) to: {output_dir}")
        
        if total_header_imgs == 0 and total_footer_imgs == 0:
            print("\nℹ️  No images found in headers or footers")
            print("   Try adjusting header_margin_percent or footer_margin_percent")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_keyword_extraction():
    """Test 4: Keyword-based extraction"""
    print("\n" + "="*80)
    print("TEST 4: Keyword-Based Extraction")
    print("="*80)
    
    test_pdfs = [
        'element/Chirelson_33_TelAviv_05_09_2025.pdf',
        'ALS/Arba_artsot_Tel_aviv_29_01_2025.pdf'
    ]
    
    pdf_path = None
    for pdf in test_pdfs:
        if Path(pdf).exists():
            pdf_path = pdf
            break
    
    if not pdf_path:
        print("❌ No test PDF found")
        return False
    
    print(f"\nTesting with: {pdf_path}")
    
    try:
        extractor = HeaderFooterExtractor(pdf_path)
        
        # Search for common header keywords
        header_keywords = ['laboratory', 'report', 'analysis', 'document', 'company']
        print(f"\n--- Searching for header keywords: {header_keywords} ---")
        headers = extractor.extract_header_by_keyword(header_keywords, page_numbers=[1, 2, 3])
        
        found_count = len([h for h in headers.values() if h])
        print(f"Found headers with keywords on {found_count} pages")
        print_header_summary(headers, max_length=100)
        
        # Search for common footer keywords
        footer_keywords = ['page', 'דף', 'copyright', '©', 'accredited', 'iso']
        print(f"\n--- Searching for footer keywords: {footer_keywords} ---")
        footers = extractor.extract_footer_by_keyword(footer_keywords, page_numbers=[1, 2, 3])
        
        found_count = len([f for f in footers.values() if f])
        print(f"Found footers with keywords on {found_count} pages")
        print_footer_summary(footers, max_length=100)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_page_number_extraction():
    """Test 5: Extract page numbers from headers/footers"""
    print("\n" + "="*80)
    print("TEST 5: Page Number Extraction")
    print("="*80)
    
    test_pdfs = [
        'ALS/Arba_artsot_Tel_aviv_29_01_2025.pdf',
        'element/Chirelson_33_TelAviv_05_09_2025.pdf'
    ]
    
    pdf_path = None
    for pdf in test_pdfs:
        if Path(pdf).exists():
            pdf_path = pdf
            break
    
    if not pdf_path:
        print("❌ No test PDF found")
        return False
    
    print(f"\nTesting with: {pdf_path}")
    
    try:
        extractor = HeaderFooterExtractor(pdf_path)
        
        # Extract headers and footers
        headers = extractor.extract_header_smart(page_numbers=list(range(1, 6)))
        footers = extractor.extract_footer_smart(page_numbers=list(range(1, 6)))
        
        # Extract page numbers
        header_page_nums = extractor.extract_page_numbers_from_header(headers)
        footer_page_nums = extractor.extract_page_numbers_from_footer(footers)
        
        print("\n--- Page Numbers from Headers ---")
        for page in sorted(header_page_nums.keys()):
            num = header_page_nums[page]
            status = "✓" if num else "✗"
            print(f"{status} Page {page}: {num if num else 'Not found'}")
        
        print("\n--- Page Numbers from Footers ---")
        for page in sorted(footer_page_nums.keys()):
            num = footer_page_nums[page]
            status = "✓" if num else "✗"
            print(f"{status} Page {page}: {num if num else 'Not found'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_lab_identification():
    """Test 6: Identify lab from header/footer"""
    print("\n" + "="*80)
    print("TEST 6: Lab Identification from Headers/Footers")
    print("="*80)
    
    test_cases = [
        ('element/Chirelson_33_TelAviv_05_09_2025.pdf', 'Element'),
        ('ALS/Arba_artsot_Tel_aviv_29_01_2025.pdf', 'ALS'),
        ('bactochem/Ainshtein15_Tel_Aviv_13_02_2025.pdf', 'Bactochem')
    ]
    
    lab_patterns = {
        'ALS': ['als', 'alsglobal', 'als czech'],
        'Element': ['element materials', 'element technology', 'element'],
        'Bactochem': ['bactochem', 'בקטוכם'],
        'Aminolab': ['aminolab', 'אמינולאב']
    }
    
    results = []
    
    for pdf_path, expected_lab in test_cases:
        if not Path(pdf_path).exists():
            print(f"⊘ Skipping {pdf_path} (not found)")
            continue
        
        try:
            extractor = HeaderFooterExtractor(pdf_path)
            headers = extractor.extract_header_smart(page_numbers=[1])
            footers = extractor.extract_footer_smart(page_numbers=[1])
            
            # Combine all text
            all_text = ' '.join([*headers.values(), *footers.values()]).lower()
            
            # Identify lab
            detected_lab = 'Unknown'
            for lab_name, patterns in lab_patterns.items():
                if any(pattern in all_text for pattern in patterns):
                    detected_lab = lab_name
                    break
            
            match = "✓" if detected_lab == expected_lab else "✗"
            results.append((pdf_path, expected_lab, detected_lab, match == "✓"))
            
            print(f"{match} {Path(pdf_path).name}")
            print(f"  Expected: {expected_lab}, Detected: {detected_lab}")
            
        except Exception as e:
            print(f"✗ Error processing {pdf_path}: {e}")
            results.append((pdf_path, expected_lab, 'Error', False))
    
    # Summary
    if results:
        success_count = sum(1 for r in results if r[3])
        print(f"\n--- Summary: {success_count}/{len(results)} correct ---")
        return success_count == len(results)
    
    return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "█"*80)
    print("HEADER & FOOTER EXTRACTION TEST SUITE")
    print("█"*80)
    
    tests = [
        ("Basic Extraction", test_basic_extraction),
        ("Smart Extraction", test_smart_extraction),
        ("Image Extraction", test_image_extraction),
        ("Keyword Extraction", test_keyword_extraction),
        ("Page Number Extraction", test_page_number_extraction),
        ("Lab Identification", test_lab_identification)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Final summary
    print("\n" + "█"*80)
    print("TEST RESULTS SUMMARY")
    print("█"*80)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_map = {
            '1': test_basic_extraction,
            '2': test_smart_extraction,
            '3': test_image_extraction,
            '4': test_keyword_extraction,
            '5': test_page_number_extraction,
            '6': test_lab_identification
        }
        
        test_num = sys.argv[1]
        if test_num in test_map:
            test_map[test_num]()
        else:
            print(f"Invalid test number. Choose from: {', '.join(test_map.keys())}")
    else:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)
