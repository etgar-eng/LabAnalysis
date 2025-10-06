

import os
import warnings

# CRITICAL: Set these BEFORE importing tensorflow or any modules that import tensorflow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Suppress warnings
warnings.filterwarnings('ignore')

import argparse
import camelot
import io
import itertools
import pandas as pd
from tensorflow.keras.models import load_model
from PIL import Image
from pathlib import Path
from image_extractor import print_image_summary, extract_images_hybrid_method
from identifier import predict_logo
from functions import Extractor
from functions import get_page_count
import logging
import sys

from openpyxl import Workbook
from logging_config import setup_logging, suppress_warnings

# Suppress all DataFrame displays
pd.set_option('display.max_rows', 0)
pd.set_option('display.max_columns', 0)
pd.set_option('display.width', 0)

# Suppress warnings
warnings.filterwarnings('ignore')


# Redirect stdout temporarily during processing if needed
def suppress_output(func, *args, **kwargs):
    """Run function with suppressed output"""
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = func(*args, **kwargs)
    finally:
        sys.stdout = original_stdout
    return result


# Setup logging first thing
logger = setup_logging(
    log_level=logging.INFO,  # Change to DEBUG for more verbose
    log_file="lab_analysis.log"  # Optional
)


class PdfLabAnalysisReader:
    def __init__(self, args=None):
        self.df_summery: list[pd.DataFrame] = []
        self.args = args
        main_dir = Path(os.getcwd())
        child_dir = main_dir / self.args.lab

        # Find PDF file - Use Path.glob() instead
        pdf_files = list(child_dir.glob("*.pdf"))  # Use Path.glob()
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in {child_dir}")
        self.pdf = self.args.input
        self.page_pdf = get_page_count(self.pdf)
        self.checks_number = self.get_number_of_checks()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Delete the entire file
        if os.path.exists("df_summary.xlsx"):
            os.remove("df_summary.xlsx")

        # Create new Excel file
        workbook = Workbook()
        workbook.save("df_summary.xlsx")
        workbook.close()

        # Delete the entire file
        if os.path.exists(f"{self.args.lab}.xlsx"):
            os.remove(f"{self.args.lab}.xlsx")

        # Create new Excel file
        workbook = Workbook()
        workbook.save(f"{self.args.lab}.xlsx")
        workbook.close()

        self.run()

    def __repr__(self):
        return f'{Path(self.pdf).stem} contains {self.checks_number} checks and {self.page_pdf} pages'

    def get_number_of_checks(self):
        if self.args.lab == 'Aminolab':
            return self.page_pdf // 8
        return 1

    def checking_for_multi_labs(self, images, model, save=False) -> list[str]:
        print_image_summary(images)
        page_dict = {}

        for i, img in enumerate(images):
            image = Image.open(io.BytesIO(img.image_data))
            page = images[i].page_number
            try:
                if save:
                    image.save(f'figure_no{i}.png')
            except OSError:
                pass

            class_names, confidence = predict_logo(model, image, ['ALS', 'Bactochem', 'Aminolab', 'ALS', 'Yeda', 'Yeda'])
            logger.info(f"Image {i} (Page {page}): {class_names} ({confidence:.3f})")

            # Check if this page already exists in dictionary
            if page not in page_dict:
                # First entry for this page
                page_dict[page] = [class_names, confidence]
            else:
                # Page already exists, check if current confidence is higher
                if confidence > page_dict[page][1]:
                    page_dict[page] = [class_names, confidence]

        # Print the final dictionary
        print("\nFinal Page Dictionary:")
        for page_num in sorted(page_dict.keys()):
            lab, conf = page_dict[page_num]
            print(f"{page_num}: ['{lab}', np.float32({conf:.2f})]")

        page = [str(i) for i in page_dict.keys() if page_dict.get(i)[0] == self.args.lab]

        if self.args.lab == 'Bactochem':
            # Find the first lab that is not Bactochem
            other_labs = [page_num for page_num, (lab, _) in page_dict.items() if lab != 'Bactochem'][0]
            p = list(range(int(page[0]), other_labs))
            p = [str(i) for i in p]

        else:
            p = page

        return p

    def run(self, save: bool = False):
        try:
            model = load_model('lab_logo_classifier.h5')
            logger.info(f"Reading PDF: try to extract figures from the pdf file")
            images = extract_images_hybrid_method(self.pdf)

            dict_labs_tables_areas = {
                'ALS': {
                    'tables_area': (['30,50,410,680'],
                                    ['30,50,410,680'],
                                    None,
                                    ['30,50,410,680'],
                                    ['30,50,410,680'],
                                    ['30,50,410,680'],
                                    None
                                    ),
                    'pages': ['3', '4', None, '6','7','8','9'],
                    'split_text': True,
                    'strip_text' : '\n',

                },
                'Element': {
                    'tables_area': (['30,100,600,600'],
                                    ['30,60,600,650']),
                    'pages': ['2', '3']
                },
                'Bactochem': {
                    'tables_area': (['240,40,550,400'],
                                    ['240,30,550,750'],
                                    ['240,30,550,750'],
                                    ['240,30,550,750'],
                                    None),
                    'pages': ['1', '2','3','4',None],
                    'row_tol': [7, 12]
                },
                'Aminolab': {
                    'tables_area': (['250,115,530,530'],
                                    ['250,200,530,690'],
                                    None,
                                    ['100,390,550,700'],
                                    ['30,110,460,680'],
                                    ['30,110,460,680'],
                                    None,
                                    None),
                    'pages': ['1', '2', None ,'4', '5', '6',None,None],
                    'row_tol': [7, 12]
                }
            }

            if self.args.multi == 'true':
                logger.info(f"Reading PDF: {self.pdf} contains multi labs chemical analysis -> extracting {self.args.lab} only")
                p = self.checking_for_multi_labs(images, model, save)
                logger.info(
                    f"Reading PDF: from pages: {p}")
            else:
                logger.info(f"Reading PDF: {self.pdf} contains single lab chemical analysis")
                data = dict_labs_tables_areas.get(self.args.lab)
                p = data.get('pages')

            # Get tables pdf position and rows heights for the current lab
            data = dict_labs_tables_areas.get(self.args.lab)
            check_no = [i for i in range(1, self.checks_number + 1) for _ in range(len(p))]
            indexes = list(range(1, self.page_pdf + 1))

            with pd.ExcelWriter("df_summary.xlsx", mode='a', engine='openpyxl', if_sheet_exists='replace'
                                ) as writer:

                for c, i, page, table_area in zip(check_no,
                                                  indexes,
                                                  p * self.checks_number,
                                                  data.get('tables_area') * self.checks_number):
                    print('-------------------------------------------------------------------------------------')
                    print(f'Check no.{c}     |    index no.{i}:  |  page no.{page}   |   table area:{table_area}')
                    if page is not None:
                        # Handle row_tol parameter safely
                        row_tol_param = None
                        if data.get('row_tol'):
                            if page == '1':
                                row_tol_param = data.get('row_tol')[0]
                            else:
                                row_tol_param = data.get('row_tol')[-1]
                        # Build camelot parameters
                        camelot_params = {
                            'pages': str(i) if self.checks_number > 1 else page,
                            'flavor': 'stream',
                            'table_areas': table_area,
                            'split_text': data.get('split_text'),
                            'strip_text': data.get('strip_text')
                        }

                        if row_tol_param is not None:
                            camelot_params['row_tol'] = row_tol_param
                        try:
                            tables = camelot.read_pdf(self.pdf, **camelot_params)
                        except IndexError:
                            break
                        if tables:
                            self.df_summery.append(tables[0].df)
                        if page == [i for i in p if isinstance(i, str)][-1]:
                            df_all = Extractor.extruct_col_from_lab(self.df_summery, self.args.lab)
                            df_all.to_excel(writer, sheet_name=f'Check{c}', index=False)
                            self.df_summery: list[pd.DataFrame] = []


                # Remove the default "Sheet" ONLY if other sheets exist
                if 'Sheet' in writer.book.sheetnames and len(writer.book.sheetnames) > 1:
                    writer.book.remove(writer.book['Sheet'])

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="PDF Lab Analysis Reader - DEBUG VERSION",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --lab Bactochem
  python main.py --lab Element --output my_results
        """
    )

    parser.add_argument(
        "--lab",
        choices=['ALS', 'Bactochem', 'Aminolab', 'Element'],
        required=True,
        help="Choose chemical analysis lab"
    )

    parser.add_argument('-m', '--multi', choices=['true', 'false'],
                        default='false',
                        help='Enable or disable multi labs processor')

    parser.add_argument(
        "--input",
        required=True,
        help="Set chemical analysis pdf file"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output filename (optional)"
    )

    args = parser.parse_args()

    try:
        # Create extractor instance
        extractor_instance = Extractor(args)

        # Process PDF
        lab_processor = PdfLabAnalysisReader(args)
        print(lab_processor)
        # Apply the function to match values
        df_format = extractor_instance.df_format.copy()
        excel_file = pd.ExcelFile('df_summary.xlsx')
        all_sheets = {}
        # Save formatted results
        output_filename = args.output or args.lab
        output_path = f'{output_filename}.xlsx'
        with suppress_warnings():
                with pd.ExcelWriter(output_path, mode='a', engine='openpyxl',if_sheet_exists='replace',
                                    ) as writer:
                    for sheet_name in excel_file.sheet_names:
                        all_sheets[sheet_name] = excel_file.parse(sheet_name)
                        df_format['values'] = df_format['test'].apply(
                           lambda i: extractor_instance.search_for_value(all_sheets[sheet_name], i))
                        df_format.to_excel(writer, index=False,sheet_name=sheet_name)
                        # Remove the default "Sheet" ONLY if other sheets exist
                        if 'Sheet' in writer.book.sheetnames and len(writer.book.sheetnames) > 1:
                            writer.book.remove(writer.book['Sheet'])


        print(f"Processing completed successfully!")
        print(f"Raw data saved to: df_summary.xlsx")
        print(f"Formatted data saved to: {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        print(f"Full traceback:\n{traceback.format_exc()}")
        exit(1)