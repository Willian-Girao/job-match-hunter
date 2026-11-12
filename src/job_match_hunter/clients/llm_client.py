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

    def estimate_match(self, cv: str, jd: str, attempts: int=3) -> dict:
        """Passes `cv` and `jd` to LLM client and prompts it to estimate match.

        Args:
            cv: The CV of a candidate.
            jd: The description of a job vacancy.
            attempts: Number of attempts in case of rate limits.

        Returns:
            Structured output from LLM call.

        Raises:
            ValueError: LLM call returns with `finish_reason` different from `stop`.
            ValueError: Input to the LLM axceeds its context window.
        """
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
            # TODO: need to handle CV/JD being too big for the model.
            raise ValueError(
                f"Input contains {tokens_count} tokens, "
                f"exceeding the model's context limit of {self._context_length}."
            )

        # Sending request to the LLM.
        for attempt in range(attempts):
            # In the case there are rate limits, try a few times.
            try:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.0,
                    seed=0,
                    extra_body={
                        "provider": {
                            "require_parameters": True,
                            "zdr": True
                        }
                    },
                    response_format=self.schema
                )
                break
            except RateLimitError:
                if attempt == attempts:
                    raise
                time.sleep(5 * (attempt + 1))

        finish_reason = response.choices[0].finish_reason
        llm_response = json.loads(response.choices[0].message.content)

        if finish_reason != 'stop':
            raise ValueError(f"LLM replied with `finish_reason` as `{finish_reason}`.")

        return llm_response

    def _get_context_limit(self) -> int:
        """Retrieves the context length size given in OpenRouter's documentation for `model_name`.
    
        Returns:
            Model's context window size.

        Raises:
            ValueError: Model ID not found on OpenRouter models list.
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