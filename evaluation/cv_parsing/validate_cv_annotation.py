from dotenv import load_dotenv
from pathlib import Path
import os
from collections import defaultdict
import subprocess
from job_match_hunter.data_layer.database import supabase_backend
from job_match_hunter.output_processing import from_cv_json_response

load_dotenv()

response = (
    supabase_backend.table("model_runs")
    .select("model, prompt, json_schema, input, output, score, score_reason, ground_truth")
    .is_("error", "null")
    .not_.is_("score", "null")
    .eq("experiment_type", "CV parsing")
    .eq("finish_reason", "stop")
    .execute()
)

rows = response.data
model_runs = defaultdict()

for row in rows:

    if row["model"] not in model_runs:
        model_runs[row["model"]] = defaultdict()

    if row["prompt"] not in model_runs[row["model"]]:
        model_runs[row["model"]][row["prompt"]] = defaultdict()

    model_runs[row["model"]][row["prompt"]][(row["input"], row["json_schema"])] = (row["score"], row["score_reason"], row["ground_truth"], row["output"])

for model, run_data in model_runs.items():
    for prompt, prompt_run_data in run_data.items():
        for input_, scoring in prompt_run_data.items():
            ground_truth = scoring[2]
            print(f'> model: {model}')
            print(f'> prompt: {prompt}')
            print(f'> input: {input_[0]}')
            print(f'> score: {scoring[0]}%\n')

            with open(Path(f'data/cv_parsing/{ground_truth}'), "r", encoding="utf-8") as f:
                ground_truth_txt = f.read()
        
            output_as_txt = from_cv_json_response(scoring[3])

            subprocess.Popen([
                "notepad.exe",
                Path(f'data/cv_parsing/{ground_truth}')
            ])
        
            print('----------------------------------------------------------------------')
            print(output_as_txt)
            print('----------------------------------------------------------------------')

            print(f'\n> reason: {scoring[1]}\n')
            input('paused...')
            os.system("cls")