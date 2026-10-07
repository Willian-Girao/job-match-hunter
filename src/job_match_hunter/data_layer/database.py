import os

from dotenv import load_dotenv
from supabase import Client, create_client

#
# Supabase initialization.
#

load_dotenv()

supabase: Client = create_client(
    os.environ["NEXT_PUBLIC_SUPABASE_URL"],
    os.environ["NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"],
)

# @TODO - remove this, is just a test for the connection.
# Supabase initialization.
#

response = supabase.table("model_validation_runs").select("*").limit(1).execute()
print("> response: ", response)