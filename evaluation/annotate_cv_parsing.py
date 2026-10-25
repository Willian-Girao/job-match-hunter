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
    .select("id, input, output, ground_truth, json_schema")
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

for row in rows:
    row_id = row['id']
    input_f = row['input']
    output = row['output']
    json_schema = row['json_schema']
    ground_truth = row['ground_truth']

    output_as_txt = from_cv_json_response(output, json_schema)

    messages = [
        {
            "role": "system",
            "content": """
    You are comparing the OUTPUT of a LLM against a GROUD TRUTH.
    Compare the OUTPUT against the GROUD TRUTH element-by-element, account for semantic 
    equivalence rather than exact wording, and return a score from 0–100.
    The content to be compared is grouped under [Technical Skills], [Professional Experience],
    [Education], and [Languages].
    """
        },
        {
            "role": "user",
            "content": f"""
    Compare the OUTPUT against the GROUD TRUTH.

    OUTPUT:
    {output_as_txt}

    GROUD TRUTH:
    {...}
    """
        }
    ]

    response = client.chat.completions.create(
        model="openai/gpt-5.6-sol",
        messages=messages,
        temperature=0.0,
        extra_body={
            "provider": {
                "require_parameters": True, # make sure only routes to models supporting structured outputs
            }
        },
        response_format=...
    )

    # subprocess.Popen([
    #     "notepad.exe",
    #     Path(f'data/cv_parsing/{ground_truth}')
    # ])

    # response = (
    #     supabase_backend
    #     .table("model_runs")
    #     .update({"score": float(score)})
    #     .eq("id", row_id)
    #     .execute()
    # )