# Add this at the top of your main.py file (or wherever you initialize your application)

import logging
import warnings
import os
import sys
from pathlib import Path


def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Setup comprehensive logging configuration

    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional log file path
    """
    # Suppress specific warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='functions')
    warnings.filterwarnings('ignore', message='.*This pattern is interpreted as a regular expression.*')
    warnings.filterwarnings('ignore', message='.*Ignoring wrong pointing object.*')
    warnings.filterwarnings('ignore', message='.*oneDNN custom operations.*')
    warnings.filterwarnings('ignore', message='.*Compiled the loaded model.*')

    # Suppress TensorFlow warnings
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=all, 1=info, 2=warnings, 3=errors
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Setup handlers
    handlers = []

    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format=log_format,
        datefmt=date_format,
        force=True  # Override any existing configuration
    )

    # Suppress specific library loggers
    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    logging.getLogger('absl').setLevel(logging.ERROR)
    logging.getLogger('pypdf').setLevel(logging.ERROR)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)

    return logging.getLogger(__name__)


# Enhanced logging for identifier.py
def setup_ml_logging():
    """Setup specific logging for ML operations"""
    logger = logging.getLogger('lab_analysis.ml')

    def log_prediction(image_num, page, prediction, confidence):
        logger.info(f"Image {image_num} (Page {page}): {prediction} ({confidence:.3f})")

    def log_model_loading(model_path):
        logger.info(f"Loading ML model from: {model_path}")

    def log_image_extraction(num_images):
        logger.info(f"Extracted {num_images} images from PDF")

    return log_prediction, log_model_loading, log_image_extraction


# Enhanced logging for image_extractor.py
def setup_extraction_logging():
    """Setup specific logging for image extraction"""
    logger = logging.getLogger('lab_analysis.extraction')

    def log_extraction_start(pdf_path):
        logger.info(f"Starting image extraction from: {pdf_path}")

    def log_extraction_summary(images):
        logger.info(f"Extraction complete: {len(images)} images found")
        if images:
            pages_with_images = {}
            for img in images:
                pages_with_images[img.page_number] = pages_with_images.get(img.page_number, 0) + 1

            for page_num, count in sorted(pages_with_images.items()):
                logger.debug(f"Page {page_num}: {count} images")

    def log_extraction_error(error, page_num=None):
        if page_num:
            logger.error(f"Error extracting from page {page_num}: {error}")
        else:
            logger.error(f"Extraction error: {error}")

    return log_extraction_start, log_extraction_summary, log_extraction_error


# Enhanced logging for functions.py
def setup_processing_logging():
    """Setup specific logging for data processing"""
    logger = logging.getLogger('lab_analysis.processing')

    def log_file_processing(file_info, rows_added=None):
        if rows_added is not None:
            logger.info(f"Processed file: {rows_added} rows added")
        else:
            logger.warning(f"Failed to process file - no valid data found")

    def log_parameter_search(param_name, found_value=None):
        if found_value is not None:
            logger.debug(f"Found parameter '{param_name}': {found_value}")
        else:
            logger.warning(f"Parameter '{param_name}' not found in data")

    def log_extraction_method(method_name):
        logger.info(f"Using extraction method: {method_name}")

    def log_final_summary(total_rows):
        logger.info(f"Processing complete: {total_rows} total rows in final dataset")

    return log_file_processing, log_parameter_search, log_extraction_method, log_final_summary


# Usage example for main.py:
if __name__ == "__main__":
    # Setup logging at the start of your main function
    logger = setup_logging(
        log_level=logging.INFO,  # Change to DEBUG for more verbose output
        log_file="lab_analysis.log"  # Optional log file
    )

    logger.info("Starting lab analysis application")

    # Your existing code here...

    logger.info("Lab analysis completed successfully")

# For identifier.py, add these imports and modifications:
# At the top of identifier.py, add:
# from your_logging_module import setup_ml_logging
# log_prediction, log_model_loading, log_image_extraction = setup_ml_logging()

# Then in your predict_logo function, replace print statements with:
# log_prediction(img_info.image_index, img_info.page_number, predicted_class, confidence)

# For image_extractor.py, add these imports and modifications:
# At the top of image_extractor.py, add:
# from your_logging_module import setup_extraction_logging
# log_extraction_start, log_extraction_summary, log_extraction_error = setup_extraction_logging()

# For functions.py, add these imports and modifications:
# At the top of functions.py, add:
# from your_logging_module import setup_processing_logging
# log_file_processing, log_parameter_search, log_extraction_method, log_final_summary = setup_processing_logging()

# Additional context manager for suppressing specific warnings during processing:
from contextlib import contextmanager


@contextmanager
def suppress_warnings():
    """Context manager to temporarily suppress warnings during processing"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        warnings.simplefilter("ignore", FutureWarning)
        yield

# Usage example:
# with suppress_warnings():
#     # Your processing code that generates warnings
#     result = some_processing_function()