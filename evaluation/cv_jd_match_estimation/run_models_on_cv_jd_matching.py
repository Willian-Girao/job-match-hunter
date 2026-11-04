import os
from openai import OpenAI, RateLimitError
from dotenv import load_dotenv
from pathlib import Path
import json
import time
from job_match_hunter.data_layer.database import supabase_backend
from job_match_hunter.ingestion import pdf_to_text

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

with open(os.path.join(root, Path('evaluation/configs/models_best.txt'))) as f:
    models = [line.rstrip('\n') for line in f]


match_prompt_files = [file for file in os.listdir(prompt_match_path) if file.endswith('.txt')]

match_schema_files = [file for file in os.listdir(schema_match_path) if file.endswith('.json')]

# 2. Compare CVs with JDs ----------

for model_name in models:
    for schema in match_schema_files:
        for prompt in match_prompt_files:
            for cv in cv_files:
                for jd in jd_files:

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

                    json_response = json.loads(response.choices[0].message.content)

                    print(model_name)
                    print(schema)
                    print(prompt)
                    print(cv)
                    print(jd)
                    print('\n')

                    for key, val in json_response.items():
                        print(key, ': ', val, '\n')
    
                    input('...')
                    os.system('cls')