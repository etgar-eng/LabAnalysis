import pdfplumber
from PIL import Image
import io
import matplotlib.pyplot as plt
from typing import List, Dict, Any
import numpy as np


class PDFImageInfo:
    """Class to store image information with page number"""

    def __init__(self, image_data: bytes, page_number: int, image_index: int,
                 bbox: tuple, image_format: str = "unknown"):
        self.image_data = image_data
        self.page_number = page_number
        self.image_index = image_index
        self.bbox = bbox  # (x0, top, x1, bottom)
        self.image_format = image_format
        self.width = bbox[2] - bbox[0] if bbox else 0
        self.height = bbox[3] - bbox[1] if bbox else 0

    def __repr__(self):
        return f"PDFImageInfo(page={self.page_number}, index={self.image_index}, size={self.width}x{self.height})"

    def save_image(self, filename: str = None):
        """Save the image to a file"""
        if not filename:
            filename = f"page_{self.page_number}_img_{self.image_index}.png"

        try:
            img = Image.open(io.BytesIO(self.image_data))
            img.save(filename)
            return filename
        except Exception as e:
            print(f"Error saving image: {e}")
            return None


    def get_pil_image(self):
        """Get PIL Image object from the image data"""
        try:
            return Image.open(io.BytesIO(self.image_data))
        except Exception as e:
            print(f"Error creating PIL image: {e}")
            return None

    def show_image(self, title: str = None):
        """Display the image using matplotlib"""
        try:
            img = self.get_pil_image()
            if img is None:
                print("Cannot display image - no valid image data")
                return

            plt.figure(figsize=(8, 6))
            plt.imshow(img)

            if title is None:
                title = f"Page {self.page_number}, Image {self.image_index} ({self.width:.0f}x{self.height:.0f})"
            plt.title(title)
            plt.axis('off')
            plt.show()

        except Exception as e:
            print(f"Error displaying image: {e}")

    def get_numpy_array(self):
        """Get image as numpy array"""
        try:
            img = self.get_pil_image()
            if img is None:
                return None
            return np.array(img)
        except Exception as e:
            print(f"Error converting to numpy array: {e}")
            return None


def extract_images_with_page_numbers(pdf_path: str, min_width: int = 50, min_height: int = 50) -> List[PDFImageInfo]:
    """
    Extract all images from PDF with page numbers using pdfplumber

    Args:
        pdf_path: Path to the PDF file
        min_width: Minimum width to consider an image (filters out small decorative elements)
        min_height: Minimum height to consider an image

    Returns:
        List of PDFImageInfo objects containing image data and metadata
    """
    image_list = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):  # Start counting from 1

                # Get images from the page
                if hasattr(page, 'images') and page.images:
                    for img_index, img_obj in enumerate(page.images):
                        # Extract image properties
                        bbox = (img_obj.get('x0', 0), img_obj.get('top', 0),
                                img_obj.get('x1', 0), img_obj.get('bottom', 0))

                        width = bbox[2] - bbox[0]
                        height = bbox[3] - bbox[1]

                        # Filter out small images (likely decorative elements)
                        if width >= min_width and height >= min_height:

                            # Try to extract image data
                            try:
                                # pdfplumber doesn't directly provide image bytes,
                                # so we'll work with the image object properties

                                # Create a placeholder for actual image data
                                # In practice, you might need to use PyMuPDF for actual extraction
                                image_info = PDFImageInfo(
                                    image_data=b"",  # Placeholder - see alternative method below
                                    page_number=page_num,
                                    image_index=img_index,
                                    bbox=bbox,
                                    image_format="unknown"
                                )

                                image_list.append(image_info)

                            except Exception as e:
                                print(f"Error processing image on page {page_num}: {e}")
                                continue

                # Alternative: Extract images using page.within_bbox() for regions
                # This can help identify image-like regions even if not explicitly marked as images

    except Exception as e:
        print(f"Error reading PDF: {e}")

    return image_list


