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


def parse_params(job_info, config, job_name):
    aliases = config.get("param_aliases", {}).get(job_name, {})
    remarks = config.get("param_remarks", {}).get(job_name, {})
    properties = job_info.get("property", [])
    definitions = []
    for prop in properties:
        parameter_definitions = prop.get("parameterDefinitions", [])
        for definition in parameter_definitions:
            item = {
                "name": definition.get("name", ""),
                "type": definition.get("type", ""),
                "default": definition.get("defaultParameterValue", {}).get("value"),
                "description": definition.get("description", ""),
                "choices": definition.get("choices", []),
                "alias": aliases.get(definition.get("name", ""), ""),
                "remark": remarks.get(definition.get("name", ""), ""),
            }
            definitions.append(item)
    return definitions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True, help="Full Jenkins job name")
    args = parser.parse_args()

    try:
        config = load_config()
        validate_config(config)
        client = connect(config)
        job_info = client.get_job_info(args.job, depth=2, fetch_all_builds=False)
        params = parse_params(job_info, config, args.job)
        payload = {"job": args.job, "parameters": params, "count": len(params)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
