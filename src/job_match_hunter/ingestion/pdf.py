import pymupdf
from pathlib import Path

def pdf_to_text(pdf_path: Path) -> str:
    """
    pdf_path (Path): complete path to the PDF file.

    text (str): string containing the content of the PDF file.
    """

    pdf = pymupdf.open(pdf_path)
    text = ''

    for page in pdf:
        text += page.get_text().strip().replace("\uFFFD", "")

    if not text.strip():
        raise ValueError("No text could be extracted from the PDF.")

    return text