import pdfplumber
import time
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption
)
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

from extraction.pdf_detector import is_digital_pdf


#---------------------------------------------------------------
#To extract text from the PDF
#---------------------------------------------------------------

def extract_pdf(pdf_path):
    text = ""
    try:
        print("Checking for tables...")

        with pdfplumber.open(pdf_path) as pdf:
            has_table = False

            # Check if any page contains tables
            for page in pdf.pages[:2]:
                tables = page.extract_tables()

                for table in tables:
                    if not table:
                        continue

                    row_count = len(table)
                    col_count = max(len(row) for row in table if row)

                    # Consider it a real table only if it has multiple rows
                    if row_count < 1:
                        for page in pdf.pages:
                            page_text = page.extract_text()

                            if page_text:
                                text += page_text + "\n"

                        if len(text.strip()) > 500:
                            print("pdfplumber successful")
                            return text

    except Exception as e:
        print("pdfplumber failed:", e)

    print("Using Docling as last option...")

# Docling for PDF Extraction
 
    converter = DocumentConverter()
    pipeline_options = PdfPipelineOptions()

    # Disable OCR
    pipeline_options.do_ocr = False


    def create_converter(use_ocr):

        pipeline_options = PdfPipelineOptions()

        pipeline_options.do_ocr = use_ocr

        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options
                )
            }
        )
    if is_digital_pdf(pdf_path):

        print("Digital PDF detected -> OCR OFF")

        converter = create_converter(False)

    else:

        print("Scanned PDF detected -> OCR ON")

        converter = create_converter(True)

    docling_start = time.time()
    result = converter.convert(pdf_path)
    print(f"Docling Time: {time.time() - docling_start:.2f}s")
    return result.document.export_to_markdown()
