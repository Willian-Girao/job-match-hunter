import os
from openai import OpenAI, RateLimitError
from dotenv import load_dotenv
from pathlib import Path
import json
import time
from job_match_hunter.data_layer.database import supabase_backend
from job_match_hunter.output_processing import from_cv_json_response

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

# a. loop over prompts for CV parsing
for idx_p, prompt in enumerate(cv_prompt_files):
    # b. loop over JSON schemas
    for idx_j, json_schema in enumerate(cv_schema_files):
        # c. loop over models
        for model_name in models:
            # TODO - need better validation for dir name creating
            # dir holds the formatted model's outputs
            dir_name = model_name.replace('/', '_').replace(':', '.')
            os.makedirs(Path(f'evaluation/model_runs/{dir_name}'), exist_ok=True)

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

                    json_response = json.loads(response.choices[0].message.content)

                    response_as_txt = from_cv_json_response(
                        json_response=json_response,
                        schema_name=response_format['json_schema']['name']
                    )

                    finish_reason = response.choices[0].finish_reason

                except Exception as e:
                    error = f"{type(e).__name__}: {e}"
                    json_response = None
                    response_as_txt = ""

                # Saving model's response to file.
                f_name = f'{idx_p}_{idx_j}_response_{idx}.txt'
                f = open(Path(f'evaluation/model_runs/{dir_name}/{f_name}'), "w", encoding="utf-8")
                f.write(response_as_txt)
                f.close()

                # Saving comparison metrics to file.
                f_name = f'{idx_p}_{idx_j}_metrics_{idx}.txt'
                f = open(Path(f'evaluation/model_runs/{dir_name}/{f_name}'), "w", encoding="utf-8")
                f.write("model: " + str(model_name) + '\n')
                f.write("prompt: " + str(prompt) + '\n')
                f.write("json_schema: " + str(json_schema) + '\n')
                f.write("input: " + str(cv) + '\n')
                f.write("ground_truth: " + str(cv_gts_list[idx]) + '\n')
                f.write("error: " + str(error) + '\n')
                f.write("latency: " + str(latency) + ' (s)' + '\n')
                f.write("cost: " + str(cost) + '\n')
                f.write("prompt_tokens: " + str(prompt_tokens) + '\n')
                f.write("completion_tokens: " + str(completion_tokens) + '\n')
                f.write("finish_reason: " + str(finish_reason) + '\n')
                f.close()

                run_data = {
                    "model": model_name,
                    "prompt": prompt,
                    "json_schema": json_schema,
                    "input": cv,
                    "output": json_response,
                    "ground_truth": cv_gts_list[idx],
                    "error": error,
                    "latency": latency,
                    "cost": cost,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "score": None,
                    "finish_reason": finish_reason
                }

                try:
                    supabase_backend.table("model_runs").insert(run_data).execute()
                    print(f'> `{model_name}` has been logged.')
                except Exception as e:
                    print(f"{type(e).__name__}: {e}")