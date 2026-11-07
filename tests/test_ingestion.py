from job_match_hunter.ingestion import pdf_to_string, txt_to_string
from pathlib import Path
import os
import pytest

root = Path(__file__).resolve().parents[1]

# 1. PDF ingestion.

cv_files = [
    file for file in os.listdir('./')
    if file.endswith('.txt') and file.startswith('cv_0')
]
pdf_to_string_args = []

for cv in cv_files:
    pdf_to_string_args.append(
        (
            Path(os.path.join('./', cv)).read_text(encoding="utf-8"),
            Path(os.path.join(root, 'data/cv_parsing/', cv.replace('.txt', '.pdf')))
        )
    )

@pytest.mark.parametrize(
    "pdf_as_string, pdf_path", pdf_to_string_args
)
def test_pdf_to_text(pdf_as_string: str, pdf_path: Path):
    """
    """
    cv_txt = pdf_to_string(pdf_path=pdf_path)

    assert cv_txt == pdf_as_string

# 2. TXT ingestion.

prompt_files = [
    file for file in os.listdir(os.path.join(root, Path('src/job_match_hunter/prompts/match_estimation/')))
    if file.endswith('.txt')
]
text_to_string_args = []

for prompt in prompt_files:
    text_to_string_args.append(
        Path(os.path.join(root, Path('src/job_match_hunter/prompts/match_estimation/'), prompt))
    )

@pytest.mark.parametrize(
    "txt_path", text_to_string_args
)
def test_txt_to_string(txt_path: Path):
    """
    """
    prompt_txt = txt_to_string(txt_path=txt_path)

    assert prompt_txt
    assert prompt_txt != ''