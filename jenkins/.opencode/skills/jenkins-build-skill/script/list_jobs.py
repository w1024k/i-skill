from __future__ import annotations

import argparse
import json
import sys

from base import ConfigError, get_server, list_all_jobs, load_config, match_jobs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="列出 Jenkins 所有任务。")
    parser.add_argument("--query", help="按任务名、别名、备注做语义匹配。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config()
        server = get_server()
        jobs = list_all_jobs(server, config)
    except ConfigError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": f"查询 Jenkins 任务失败: {exc}"}, ensure_ascii=False))
        return 1

    if args.query:
        payload = {
            "ok": True,
            "query": args.query,
            "count": len(jobs),
            "matches": match_jobs(jobs, args.query),
        }
    else:
        payload = {
            "ok": True,
            "count": len(jobs),
            "jobs": [
                {"index": index, **job.to_dict()}
                for index, job in enumerate(jobs, start=1)
            ],
        }

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
