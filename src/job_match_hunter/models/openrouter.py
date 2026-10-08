import os
from openai import OpenAI
from dotenv import load_dotenv

# makes the variables in .env accessible.
load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

response = client.chat.completions.create(
    model="openai/gpt-5.4",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    max_tokens=500
)

print(response.choices[0].message.content)