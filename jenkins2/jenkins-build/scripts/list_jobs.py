#!/usr/bin/env python
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


def normalize_job(job, config):
    full_name = job.get("fullname") or job.get("fullName") or job.get("name")
    display_name = job.get("name")
    aliases = config.get("job_aliases", {})
    remarks = config.get("job_remarks", {})
    return {
        "full_name": full_name,
        "display_name": display_name,
        "alias": aliases.get(full_name, ""),
        "remark": remarks.get(full_name, ""),
        "url": job.get("url", ""),
    }


def main():
    try:
        config = load_config()
        validate_config(config)
        client = connect(config)
        jobs = client.get_all_jobs()
        normalized = [normalize_job(job, config) for job in jobs]
        normalized.sort(key=lambda item: item["full_name"])
        for index, item in enumerate(normalized, start=1):
            item["index"] = index
        payload = {"jobs": normalized, "count": len(normalized)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
