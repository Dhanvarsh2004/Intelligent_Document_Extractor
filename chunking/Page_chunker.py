import pdfplumber

def page_chunking(pdf_path):

    page_chunks = []

    with pdfplumber.open(pdf_path) as pdf:

        for i, page in enumerate(pdf.pages):

            page_text = page.extract_text()
            tables = page.extract_tables()

            if page_text is None:
                page_text = ""

            # Determine page type
            if tables:
                text_type = "table"
            else:
                text_type = "text"

            page_chunks.append({
                "pageno": i + 1,
                "type": text_type,
                "text": page_text
            })

    return page_chunks