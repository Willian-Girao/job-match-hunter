from job_match_hunter.ingestion import pdf_to_text
from pathlib import Path
import os
import pytest

root = Path(__file__).resolve().parents[1]

cv_files = [
    file for file in os.listdir('./')
    if file.endswith('.txt') and file.startswith('cv_0')
]

pdf_to_text_args = []

for cv in cv_files:
    pdf_to_text_args.append(
        (
            Path(os.path.join('./', cv)).read_text(encoding="utf-8"),
            Path(os.path.join(root, 'data/cv_parsing/', cv.replace('.txt', '.pdf')))
        )
    )

@pytest.mark.parametrize(
    "pdf_as_string, pdf_path", pdf_to_text_args
)
def test_pdf_to_text(pdf_as_string: str, pdf_path: Path):
    """
    """
    cv_txt = pdf_to_text(pdf_path=pdf_path)

    assert cv_txt == pdf_as_string