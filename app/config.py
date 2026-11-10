from pathlib import Path

# --- Paths ---

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MATCH_PROMPT_PATH = (
    PROJECT_ROOT / "src" / "job_match_hunter" / "prompts" / "match_estimation" / "01_raw_cv_jd_match.txt"
)

MATCH_SCHEMA_PATH = (
    PROJECT_ROOT / "src" / "job_match_hunter" / "schemas" / "match_estimation" / "raw_cv_jd_match.json"
)

# --- LLM Related ---

MODEL_ID = "openai/gpt-4.1-nano"