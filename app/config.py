from pathlib import Path

# --- Paths ---

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROMPT = "01_raw_cv_jd_match_v1.txt"
SCHEMA = "01_raw_cv_jd_match_v12.json"

MATCH_PROMPT_PATH = (
    PROJECT_ROOT / "src" / "job_match_hunter" / "prompts" / "match_estimation" / PROMPT
)

MATCH_SCHEMA_PATH = (
    PROJECT_ROOT / "src" / "job_match_hunter" / "schemas" / "match_estimation" / SCHEMA
)

# --- LLM Related ---

MODEL_ID = "openai/gpt-4.1-nano"