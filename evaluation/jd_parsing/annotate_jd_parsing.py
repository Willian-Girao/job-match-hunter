from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
import json
from job_match_hunter.data_layer.database import supabase_backend
from job_match_hunter.output_processing import from_jd_json_response
from collections import defaultdict

load_dotenv()

MAX_LATENCY = 7

root = Path(__file__).resolve().parents[2]

# =================================================================================

response = (
    supabase_backend.table("model_runs")
    .select("id, model, prompt, json_schema, input")
    .lte("latency", MAX_LATENCY)
    .is_("error", "null")
    .eq("experiment_type", "JD parsing")
    .eq("finish_reason", "stop")
    .execute()
)

rows = response.data
valid_rows = []

# 1. Load test dataset ----------

jd_files = [
    file for file in os.listdir(os.path.join(root, Path('data/jd_parsing/')))
    if not file.endswith('_ground_truth.txt')
]

# 2. Load prompts ----------

jd_prompt_path = os.path.join(root, Path('src/job_match_hunter/prompts/jd_parsing/'))
jd_prompt_files = [file for file in os.listdir(jd_prompt_path) if file.endswith('.txt')]

# 3. Load schemas ----------

jd_schema_path = os.path.join(root, Path('src/job_match_hunter/schemas/jd_parsing/'))
jd_schema_files = [file for file in os.listdir(jd_schema_path) if file.endswith('.json')]

expected = {
    (prompt, schema, jd)
    for prompt in jd_prompt_files
    for schema in jd_schema_files
    for jd in jd_files
}   

model_runs = defaultdict(set)

for row in rows:
    model_runs[row["model"]].add(
        (row["prompt"], row["json_schema"], row["input"])
    )

valid_rows = [
    (model, runs)
    for model, runs in model_runs.items()
    if sorted(runs) == sorted(expected)
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
    .eq("experiment_type", "JD parsing")
    .eq("finish_reason", "stop")
    .in_("model", valid_models)
    .execute()
)

rows = response.data

client = OpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=os.environ['OPENROUTER_API_KEY']
)

with open(os.path.join(root, Path('evaluation/configs/annotator_schema.json')), encoding="utf-8") as f:
    annotator_schema = json.load(f)

with open(os.path.join(root, Path('evaluation/configs/jd_annotator_prompt.txt')), encoding="utf-8") as f:
    annotator_prompt = f.read()

for row in rows:
    row_id = row['id']
    model = row['model']
    input_f = row['input']
    output = row['output']
    json_schema = row['json_schema']
    prompt = row['prompt']
    ground_truth = row['ground_truth']

    with open(os.path.join(root, Path('data/jd_parsing', ground_truth)), "r", encoding="utf-8") as f:
        ground_truth_txt = f.read()

    output_as_txt = from_jd_json_response(output)

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
    print('ground truth: ', ground_truth)
    print('prompt: ', prompt)
    print('score: ', annotator_json_response['score'])
    print('reason: ', annotator_json_response['reason'])