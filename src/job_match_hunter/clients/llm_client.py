import datetime
import json
import time
import os
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
import requests
from job_match_hunter.clients.tokenizers import input_tokens_counter

load_dotenv()

class LLMClient:
    """Handle LLM API requests for CV–job matching.

    Requests are handled using OpenAI's (synchronous) client instance.

    Args:
        model_name: OpenRouter model ID.
        prompt: System instructions sent to the model.
        schema: JSON schema defining the expected response structure.
    """
    def __init__(self, model_name: str, prompt: str, schema: dict):
        self.model_name = model_name
        self.prompt = prompt
        self.schema = schema

        self._client = OpenAI(
            base_url='https://openrouter.ai/api/v1',
            api_key=os.environ['OPENROUTER_API_KEY']
        )

        self._context_length = self._get_context_limit()

        self._input_tokens_counter = input_tokens_counter(
            model_name=self.model_name
        )

    def estimate_match(self, cv: str, jd: str, attempts: int=2) -> dict:
        # Current date (helps mode figure out time durations that use `<month> <year> - Present`).
        x = datetime.datetime.now()
        current_date = f'{x.strftime("%B")} {x.strftime("%Y")}'

        # Inputs for the LLM (prompt + CV + JD).
        messages = [
            {
                "role": "system",
                "content": self.prompt
            },
            {
                "role": "user",
                "content": f"""
        Present: {current_date}
        Compare the following CV to the JD.

        CV:
        ###############
        {cv}
        ###############

        JD:
        ###############
        {jd}
        ###############
        """
            }
        ]

        # Validating input to LLM fits in its context window.
        tokens_count = self._input_tokens_counter(
            messages=messages,
            schema=self.schema
        )

        if tokens_count > self._context_length:
            return {} # TODO: need to handle CV/JD being too big for the model; needs handling.

        # Sending request to the LLM.
        try:
            # In the case there are rate limits, try a few times.
            for attempt in range(attempts):
                try:
                    response = self._client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=0.0,
                        extra_body={
                            "provider": {
                                "require_parameters": True,
                            }
                        },
                        response_format=self.schema
                    )
                    break
                except RateLimitError:
                    if attempt == attempts:
                        raise
                    time.sleep(2 * (attempt + 1))

            finish_reason = response.choices[0].finish_reason
            llm_response = json.loads(response.choices[0].message.content)

        except Exception as e:
            raise ValueError(f"{type(e).__name__}: {e}")

        if finish_reason != 'stop':
            return {} # TODO: something went wrong generating the output; needs handling.

        return llm_response

    def _get_context_limit(self) -> int:
        """
        Retrieves the context length size given in OpenRouter's documentation for `model_name`.
    
        Returns:
            Model's context window size.
        """
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"
            },
            timeout=30,
        )
        response.raise_for_status()

        for model in response.json()["data"]:
            if model["id"] == self.model_name:
                return model["context_length"]

        raise ValueError(f"Model not found on OpenRouter: {self.model_name}")