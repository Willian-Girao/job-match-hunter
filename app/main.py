from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from typing import Any
from pathlib import Path
import json
from job_match_hunter.ingestion import pdf_to_string, txt_to_string
from job_match_hunter.clients.llm_client import LLMClient

# --- Constants ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]

prompt = Path(
    Path(f'{PROJECT_ROOT}/src/job_match_hunter/prompts/match_estimation/01_raw_cv_jd_match.txt')
).read_text(encoding="utf-8")

with open(
    Path(f'{PROJECT_ROOT}/src/job_match_hunter/schemas/match_estimation/raw_cv_jd_match.json'),
    encoding="utf-8"
    ) as f:
    schema = json.load(f)

llm_client = LLMClient(
    model_name="openai/gpt-4.1-nano",
    prompt=prompt,
    schema=schema,
)

# --- FastAPI App ---
app = FastAPI()

# --- Pydantic Models ---
class PredictionResponse(BaseModel):
    """
    Sources:
        https://pydantic.dev/docs/validation/dev/concepts/json/
        https://pydantic.dev/docs/validation/2.0/usage/model_config/
    """
    model_config = ConfigDict(strict=True) # TODO: this might not be necessary.

    score: float
    score_reason: str
    opinion: str
    mandatory_elements: list | None
    optional_elements: list | None
    met_elements: list | None
    unmet_mandatory_elements: list | None

class PredictionRequest(BaseModel):
    """
    """
    cv_file: str
    jd_url: str

# --- API endpoints ---
@app.get("/")
async def root():
    return {"message": "I'm alive!"}

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest) -> dict:
    """
    Sources:
        https://fastapi.tiangolo.com/tutorial/response-model/#response-model-parameter
    """
    # Converting CV/JD into input string for the LLM.
    # TODO: CV and JD temporarilly load here but they'll eventually be sent via the request.
    cv = pdf_to_string(
        pdf_path=Path(f'{PROJECT_ROOT}/data/cv_parsing/cv_01_easy.pdf')
    )

    jd = txt_to_string(
        txt_path=Path(f'{PROJECT_ROOT}/data/jd_parsing/jd_03_hard.txt')
    )

    # Requesting LLM to estimate match between CV and JD.
    llm_response = llm_client.estimate_match(
        cv=cv,
        jd=jd
    )

    return llm_response