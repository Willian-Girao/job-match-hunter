import pymupdf

def pdf_to_text(pdf_path: str) -> str:
    """
    pdf_path (str): complete path to the PDF file.

    text (str): string containing the content of the PDF file.
    """

    pdf = pymupdf.open(pdf_path)
    text = ''

    for page in pdf:
        text += page.get_text()

    if not text.strip():
        raise ValueError("No text could be extracted from the PDF.")

    return text