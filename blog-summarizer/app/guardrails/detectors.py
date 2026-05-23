import re

from app.guardrails.schemas import GuardrailFinding

PROMPT_INJECTION_PATTERNS = {
    "ignore_previous_instructions": r"\b(ignore|forget|disregard)\b.{0,40}\b(previous|prior|above|system|developer)\b.{0,40}\b(instructions?|prompt|rules?)\b",
    "reveal_system_prompt": r"\b(show|print|reveal|repeat|dump|leak)\b.{0,40}\b(system prompt|hidden prompt|developer message|instructions?)\b",
    "role_override": r"\b(you are now|act as|pretend to be)\b.{0,60}\b(system|developer|admin|root)\b",
    "jailbreak_marker": r"\b(DAN|jailbreak|developer mode|unfiltered mode|god mode)\b",
    "tool_exfiltration": r"\b(call|use|invoke)\b.{0,40}\b(tool|function|browser|shell|terminal)\b.{0,40}\b(secret|key|token|env)\b",
}

MALICIOUS_INPUT_PATTERNS = {
    "secret_exfiltration": r"\b(api[_ -]?key|password|secret|token|credential|private key)\b",
    "command_injection": r"(\brm\s+-rf\b|\bdel\s+/[sq]\b|;|\|\||&&|`|\$\()",
    "script_payload": r"(<script\b|javascript:|onerror\s*=|onload\s*=)",
    "sql_injection": r"(\bunion\s+select\b|\bdrop\s+table\b|\bor\s+1\s*=\s*1\b)",
}

TOXIC_CONTENT_PATTERNS = {
    "harassment": r"\b(idiot|stupid|worthless)\b",
    "violence": r"\b(kill|murder|attack)\b",
    "hate": r"\bhate\b.{0,30}\b(group|people|race|religion)\b",
}


def detect_prompt_injection(text: str) -> list[GuardrailFinding]:
    return _detect_patterns(text, PROMPT_INJECTION_PATTERNS, base_score=0.35)


def detect_malicious_input(text: str) -> list[GuardrailFinding]:
    return _detect_patterns(text, MALICIOUS_INPUT_PATTERNS, base_score=0.25)


def detect_toxic_content(text: str) -> list[GuardrailFinding]:
    return _detect_patterns(text, TOXIC_CONTENT_PATTERNS, base_score=0.25)


def detect_token_abuse(estimated_tokens: int, max_tokens: int) -> list[GuardrailFinding]:
    if estimated_tokens <= max_tokens:
        return []
    return [
        GuardrailFinding(
            code="token_abuse",
            message="Input exceeds the configured token budget.",
            score=min(1.0, estimated_tokens / max_tokens - 1.0),
            evidence=[f"estimated_tokens={estimated_tokens}", f"max_tokens={max_tokens}"],
        )
    ]


def _detect_patterns(
    text: str,
    patterns: dict[str, str],
    base_score: float,
) -> list[GuardrailFinding]:
    findings: list[GuardrailFinding] = []
    for code, pattern in patterns.items():
        matches = re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if matches:
            evidence = [str(match)[:160] for match in matches[:3]]
            findings.append(
                GuardrailFinding(
                    code=code,
                    message=f"Detected {code.replace('_', ' ')} signal.",
                    score=min(1.0, base_score + 0.1 * (len(matches) - 1)),
                    evidence=evidence,
                )
            )
    return findings
