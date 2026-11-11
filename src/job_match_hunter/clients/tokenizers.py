from collections.abc import Callable
import tiktoken
import re
import json

def input_tokens_counter(model_name: str) -> Callable[[list, dict], int]:
    """Returns a function, based on `model_name`, that computes total input token count.

    Args:
        model_name: OpenRouter model ID.

    Returns:
        Function computing input token count.

    Raises:
        ValueError: Function not implemented for the given model ID.
    """
    if re.search(r"gpt-4\.1-nano", model_name):
        return load_gpt_4_1_nano_validator
    else:
        raise ValueError(f'Function not implemented for OpenRouter model ID `{model_name}`.')

def load_gpt_4_1_nano_validator(messages: list, schema: dict) -> int:
    """Computes total input token count.

    Args:
        messages: List provided as the `messages` argument to OpenAI's (synchronous) client instance.
        schema: JSON schema defining the expected response structure (`response_format` argument to OpenAI's client instance).

    Returns:
        Total input token count.
    """
    tokenizer = tiktoken.encoding_for_model("gpt-4.1-nano")

    # Encode the content of each message.
    message_tokens = [
        tokenizer.encode(message["content"], disallowed_special=())
        for message in messages
    ]

    # Convert the schema dictionary into text before encoding it.
    schema_text = json.dumps(schema, ensure_ascii=False)
    schema_tokens = tokenizer.encode(schema_text, disallowed_special=())    

    # .encode() returns token IDs; len() gives their count.
    content_token_count = sum(len(tokens) for tokens in message_tokens)
    schema_token_count = len(schema_tokens)

    return content_token_count + schema_token_count