def extract_images_hybrid_method(pdf_path: str, min_width: int = 50, min_height: int = 50) -> List[PDFImageInfo]:
    """
    Hybrid method using both pdfplumber and PyMuPDF for complete image extraction
    """
    import fitz  # PyMuPDF for actual image data extraction

    image_list = []

    try:
        # Use PyMuPDF to get actual image data
        fitz_doc = fitz.open(pdf_path)

        # Use pdfplumber to get page structure and image locations
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):

                # Get corresponding PyMuPDF page
                fitz_page = fitz_doc.load_page(page_num - 1)  # PyMuPDF uses 0-based indexing
                fitz_images = fitz_page.get_images(full=True)

                # Process images found by PyMuPDF
                for img_index, img in enumerate(fitz_images):
                    try:
                        xref = img[0]
                        base_image = fitz_doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        # Get image dimensions from PyMuPDF
                        img_rect = fitz_page.get_image_bbox(img)
                        bbox = (img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1)

                        width = bbox[2] - bbox[0]
                        height = bbox[3] - bbox[1]

                        # Filter by size
                        if width >= min_width and height >= min_height:
                            image_info = PDFImageInfo(
                                image_data=image_bytes,
                                page_number=page_num,
                                image_index=img_index,
                                bbox=bbox,
                                image_format=image_ext
                            )

                            image_list.append(image_info)

                    except Exception as e:
                        print(f"Error extracting image {img_index} from page {page_num}: {e}")
                        continue

        fitz_doc.close()

    except Exception as e:
        print(f"Error in hybrid extraction: {e}")

    return image_list


def display_images_grid(image_list: List[PDFImageInfo], max_images: int = 12,
                        figsize: tuple = (15, 10)):
    """
    Display multiple images in a grid layout

    Args:
        image_list: List of PDFImageInfo objects
        max_images: Maximum number of images to display
        figsize: Figure size for matplotlib
    """
    # Limit number of images to display
    images_to_show = image_list[:max_images]

    if not images_to_show:
        print("No images to display")
        return

    # Calculate grid dimensions
    num_images = len(images_to_show)
    cols = min(4, num_images)  # Max 4 columns
    rows = (num_images + cols - 1) // cols  # Ceiling division

    fig, axes = plt.subplots(rows, cols, figsize=figsize)

    # Handle single image case
    if num_images == 1:
        axes = [axes]
    elif rows == 1:
        axes = [axes] if cols == 1 else axes
    else:
        axes = axes.flatten()

    for i, img_info in enumerate(images_to_show):
        try:
            pil_img = img_info.get_pil_image()
            if pil_img is not None:
                axes[i].imshow(pil_img)
                axes[i].set_title(f"P{img_info.page_number}-I{img_info.image_index}\n"
                                  f"{img_info.width:.0f}x{img_info.height:.0f}")
                axes[i].axis('off')
            else:
                axes[i].text(0.5, 0.5, "Error\nLoading Image",
                             ha='center', va='center', transform=axes[i].transAxes)
                axes[i].axis('off')
        except Exception as e:
            print(f"Error displaying image {i}: {e}")
            axes[i].axis('off')

    # Hide any extra subplots
    for i in range(num_images, len(axes)):
        axes[i].axis('off')

    plt.tight_layout()
    plt.show()


def show_single_image(image_info: PDFImageInfo, title: str = None):
    """
    Display a single image

    Args:
        image_info: PDFImageInfo object
        title: Custom title for the image
    """
    image_info.show_image(title)


def display_images_by_page(image_list: List[PDFImageInfo], page_number: int):
    """
    Display all images from a specific page

    Args:
        image_list: List of PDFImageInfo objects
        page_number: Page number to display images from
    """
    page_images = [img for img in image_list if img.page_number == page_number]

    if not page_images:
        print(f"No images found on page {page_number}")
        return

    print(f"Displaying {len(page_images)} images from page {page_number}")
    display_images_grid(page_images, figsize=(12, 8))


