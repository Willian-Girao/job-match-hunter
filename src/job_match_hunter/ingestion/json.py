from pathlib import Path
import json

def json_to_dict(json_path: Path) -> dict:
    """Loads a JSON object from file.

    Args:
        json_path: Complete path to the JSON file.

    Returns:
        Loaded JSON file.

    Raises:
        ValueError: When an empty JSON is loaded.
    """
    with open(json_path, encoding="utf-8") as f:
        loaded_json = json.load(f)

    if not loaded_json:
        raise ValueError("Could not load JSON file.")

    return loaded_json