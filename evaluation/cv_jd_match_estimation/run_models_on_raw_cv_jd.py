import os
from openai import OpenAI, RateLimitError
from dotenv import load_dotenv
from pathlib import Path
import json
import time
from job_match_hunter.data_layer.database import supabase_backend
from job_match_hunter.ingestion import pdf_to_text
import datetime

x = datetime.datetime.now()
present_date = f'{x.strftime("%B")} {x.strftime("%Y")}'

load_dotenv()

root = Path(__file__).resolve().parents[2]

client = OpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=os.environ['OPENROUTER_API_KEY']
)

prompt_match_path = os.path.join(root, Path('src/job_match_hunter/prompts/match_estimation/'))
schema_match_path = os.path.join(root, Path('src/job_match_hunter/schemas/match_estimation/'))

# 1. Load CVs, JDs, models' names, prompts, and schemas ----------

cv_files = [
    file for file in os.listdir(os.path.join(root, Path('data/cv_parsing/')))
    if file.endswith('.pdf')
]

jd_files = [
    file for file in os.listdir(os.path.join(root, Path('data/jd_parsing/')))
    if not file.endswith('_ground_truth.txt')
]

with open(os.path.join(root, Path('evaluation/configs/models_v1.txt'))) as f:
    models = [line.rstrip('\n') for line in f]


match_prompt_files = [file for file in os.listdir(prompt_match_path) if file.endswith('.txt')]

match_schema_files = [file for file in os.listdir(schema_match_path) if file.endswith('.json')]

# 2. Compare CVs with JDs ----------

for model_name in models:
    for schema in match_schema_files:
        for prompt in match_prompt_files:
            for cv in cv_files:
                for jd in jd_files:

                    # Checking if model/prompt/schema/input has already been run.
                    response = (
                        supabase_backend.table("match_estimation")
                        .select("id")
                        .eq("model", model_name)
                        .eq("prompt", prompt)
                        .eq("json_schema", schema)
                        .eq("cv_input", cv)
                        .eq("jd_input", jd)
                        .execute()
                    )
                    
                    if not len(response.data):
                        # Running experiment.
                        print(f'> running - `{model_name}` | `{prompt}` | `{cv}` | `{jd}`')

                        jd_txt = Path(os.path.join(root, Path('data/jd_parsing', jd))).read_text(encoding="utf-8")
                        cv_txt = pdf_to_text(pdf_path=os.path.join(root, Path('data/cv_parsing'), cv))

                        prompt_txt = Path(os.path.join(prompt_match_path, prompt)).read_text(encoding="utf-8")
                        with open(os.path.join(schema_match_path, schema), encoding="utf-8") as f:
                            response_format = json.load(f)

                        messages = [
                            {
                                "role": "system",
                                "content": prompt_txt
                            },
                            {
                                "role": "user",
                                "content": f"""
                        Present: {present_date}
                        Compare the following CV to the JD.

                        CV:
                        ###############
                        {cv_txt}
                        ###############

                        JD:
                        ###############
                        {jd_txt}
                        ###############
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
                                        temperature=0.0,
                                        extra_body={
                                            "provider": {
                                                "require_parameters": True,
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
                            "json_schema": schema,
                            "cv_input": cv,
                            "jd_input": jd,
                            "output": json_response,
                            "error": error,
                            "latency": latency,
                            "cost": cost,
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "score": None,
                            "finish_reason": finish_reason,
                            "experiment_type": "raw CV-JD matching"
                        }
    
                        try:
                            supabase_backend.table("match_estimation").insert(run_data).execute()
                        except Exception as e:
                            print(f"{type(e).__name__}: {e}")

                    else:
                        print(f'> skipping - `{model_name}` | `{prompt}` | `{cv}` | `{jd}`')
                    
                    os.system('cls')