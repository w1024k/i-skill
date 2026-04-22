#!/usr/bin/env python
import argparse
import json
import re
import sys


PAIR_START_PATTERN = re.compile(
    r"(?P<key>[A-Za-z_][A-Za-z0-9_\-]*)\s*(?P<op>=|:|是|为)\s*"
)

JOB_PATTERNS = [
    re.compile(r"(?:构建|执行|触发|运行|build)\s+(?P<job>[A-Za-z0-9_./\-]+)", re.IGNORECASE),
    re.compile(r"(?:任务|job|pipeline)\s*(?:是|为|:|=)?\s*(?P<job>[A-Za-z0-9_./\-]+)", re.IGNORECASE),
]

STOPWORDS = {
    "构建",
    "执行",
    "触发",
    "运行",
    "job",
    "pipeline",
    "任务",
    "参数",
    "with",
}


def strip_quotes(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def clean_value(value):
    value = value.strip()
    value = value.strip(",，;；")
    return strip_quotes(value.strip())


def parse_pairs(text):
    pairs = []
    seen = set()
    matches = list(PAIR_START_PATTERN.finditer(text))
    for index, match in enumerate(matches):
        key = match.group("key")
        normalized = key.lower()
        if normalized in STOPWORDS or normalized == "job":
            continue

        value_start = match.end()
        value_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        value = clean_value(text[value_start:value_end])
        if not value or normalized in seen:
            continue
        seen.add(normalized)
        pairs.append(
            {
                "name_hint": key,
                "value": value,
                "source": text[match.start():value_end].strip(),
            }
        )
    return pairs


def parse_job(text):
    for pattern in JOB_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group("job")

    # Fall back to the first folder-qualified or token-like identifier.
    tokens = re.findall(r"[A-Za-z0-9_./\-]+", text)
    for token in tokens:
        lowered = token.lower()
        if lowered in STOPWORDS:
            continue
        if "/" in token or "." in token or "-" in token or "_" in token:
            return token

    for token in tokens:
        if token.lower() not in STOPWORDS:
            return token
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="Free-form user request")
    args = parser.parse_args()

    try:
        payload = {
            "job_hint": parse_job(args.text.strip()),
            "parameter_hints": parse_pairs(args.text),
            "original_text": args.text,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
