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

for row in rows:
    row_id = row['id']
    input_f = row['input']
    output = row['output']
    json_schema = row['json_schema']
    ground_truth = row['ground_truth']

    output_as_txt = from_cv_json_response(output, json_schema)

    print(f'#################### {json_schema} ###########################')
    print(output_as_txt)
    print('###############################################')
    input('...')

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