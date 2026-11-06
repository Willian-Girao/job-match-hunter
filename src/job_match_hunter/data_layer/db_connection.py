from database import supabase

response = supabase.table("model_validation_runs").select("*").limit(1).execute()
print("> response: ", response)