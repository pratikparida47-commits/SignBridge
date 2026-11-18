import json


def safe_script_json(value: str) -> str:
    """Serialize a string for an inline script without raw HTML delimiters."""
    return (
        json.dumps(value)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
