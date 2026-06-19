import pdfplumber


#-----------------------------------------------------------------------------
#This part is used to dectect if the input PDF is Digital or Image converted
#-----------------------------------------------------------------------------
def is_digital_pdf(pdf_path, min_chars=1000):

    try:
        text = ""

        with pdfplumber.open(pdf_path) as pdf:

            for page in pdf.pages:

                images = page.images
                page_area = page.width * page.height
                full_page_image = False

                for img in page.images:
                    img_width = img["x1"] - img["x0"]
                    img_height = img["y1"] - img["y0"]

                    img_area = img_width * img_height

                    coverage = img_area / page_area

                    if coverage > 1:
                        return True

    except: 
        return False
