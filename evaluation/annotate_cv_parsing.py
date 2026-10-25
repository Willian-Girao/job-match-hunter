from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
import json
from job_match_hunter.data_layer.database import supabase_backend
from job_match_hunter.ingestion import pdf_to_text
from job_match_hunter.output_processing import from_cv_json_response
import subprocess

load_dotenv()

response = (
    supabase_backend.table("model_runs")
    .select("id, input, output, ground_truth, json_schema, prompt")
    .lte("latency", 5)
    .is_("error", "null")
    .is_("score", "null")
    .eq("experiment_type", "CV parsing")
    .eq("finish_reason", "stop")
    .execute()
)

rows = response.data

client = OpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=os.environ['OPENROUTER_API_KEY']
)

with open(Path('src/job_match_hunter/schemas/annotator/annotator.json'), encoding="utf-8") as f:
    annotator_schema = json.load(f)

for row in rows:
    row_id = row['id']
    input_f = row['input']
    output = row['output']
    json_schema = row['json_schema']
    prompt = row['prompt']
    ground_truth = row['ground_truth']

    with open(Path(f'data/cv_parsing/{ground_truth}'), "r", encoding="utf-8") as f:
        ground_truth_txt = f.read()

    output_as_txt = from_cv_json_response(output, json_schema)

    messages = [
        {
            "role": "system",
            "content": """
    You are comparing the <OUTPUT> of a LLM against a <GROUD TRUTH>.
    Compare the <GROUD TRUTH> against the <OUTPUT> element-by-element, account for semantic 
    equivalence rather than exact wording, and return a score from 0–100.
    The content to be compared is grouped under [Technical Skills], [Professional Experience],
    [Education], and [Languages].
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
        model="openai/gpt-4.1-nano",
        messages=messages,
        temperature=0.0,
        extra_body={
            "provider": {
                "require_parameters": True, # make sure only routes to models supporting structured outputs
            }
        },
        response_format=annotator_schema
    )

    annotator_json_response = json.loads(response.choices[0].message.content)

    subprocess.Popen([
        "notepad.exe",
        Path(f'data/cv_parsing/{ground_truth}')
    ])

    print('###################################')
    print(output_as_txt)
    print('###################################')
    print(json_schema)
    print(prompt)
    print(annotator_json_response)

    input('> paused...')

    # response = (
    #     supabase_backend
    #     .table("model_runs")
    #     .update({"score": float(score)})
    #     .eq("id", row_id)
    #     .execute()
    # )