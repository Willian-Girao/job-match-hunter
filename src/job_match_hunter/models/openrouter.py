import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import json

from job_match_hunter.doc_processing import pdf_to_text

# makes the variables in .env accessible.
load_dotenv()

# 0. Instantiate model

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

# 1. PDF to text

cv_as_txt = pdf_to_text(pdf_path=Path('data/job_hunter_dummy_cv.pdf'))

# 2. Prompt loading
prompt = Path("src/job_match_hunter/prompts/cv_extraction_v1.txt").read_text()

# 3. Extract structured information

messages = [
    {
        "role": "system",
        "content": prompt
    },
    {
        "role": "user",
        "content": f"""
Extract relevant structured information from the following CV.

CV:
{cv_as_txt}
"""
    }
]

# TODO - not every model/provider endpoint supports structured outputs!
# TODO - https://openrouter.ai/docs/guides/features/structured-outputs#best-practices
response = client.chat.completions.create(
    model="openai/gpt-5.4",
    messages=messages,
    max_tokens=1000, # TODO - using free tier; need paid for more tokens.
    extra_body={
        "provider": {
            "require_parameters": True, # make sure only routes to models supporting structured outputs
        }
    },
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "structured_cv_information",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "technical_skills": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "professional_experience": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "education": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "languages": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                },
                "required": ["technical_skills", "professional_experience", "education", "languages"],
                "additionalProperties": False,
            }
        }
    }
)

json_response = json.loads(response.choices[0].message.content)

for key, val in json_response.items():
    print(key, ": ")
    for v in val:
        print("- ", v)
    print("\n")