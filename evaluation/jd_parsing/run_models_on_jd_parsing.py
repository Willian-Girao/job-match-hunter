import os
from openai import OpenAI, RateLimitError
from dotenv import load_dotenv
from pathlib import Path
import json
import time
from job_match_hunter.data_layer.database import supabase_backend
from job_match_hunter.ingestion import pdf_to_text

load_dotenv()

client = OpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=os.environ['OPENROUTER_API_KEY']
)

project_root = Path(__file__).resolve().parents[2]

# 1. Load test dataset ----------

jd_files = [
    file for file in os.listdir(Path(f'{project_root}/data/jd_parsing/'))
    if not file.endswith('_ground_truth.txt')
]
jd_gts_list = [file for file in os.listdir(Path(f'{project_root}/data/jd_parsing/')) if file.endswith('_ground_truth.txt')] # ground-truth

# 2. Load prompts ----------

jd_prompt_path = Path(f'{project_root}/src/job_match_hunter/prompts/jd_parsing/')
jd_prompt_files = [file for file in os.listdir(jd_prompt_path) if file.endswith('.txt')]

# 3. Load schemas ----------

jd_schema_path = Path(f'{project_root}/src/job_match_hunter/schemas/jd_parsing/')
jd_schema_files = [file for file in os.listdir(jd_schema_path) if file.endswith('.json')]

# 4. Test models ----------

with open(Path(f'{project_root}/evaluation/configs/models_best.txt')) as f:
    models = [line.rstrip('\n') for line in f]

# a. loop over prompts for JD parsing
for idx_p, prompt in enumerate(jd_prompt_files):
    # b. loop over JSON schemas
    for idx_j, json_schema in enumerate(jd_schema_files):
        # c. loop over models
        for model_name in models:
            with open(os.path.join(jd_schema_path, json_schema), encoding="utf-8") as f:
                response_format = json.load(f)

            # d. loop over test samples
            for idx, jd in enumerate(jd_files):

                # Checking if model/prompt/schema/input has already been run.
                response = (
                    supabase_backend.table("model_runs")
                    .select("error")
                    .eq("model", model_name)
                    .eq("prompt", prompt)
                    .eq("json_schema", json_schema)
                    .eq("input", jd)
                    .execute()
                )
                
                if not len(response.data):
                    # Running experiment.
                    print(f'> running - `{model_name}` | `{prompt}` | `{json_schema}` | `{jd}`')

                    jd_txt = pdf_to_text(pdf_path=Path(f'{project_root}/data/jd_parsing/{jd}'))
                    prompt_txt = Path(os.path.join(jd_prompt_path, prompt)).read_text(encoding="utf-8")

                    # e. extract structured data from JD
                    messages = [
                        {
                            "role": "system",
                            "content": prompt_txt
                        },
                        {
                            "role": "user",
                            "content": f"""
                    Extract information from the following JD.

                    JD:
                    {jd_txt}
                    """
                        }
                    ]

                    error = None
                    latency = None
                    cost = None
                    prompt_tokens = None
                    completion_tokens = None
                    finish_reason = None

                    try:
                        for attempt in range(3):
                            # In the case there are rate limits, try a few times.
                            try:
                                start_time = time.perf_counter()
                                response = client.chat.completions.create(
                                    model=model_name,
                                    messages=messages,
                                    temperature=0.0, # https://openrouter.ai/docs/api_reference/parameters#temperature
                                    extra_body={
                                        "provider": {
                                            "require_parameters": True, # make sure only routes to models supporting structured outputs
                                        }
                                    },
                                    response_format=response_format
                                )
                                latency = time.perf_counter() - start_time
                                break
                            except RateLimitError:
                                if attempt == 2:
                                    raise
                                time.sleep(5 * (attempt + 1))
                        
                        # https://openrouter.ai/docs/cookbook/administration/usage-accounting
                        cost = response.usage.cost
                        prompt_tokens = response.usage.prompt_tokens
                        completion_tokens = response.usage.completion_tokens
                        finish_reason = response.choices[0].finish_reason

                        json_response = json.loads(response.choices[0].message.content)

                    except Exception as e:
                        error = f"{type(e).__name__}: {e}"
                        json_response = None

                    run_data = {
                        "model": model_name,
                        "prompt": prompt,
                        "json_schema": json_schema,
                        "input": jd,
                        "output": json_response,
                        "ground_truth": jd_gts_list[idx],
                        "error": error,
                        "latency": latency,
                        "cost": cost,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "score": None,
                        "finish_reason": finish_reason,
                        "experiment_type": "JD parsing"
                    }

                    try:
                        supabase_backend.table("model_runs").insert(run_data).execute()
                    except Exception as e:
                        print(f"{type(e).__name__}: {e}")

                else:
                    print(f'> skipping - `{model_name}` | `{prompt}` | `{json_schema}` | `{jd}`')