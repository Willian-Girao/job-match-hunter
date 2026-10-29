from dotenv import load_dotenv
from pathlib import Path
import os
from collections import defaultdict
from job_match_hunter.data_layer.database import supabase_backend

load_dotenv()

response = (
    supabase_backend.table("model_runs")
    .select("id, model, prompt, json_schema, input")
    .lte("latency", 10)
    .is_("error", "null")
    .is_("score", "null")
    .eq("experiment_type", "CV parsing")
    .eq("finish_reason", "stop")
    .execute()
)

rows = response.data
valid_rows = []

# 1. Load test dataset ----------

cv_files = [
    file for file in os.listdir(Path('data/cv_parsing/'))
    if file.endswith('.pdf')
]

# 2. Load prompts ----------

cv_prompt_path = Path('src/job_match_hunter/prompts/cv_parsing/')
cv_prompt_files = [file for file in os.listdir(cv_prompt_path) if file.endswith('.txt')]

# 3. Load schemas ----------

cv_schema_path = Path('src/job_match_hunter/schemas/cv_parsing/')
cv_schema_files = [file for file in os.listdir(cv_schema_path) if file.endswith('.json')]

expected = {
    (prompt, schema, cv)
    for prompt in cv_prompt_files
    for schema in cv_schema_files
    for cv in cv_files
}   

model_runs = defaultdict(set)

for row in rows:
    model_runs[row["model"]].add(
        (row["prompt"], row["json_schema"], row["input"])
    )

valid_rows = [
    (model, runs)
    for model, runs in model_runs.items()
    if runs == expected
]

print(f'Valid models: {len(valid_rows)}')
for row in valid_rows:
    print(row[0])