def browse_images_interactive(image_list: List[PDFImageInfo]):
    """
    Interactive browser for PDF images
    """
    if not image_list:
        print("No images to browse")
        return

    print(f"Found {len(image_list)} images to browse")
    print("Commands: 'next', 'prev', 'show <index>', 'page <num>', 'grid', 'quit'")

    current_index = 0

    while True:
        # Show current image info
        img = image_list[current_index]
        print(f"\n[{current_index + 1}/{len(image_list)}] {img}")

        command = input("Command: ").strip().lower()

        if command == 'quit' or command == 'q':
            break
        elif command == 'next' or command == 'n':
            current_index = (current_index + 1) % len(image_list)
            image_list[current_index].show_image()
        elif command == 'prev' or command == 'p':
            current_index = (current_index - 1) % len(image_list)
            image_list[current_index].show_image()
        elif command.startswith('show '):
            try:
                idx = int(command.split()[1]) - 1
                if 0 <= idx < len(image_list):
                    current_index = idx
                    image_list[current_index].show_image()
                else:
                    print(f"Invalid index. Use 1-{len(image_list)}")
            except ValueError:
                print("Invalid index format")
        elif command.startswith('page '):
            try:
                page_num = int(command.split()[1])
                display_images_by_page(image_list, page_num)
            except ValueError:
                print("Invalid page number format")
        elif command == 'grid':
            display_images_grid(image_list)
        else:
            print("Unknown command. Use: next, prev, show <index>, page <num>, grid, quit")


def predict_logo(model, image, class_names):
    """
    Predict logo class for a single image object

    Args:
        model: Trained Keras model
        image: PIL Image object, numpy array, or PDFImageInfo object
        class_names: List of class names

    Returns:
        tuple: (predicted_class_name, confidence)
    """
    # Handle PDFImageInfo object
    if isinstance(image, PDFImageInfo):
        img = image.get_pil_image()
        if img is None:
            raise ValueError("Cannot extract PIL image from PDFImageInfo object")
    elif isinstance(image, np.ndarray):
        # It's a numpy array
        img = Image.fromarray(image.astype('uint8'))
    else:
        # Assume it's already a PIL Image
        img = image

    # Resize to model's expected input size (assuming 224x224 for MobileNetV2)
    IMG_HEIGHT, IMG_WIDTH = 224, 224
    img = img.resize((IMG_HEIGHT, IMG_WIDTH))

    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Convert to array and normalize
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, 0)  # Create batch dimension
    img_array = img_array.astype('float32') / 255.0  # Normalize

    predictions = model.predict(img_array)
    predicted_class = np.argmax(predictions[0])
    confidence = np.max(predictions[0])

    return class_names[predicted_class], confidence


def print_image_summary(image_list: List[PDFImageInfo]):
    """Print a summary of extracted images"""
    print(f"\nExtracted {len(image_list)} images:")
    print("-" * 60)

    for img in image_list:
        print(f"Page {img.page_number:2d} | Image {img.image_index} | "
              f"{img.width:4.0f}x{img.height:4.0f} | Format: {img.image_format}")

    # Group by page
    pages_with_images = {}
    for img in image_list:
        if img.page_number not in pages_with_images:
            pages_with_images[img.page_number] = 0
        pages_with_images[img.page_number] += 1

    print(f"\nImages per page:")
    for page_num, count in sorted(pages_with_images.items()):
        print(f"Page {page_num}: {count} images")



# Usage examples
if __name__ == "__main__":
    pdf_path = "your_document.pdf"

    # Extract images using hybrid method (recommended)
    print("Extracting images from PDF...")
    images = extract_images_hybrid_method(pdf_path)
    print_image_summary(images)

    # Display all images in a grid
    print("\nDisplaying all images in grid:")
    display_images_grid(images)

    # Display images from specific page
    print("\nDisplaying images from page 1:")
    display_images_by_page(images, 1)

    # Show individual images
    print("\nShowing individual images:")
    for img in images[:3]:  # Show first 3 images
        img.show_image()

    # Interactive browsing
    print("\nStarting interactive browser...")
    browse_images_interactive(images)

    # Test with your ML model (if you have it loaded)
    # from tensorflow.keras.models import load_model
    # model = load_model('lab_logo_classifier.h5')
    # class_names = ['lab1', 'lab2', 'lab3']
    #
    # for img in images:
    #     try:
    #         prediction, confidence = predict_logo(model, img, class_names)
    #         print(f"Page {img.page_number}, Image {img.image_index}: {prediction} ({confidence:.3f})")
    #     except Exception as e:
    #         print(f"Error predicting image: {e}")