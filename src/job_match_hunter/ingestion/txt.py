from pathlib import Path

def txt_to_string(txt_path: Path) -> str:
    """Extract text from a .txt file.

    Args:
        txt_path: Complete path to the .txt file.

    Returns:
        Extracted text.

    Raises:
        ValueError: No text could be extracted from the .txt file.
    """
    text = txt_path.read_text(encoding="utf-8")

    if not text.strip():
        raise ValueError("No text could be extracted from the .txt file.")

    return text