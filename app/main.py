from fastapi import FastAPI, File, Form, UploadFile
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, UrlConstraints
from typing import Any, Annotated
from job_match_hunter.ingestion import pdf_bytes_to_string, txt_to_string, json_to_dict, html_to_string
from job_match_hunter.clients.llm_client import LLMClient
from config import MATCH_PROMPT_PATH, MATCH_SCHEMA_PATH, MODEL_ID

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

HttpsUrl = Annotated[
    HttpUrl,
    UrlConstraints(allowed_schemes=["https"]),
] # More on URL validation and constraints: https://pydantic.dev/docs/validation/latest/api/pydantic/networks/

# --- API endpoints ---
@app.get("/")
async def root():
    return {"message": "I'm alive!"}

@app.post("/predict", response_model=PredictionResponse)
def predict(
    cv_file: Annotated[UploadFile, File()],
    jd_url: Annotated[HttpsUrl, Form()]
) -> dict[str, Any]:
    """Requests the LLMClient to evaluate the match between a CV and a job description (JD).

    The CV (.pdf file) is converted to text. The JD's HTML is parsed for its content and converted
    into text. Both texts are given to the LLMClient, which generates a match estimation and reasoning.

    Args:
        cv_file: A .pdf file.
        jd_url: An URL for a JD.

    Returns:
        Structured output from LLMClient.

    Sources:
        https://fastapi.tiangolo.com/tutorial/response-model/#response-model-parameter
        https://fastapi.tiangolo.com/tutorial/request-forms-and-files/
    """
    # Converting CV/JD into input string for the LLM.
    cv = pdf_bytes_to_string(
        pdf_bytes=cv_file.file.read()
    )

    jd = html_to_string(
        url=str(jd_url)
    )

    # Requesting LLM to estimate match between CV and JD.
    llm_response = llm_client.estimate_match(
        cv=cv,
        jd=jd
    )

    return llm_response