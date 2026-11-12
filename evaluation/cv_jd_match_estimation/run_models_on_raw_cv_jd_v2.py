import os
from dotenv import load_dotenv
from pathlib import Path
from job_match_hunter.ingestion import pdf_to_string, txt_to_string, json_to_dict, html_to_string
from job_match_hunter.clients.llm_client import LLMClient

load_dotenv()

root = Path(__file__).resolve().parents[2]

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


for schema in match_schema_files:
    for prompt in match_prompt_files:

        llm_client = LLMClient(
            model_name="openai/gpt-4.1-nano",
            prompt=txt_to_string(
                txt_path=Path(os.path.join(root, prompt_match_path, prompt))
            ),
            schema=json_to_dict(
                json_path=Path(os.path.join(root, schema_match_path, schema))
            )
        )
    
        # Requesting LLM to estimate match between CV and JD.
        llm_response = llm_client.estimate_match(
            cv=pdf_to_string(
                pdf_path=Path(os.path.join(root, Path('data/cv_parsing/cv_03_hard.pdf')))
            ),
            jd=html_to_string(
                url='https://ohpen.jobs.personio.com/job/2803224'
            )
        )

        print(f'schema: {schema}')
        print(f'prompt: {prompt}\n\n')
        for key, val in llm_response.items():
            if type(val) != list:
                print(f'{key}: ', val, '\n')
            else:
                print(f'{key}: ', '\n')
                for v in val:
                    print(f'- {v}', '\n')
        input('...')
                
        os.system('cls')