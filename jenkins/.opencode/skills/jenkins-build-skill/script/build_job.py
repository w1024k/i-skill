from __future__ import annotations

import argparse
import json
import sys
from typing import Dict

from base import ConfigError, get_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="触发 Jenkins 构建任务。")
    parser.add_argument("--job", required=True, help="任务全名，例如 folder-a/example-pipeline")
    parser.add_argument(
        "--params-json",
        default="{}",
        help='JSON 格式参数，例如 \'{"ENV":"test","VERSION":"1.0.0"}\'',
    )
    parser.add_argument(
        "--params-file",
        help='从文件读取 JSON 参数（适用于 Windows 命令行转义问题）',
    )
    parser.add_argument(
        "--param",
        action='append',
        dest='params',
        metavar='KEY=VALUE',
        help='单个参数（可多次使用），例如：--param ENV=test --param VERSION=1.0.0',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    
    # 优先级：--param > --params-file > --params-json
    if args.params:
        # 从 --param KEY=VALUE 构建参数
        params: Dict[str, object] = {}
        for param in args.params:
            if '=' not in param:
                print(json.dumps({"ok": False, "error": f"参数格式错误：{param}，应该为 KEY=VALUE"}, ensure_ascii=False))
                return 1
            key, value = param.split('=', 1)
            params[key.strip()] = value.strip()
    elif args.params_file:
        # 从文件读取
        try:
            with open(args.params_file, 'r', encoding='utf-8') as f:
                params_json = f.read().strip()
        except Exception as exc:
            print(json.dumps({"ok": False, "error": f"读取参数文件失败：{exc}"}, ensure_ascii=False))
            return 1
        
        try:
            params = json.loads(params_json)
            if not isinstance(params, dict):
                raise ValueError("params-json 必须是 JSON 对象。")
        except Exception as exc:
            print(json.dumps({"ok": False, "error": f"参数 JSON 非法：{exc}"}, ensure_ascii=False))
            return 1
    else:
        # 从 --params-json 读取
        try:
            params = json.loads(args.params_json)
            if not isinstance(params, dict):
                raise ValueError("params-json 必须是 JSON 对象。")
        except Exception as exc:
            print(json.dumps({"ok": False, "error": f"参数 JSON 非法：{exc}"}, ensure_ascii=False))
            return 1

    try:
        server = get_server()
        queue_id = server.build_job(args.job, parameters=params)
        print(
            json.dumps(
                {
                    "ok": True,
                    "job": args.job,
                    "parameters": params,
                    "queue_id": queue_id,
                    "message": "构建已触发。",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except ConfigError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {"ok": False, "error": f"触发构建失败: {exc}", "job": args.job, "parameters": params},
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
