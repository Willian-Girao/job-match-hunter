import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import json
import time
from job_match_hunter.data_layer.database import supabase

from job_match_hunter.ingestion import pdf_to_text

load_dotenv()

# TODO - the hardcoded paths should be an env variable.
# TODO - understing using OpenAI Python client for all models (not just from them).
client = OpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=os.environ['OPENROUTER_API_KEY']
)

# 1. Load test dataset ----------

cv_files = [
    file for file in os.listdir(Path('data/cv_parsing/'))
    if file.endswith('.pdf')
] # CVs as text
cv_gts_list = [file for file in os.listdir(Path('data/cv_parsing/')) if file.endswith('.txt')] # ground-truth

# 2. Load prompts ----------

cv_prompt_path = Path('src/job_match_hunter/prompts/cv_parsing/')
cv_prompt_files = [file for file in os.listdir(cv_prompt_path) if file.endswith('.txt')]

# 3. Load schemas ----------

cv_schema_path = Path('src/job_match_hunter/schemas/cv_parsing/')
cv_schema_files = [file for file in os.listdir(cv_schema_path) if file.endswith('.json')]

# 4. Test models ----------

with open(Path('evaluation/configs/models.txt')) as f:
    models = [line.rstrip('\n') for line in f]

# a. loop over models
for model_name in models:
    # b. loop over prompts for CV parsing
    for prompt in cv_prompt_files:
        # c. loop over JSON schemas
        for json_schema in cv_schema_files:
            with open(os.path.join(cv_schema_path, json_schema), encoding="utf-8") as f:
                response_format = json.load(f)

            # d. loop over test samples
            for idx, cv in enumerate(cv_files):
                cv_txt = pdf_to_text(pdf_path=Path(f'data/cv_parsing/{cv}'))
                prompt_txt = Path(os.path.join(cv_prompt_path, prompt)).read_text()

                # e. extract structured data from CV
                messages = [
                    {
                        "role": "system",
                        "content": prompt_txt
                    },
                    {
                        "role": "user",
                        "content": f"""
                Extract relevant structured information from the following CV.

                CV:
                {cv_txt}
                """
                    }
                ]

                error = None
                latency = None
                cost = None
                total_tokens = None

                try:

                    start_time = time.perf_counter()

                    response = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        max_tokens=1000, # TODO - need to figure out what to do with this argument.
                        temperature=0.0, # https://openrouter.ai/docs/api_reference/parameters#temperature
                        extra_body={
                            "provider": {
                                "require_parameters": True, # make sure only routes to models supporting structured outputs
                            }
                        },
                        response_format=response_format
                    )

                    latency = time.perf_counter() - start_time
                    
                    # https://openrouter.ai/docs/cookbook/administration/usage-accounting
                    cost = response.usage.cost
                    total_tokens = response.usage.total_tokens

                    json_response = json.loads(response.choices[0].message.content)

                except OpenAI.APIStatusError as e:
                    error = f"HTTP {e.status_code}: {e}"

                except OpenAI.APIConnectionError as e:
                    error = f"Connection error: {e}"

                except OpenAI.APIError as e:
                    error = f"API error: {e}"

                except Exception as e:
                    error = f"{type(e).__name__}: {e}"

                print('---------- model output ----------\n')
                for key, val in json_response.items():
                    print(key, ": ")
                    for v in val:
                        print("- ", v)
                    print("\n")

                print('---------- meta data ----------\n')
                print('sample: ', cv)
                print('ground-truth: ', cv_gts_list[idx])
                print('latency: ', latency, ' (s)')
                print('error: ', error)
                print('cost: ', cost)
                print('total_tokens: ', total_tokens)

                score = input('\n> score (between 0 and 1): ')

                if float(score) < 0 or float(score) > 1:
                    score = input('\n> score must be between 0 and 1: ')

                run_data = {
                    "model": model_name,
                    "prompt": prompt,
                    "json_schema": json_schema,
                    "input": cv,
                    "ground_truth": cv_gts_list[idx],
                    "error": error,
                    "latency": latency,
                    "cost": cost,
                    "total_tokens": total_tokens,
                    "score": float(score)
                }

                try:
                    supabase.table("model_runs").insert(run_data).execute()
                except Exception as e:
                    print(f"{type(e).__name__}: {e}")