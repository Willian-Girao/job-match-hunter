from job_match_hunter.ingestion import pdf_to_string, txt_to_string, json_to_dict
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

# 3. JSON ingestion.

json_files = [
    file for file in os.listdir(os.path.join(root, Path('src/job_match_hunter/schemas/match_estimation/')))
    if file.endswith('.json')
]
json_to_dict_args = []

for jsonf in json_files:
    json_to_dict_args.append(
        Path(os.path.join(root, Path('src/job_match_hunter/schemas/match_estimation/'), jsonf))
    )

@pytest.mark.parametrize(
    "json_path", json_to_dict_args
)
def test_json_to_dict(json_path: Path):
    """
    """
    json_dict = json_to_dict(json_path=json_path)

    assert json_dict
    assert json_dict["json_schema"]
    assert json_dict["json_schema"]["schema"]
    assert json_dict["json_schema"]["schema"]["properties"]["score"]
    assert json_dict["json_schema"]["schema"]["properties"]["score_reason"]
    assert json_dict["json_schema"]["schema"]["properties"]["opinion"]
    assert json_dict["json_schema"]["schema"]["properties"]["mandatory_elements"]
    assert json_dict["json_schema"]["schema"]["properties"]["optional_elements"]
    assert json_dict["json_schema"]["schema"]["properties"]["met_elements"]
    assert json_dict["json_schema"]["schema"]["properties"]["unmet_mandatory_elements"]