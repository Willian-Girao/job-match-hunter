from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
import json
from job_match_hunter.data_layer.database import supabase_backend
from job_match_hunter.output_processing import from_cv_json_response
from collections import defaultdict

load_dotenv()

MAX_LATENCY = 5

# =================================================================================

response = (
    supabase_backend.table("model_runs")
    .select("id, model, prompt, json_schema, input")
    .lte("latency", MAX_LATENCY)
    .is_("error", "null")
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

valid_models = [row[0] for row in valid_rows]
print(f'Valid models: {valid_models}')

# =================================================================================

response = (
    supabase_backend.table("model_runs")
    .select("id, input, output, ground_truth, json_schema, prompt, json_schema, model")
    .lte("latency", MAX_LATENCY)
    .is_("error", "null")
    .is_("score", "null")
    .eq("experiment_type", "CV parsing")
    .eq("finish_reason", "stop")
    .in_("model", valid_models)
    .execute()
)

rows = response.data

client = OpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=os.environ['OPENROUTER_API_KEY']
)

with open(Path('evaluation/configs/annotator_schema.json'), encoding="utf-8") as f:
    annotator_schema = json.load(f)

with open(Path('evaluation/configs/annotator_prompt.txt'), encoding="utf-8") as f:
    annotator_prompt = f.read()

for row in rows:
    row_id = row['id']
    model = row['model']
    input_f = row['input']
    output = row['output']
    json_schema = row['json_schema']
    prompt = row['prompt']
    ground_truth = row['ground_truth']

    with open(Path(f'data/cv_parsing/{ground_truth}'), "r", encoding="utf-8") as f:
        ground_truth_txt = f.read()

    output_as_txt = from_cv_json_response(output)

    messages = [
        {
            "role": "system",
            "content": f"""
    {annotator_prompt}
    """
        },
        {
            "role": "user",
            "content": f"""
    Compare the <GROUD TRUTH> against the <OUTPUT>.

    <GROUD TRUTH>:
    {ground_truth_txt}

    <OUTPUT>:
    {output_as_txt}
    """
        }
    ]

    response = client.chat.completions.create(
        model="openai/gpt-5.6-sol",
        messages=messages,
        extra_body={
            "provider": {
                "require_parameters": True, # make sure only routes to models supporting structured outputs
            }
        },
        response_format=annotator_schema
    )

    annotator_json_response = json.loads(response.choices[0].message.content)

    response = (
        supabase_backend
        .table("model_runs")
        .update({
            "score": float(annotator_json_response['score']),
            "score_reason": annotator_json_response['reason']
        })
        .eq("id", row_id)
        .execute()
    )

    print('\n\nmodel: ', model)
    print('input: ', input_f)
    print('prompt: ', prompt)
    print('score: ', annotator_json_response['score'])
    print('reason: ', annotator_json_response['reason'])