#!/usr/bin/env python
import argparse
import json
import sys
from pathlib import Path

import jenkins


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_config(config):
    missing = [key for key in ("base_url", "username", "api_token") if not config.get(key)]
    if missing:
        raise ValueError(
            "Missing Jenkins config values in config.json: " + ", ".join(missing)
        )


def connect(config):
    timeout = config.get("timeout_seconds", 30)
    return jenkins.Jenkins(
        config["base_url"],
        username=config["username"],
        password=config["api_token"],
        timeout=timeout,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True, help="Full Jenkins job name")
    parser.add_argument(
        "--params",
        default="{}",
        help="JSON object with Jenkins build parameters",
    )
    args = parser.parse_args()

    try:
        params = json.loads(args.params)
        if not isinstance(params, dict):
            raise ValueError("--params must decode to a JSON object")

        config = load_config()
        validate_config(config)
        client = connect(config)
        queue_id = client.build_job(args.job, parameters=params)
        payload = {"job": args.job, "parameters": params, "queue_id": queue_id}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
