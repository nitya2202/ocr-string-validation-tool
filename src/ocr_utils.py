# ocr_string_validator/src/ocr_utils.py

from PIL import Image
import pytesseract

def extract_text_from_image_region(image_path, region):
    try:
        img = Image.open(image_path)
        left, top, right, bottom = region
        cropped = img.crop((left, top, right, bottom))
        text = pytesseract.image_to_string(cropped, lang='eng')
        return text.strip()
    except Exception as e:
        print(f"Error reading {image_path}: {e}")
        return ""
