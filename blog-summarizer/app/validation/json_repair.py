import json
import re
from typing import Any

from app.validation.schemas import JsonRepairReport


def parse_json_with_repair(raw_output: str) -> tuple[dict[str, Any] | None, JsonRepairReport]:
    try:
        parsed = json.loads(raw_output)
        return _ensure_object(parsed), JsonRepairReport()
    except json.JSONDecodeError as exc:
        initial_error = str(exc)

    repaired_text = _extract_json_object(raw_output)
    if repaired_text is None:
        return None, JsonRepairReport(
            attempted=True,
            repaired=False,
            strategy="extract_outer_json_object",
            error=initial_error,
        )

    try:
        parsed = json.loads(_remove_trailing_commas(repaired_text))
        return _ensure_object(parsed), JsonRepairReport(
            attempted=True,
            repaired=True,
            strategy="extract_outer_json_object_and_remove_trailing_commas",
        )
    except (json.JSONDecodeError, TypeError) as exc:
        return None, JsonRepairReport(
            attempted=True,
            repaired=False,
            strategy="extract_outer_json_object_and_remove_trailing_commas",
            error=str(exc),
        )


def _ensure_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    return None


def _extract_json_object(raw_output: str) -> str | None:
    start = raw_output.find("{")
    end = raw_output.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return raw_output[start : end + 1]


def _remove_trailing_commas(raw_output: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", raw_output)
