import pdfplumber
def page_chunking(pdf_path):

    page_chunks = []

    with pdfplumber.open(pdf_path) as pdf:

        for i, page in enumerate(pdf.pages):

            page_text = page.extract_text()
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    text_type="text"
                else:
                    text_type="table"

            if page_text is None:
                page_text = ""

            page_chunks.append({
                "pageno": i + 1,
                "type": text_type,
                "text": page_text
            })

    return page_chunks

chunks=page_chunking(r"C:\Users\Dhanvarsh.m\Desktop\IDE\TestDocuments\748e1749-318f-4e41-b10b-8de5dadaac7d.pdf")
print(chunks)

