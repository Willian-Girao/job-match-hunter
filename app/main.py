from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field
from typing import Any
from pathlib import Path
from job_match_hunter.ingestion import pdf_to_string, txt_to_string, json_to_dict
from job_match_hunter.clients.llm_client import LLMClient
from config import PROJECT_ROOT, MATCH_PROMPT_PATH, MATCH_SCHEMA_PATH, MODEL_ID

# --- Constants ---
llm_client = LLMClient(
    model_name=MODEL_ID,
    prompt=txt_to_string(
        txt_path=MATCH_PROMPT_PATH
    ),
    schema=json_to_dict(
        json_path=MATCH_SCHEMA_PATH
    )
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
    model_config = ConfigDict(
        strict=True
    ) # helps in detecting unexpected output types instead of silently converting them.

    score: float = Field(ge=0, le=100)
    score_reason: str
    opinion: str
    mandatory_elements: list[str] | None
    optional_elements: list[str] | None
    met_elements: list[str] | None
    unmet_mandatory_elements: list[str] | None

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
async def predict(request: PredictionRequest) -> dict[str, Any]:
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