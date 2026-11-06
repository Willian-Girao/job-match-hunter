from dotenv import load_dotenv
from job_match_hunter.data_layer.database import supabase_backend

load_dotenv()

for MODEL_NAME in [
    "inception/mercury-2",
    "openai/gpt-4.1-nano",
    "openai/gpt-oss-safeguard-20b",
    ]:

    response = (
        supabase_backend.table("model_runs")
        .select("prompt, input, latency, score, finish_reason, error")
        .eq("model", MODEL_NAME)
        .execute()
    )

    rows = response.data

    print(f"model: {MODEL_NAME}")
    for row in rows:
        if row["latency"] > 5 or row["error"] != None:
            print('prompt: ', row["prompt"])
            print('input: ', row["input"])
            print('latency: ', row["latency"])
            print('score: ', row["score"])
            print('finish_reason: ', row["finish_reason"])
            print('error: ', row["error"][:20] if row["error"] != None else row["error"])
            print('\n\n')