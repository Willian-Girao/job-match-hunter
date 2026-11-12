import pymupdf
from pathlib import Path

def pdf_to_string(pdf_path: Path) -> str:
    """Extract text from a PDF file.

    Args:
        pdf_path: Complete path to the PDF file.

    Returns:
        Extracted text.

    Raises:
        ValueError: No text could be extracted from the PDF.
    """
    text = ""

    with pymupdf.open(pdf_path) as pdf:
        for page in pdf:
            text += page.get_text().strip().replace("\uFFFD", "")

    if not text.strip():
        raise ValueError("No text could be extracted from the PDF.")

    return text

def pdf_bytes_to_string(pdf_bytes: bytes) -> str:
    """Extract text from PDF contents supplied as bytes.

    Args:
        pdf_bytes: The PDF file.

    Returns:
        Extracted text.

    Raises:
        ValueError: No text could be extracted from the PDF.
    """
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
        pages = [
            page.get_text().strip().replace("\uFFFD", "")
            for page in pdf
        ]

    text = "\n\n".join(pages)

    if not text.strip():
        raise ValueError("No text could be extracted from the PDF.")

    return text