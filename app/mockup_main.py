from job_match_hunter.clients.llm_client import LLMClient
from pathlib import Path
import json
from job_match_hunter.ingestion import pdf_to_string, txt_to_string

root = Path(__file__).resolve().parent

prompt_path = Path(f'{root}/src/job_match_hunter/prompts/match_estimation/01_raw_cv_jd_match.txt')
schema_path = Path(f'{root}/src/job_match_hunter/schemas/match_estimation/raw_cv_jd_match.json')

cv = pdf_to_string(
    pdf_path=Path(f'{root}/data/cv_parsing/cv_01_easy.pdf')
)

jd = txt_to_string(
    txt_path=Path(f'{root}/data/jd_parsing/jd_03_hard.txt')
)

prompt = Path(prompt_path).read_text(encoding="utf-8")
with open(schema_path, encoding="utf-8") as f:
    schema = json.load(f)

llm_client = LLMClient(
    model_name="openai/gpt-4.1-nano",
    prompt=prompt,
    schema=schema,
)

llm_response = llm_client.estimate_match(
    cv=cv,
    jd=jd
)

for key, val in llm_response.items():
    print(key, val, '\n')