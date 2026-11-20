from pathlib import Path

import pymupdf as fitz
import pytesseract
from PIL import Image, ImageOps

from app.core.config import settings

# pytesseract ko batao ki Tesseract program kahan hai
pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

# Agar PDF ke ek page se itne se kam characters mile, to use scanned maanenge
MIN_CHARS_PER_PAGE = 50

# OCR ke liye page ko 3 guna bada karke image banate hain (saaf padhne ke liye)
OCR_ZOOM = 3

# Bahut lambi PDF se server na atke, isliye itne pages tak hi padhenge
MAX_PAGES = 20

# Ek hi row ke shabdon ki height (y) mein itna farak ho sakta hai
ROW_TOLERANCE = 4

# Do shabdon ke beech itna gap ho to unhe alag column maanenge
COLUMN_GAP = 12


def _ocr_image(image: Image.Image) -> str:
    """Ek image se Tesseract text padhta hai."""
    return pytesseract.image_to_string(image, lang=settings.ocr_language)


def _page_text_by_rows(page) -> str:
    """PDF page ka text row ke hisaab se deta hai (table ki row = ek line)."""
    # Har word: (x0, y0, x1, y1, text, ...)
    words = page.get_text("words")
    if not words:
        return ""

    # Upar se neeche, phir left se right
    words = sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0]))

    # Jin words ki height lagbhag same hai, unhe ek row mein rakho
    rows = []
    for word in words:
        y_center = (word[1] + word[3]) / 2
        if rows and abs(y_center - rows[-1]["y"]) <= ROW_TOLERANCE:
            rows[-1]["words"].append(word)
        else:
            rows.append({"y": y_center, "words": [word]})

    # Har row ko ek line banao. Bade gap par 2 spaces (column ka alag hona)
    lines = []
    for row in rows:
        row_words = sorted(row["words"], key=lambda w: w[0])
        line = row_words[0][4]
        for previous, current in zip(row_words, row_words[1:]):
            gap = current[0] - previous[2]
            separator = "  " if gap > COLUMN_GAP else " "
            line += separator + current[4]
        lines.append(line)

    return "\n".join(lines)


def _extract_pdf(file_path: Path) -> tuple[str, str]:
    """PDF se text nikalta hai. Scanned page mile to us par OCR lagata hai."""
    pages_text: list[str] = []
    used_text = False
    used_ocr = False

    doc = fitz.open(file_path)
    try:
        for page_number, page in enumerate(doc):
            if page_number >= MAX_PAGES:
                break

            # Pehle seedha text nikalne ki koshish (row-wise)
            text = _page_text_by_rows(page).strip()

            if len(text) >= MIN_CHARS_PER_PAGE:
                used_text = True
            else:
                # Text nahi mila: ye scanned page hai, to OCR lagao
                pixmap = page.get_pixmap(matrix=fitz.Matrix(OCR_ZOOM, OCR_ZOOM))
                image = Image.frombytes(
                    "RGB", (pixmap.width, pixmap.height), pixmap.samples
                )
                text = _ocr_image(image).strip()
                used_ocr = True

            pages_text.append(text)
    finally:
        doc.close()

    if used_text and used_ocr:
        method = "mixed"
    elif used_ocr:
        method = "ocr"
    else:
        method = "digital_pdf"

    return "\n\n".join(pages_text), method


def _extract_image(file_path: Path) -> tuple[str, str]:
    """JPG ya PNG image se OCR se text nikalta hai."""
    with Image.open(file_path) as image:
        # Mobile photo ghumi hui ho to seedhi kar do
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")
        text = _ocr_image(image).strip()
    return text, "ocr"


def extract_text(file_path: Path, file_type: str) -> tuple[str, str]:
    """File se text nikalta hai. (text, method) wapas deta hai.

    method: "digital_pdf", "ocr", ya "mixed"
    """
    if file_type == "pdf":
        return _extract_pdf(file_path)
    if file_type in ("jpg", "png"):
        return _extract_image(file_path)
    raise ValueError(f"Unsupported file type: {file_type}")