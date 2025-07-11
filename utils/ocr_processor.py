from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
import io

def extract_text_from_file(uploaded_file):
    # uploaded_file is a Streamlit UploadedFile object
    file_type = uploaded_file.type
    file_bytes = uploaded_file.read()
    text = ""
    if file_type == "application/pdf":
        images = convert_from_bytes(file_bytes)
        for img in images:
            text += pytesseract.image_to_string(img)
    else:
        img = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(img)
    return text