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

supabase_backend: Client = create_client(
    os.environ["NEXT_PUBLIC_SUPABASE_URL"],
    os.environ["SUPABASE_SECRET_KEY"],
)