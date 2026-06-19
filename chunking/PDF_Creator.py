from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter


def extract_pages_as_pdf(pdf_path, page_numbers, output_folder="ExtractedPages"):
    pdf_path = Path(pdf_path)
    output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True)

    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page_no in page_numbers:

        if page_no < 1 or page_no > len(reader.pages):
            print(f"Skipping invalid page number: {page_no}")
            continue

        # Add page to the same PDF
        writer.add_page(reader.pages[page_no - 1])

    # Save once after all pages have been added
    output_file = output_folder / "selected_pages.pdf"

    with open(output_file, "wb") as f:
        writer.write(f)

    print(f"Saved: {output_file}")