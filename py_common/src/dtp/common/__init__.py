"""DTP Platform: Common Utilities."""

from typing import Any

from pydantic import BaseModel


def fastapi_text_example(content: str) -> dict[str, Any]:
    """Returns a JSON object for specifying a plain text response in FastAPI."""
    return {
        "content": {"text/plain": {"example": content}},
    }


def fastapi_json_example(model_instance: BaseModel) -> dict[str, Any]:
    """Returns a JSON object for specifying a JSON response in FastAPI."""
    return {
        "content": {"application/json": {"example": model_instance.model_dump(mode="json")}},
    }
