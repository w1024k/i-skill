from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

from base import ConfigError, get_server, load_config, normalize_text, score_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="查询 Jenkins 任务参数。")
    parser.add_argument("--job", required=True, help="任务全名，例如 folder-a/example-pipeline")
    parser.add_argument("--query", help="按参数名、别名、备注做语义匹配。")
    return parser.parse_args()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_parameter_definitions(root: ET.Element) -> List[ET.Element]:
    definitions: List[ET.Element] = []
    for element in root.iter():
        if _local_name(element.tag) == "parameterDefinitions":
            definitions.extend(list(element))
    return definitions


def _param_meta(config: Dict[str, Any], job_name: str, param_name: str) -> Dict[str, Any]:
    return config.get("param_aliases", {}).get(job_name, {}).get(param_name, {})


def _text(element: ET.Element, name: str, default: str = "") -> str:
    for child in element:
        if _local_name(child.tag) == name:
            return (child.text or default).strip()
    return default


def _choices(element: ET.Element) -> List[str]:
    values: List[str] = []
    for child in element.iter():
        if _local_name(child.tag) == "string":
            text = (child.text or "").strip()
            if text:
                values.append(text)
    return values


def extract_parameters(config_xml: str, config: Dict[str, Any], job_name: str) -> List[Dict[str, Any]]:
    root = ET.fromstring(config_xml)
    parameters: List[Dict[str, Any]] = []

    for definition in _find_parameter_definitions(root):
        param_name = _text(definition, "name")
        if not param_name:
            continue

        class_name = definition.attrib.get("plugin", "") or _local_name(definition.tag)
        meta = _param_meta(config, job_name, param_name)
        parameters.append(
            {
                "name": param_name,
                "type": _local_name(definition.tag),
                "class_name": class_name,
                "default": _text(definition, "defaultValue"),
                "description": _text(definition, "description"),
                "choices": _choices(definition),
                "aliases": list(meta.get("aliases", [])),
                "note": str(meta.get("note", "")),
            }
        )

    return parameters


def match_parameters(parameters: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []
    for param in parameters:
        score = score_text(
            query,
            param["name"],
            param.get("description", ""),
            param.get("note", ""),
            *param.get("aliases", []),
        )
        if score <= 0:
            continue
        matches.append({"score": score, **param})

    matches.sort(key=lambda item: (-item["score"], normalize_text(item["name"])))
    return matches


def main() -> int:
    args = parse_args()
    try:
        config = load_config()
        server = get_server()
        config_xml = server.get_job_config(args.job)
        params = extract_parameters(config_xml, config, args.job)
    except ConfigError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {"ok": False, "error": f"查询任务参数失败: {exc}", "job": args.job},
                ensure_ascii=False,
            )
        )
        return 1

    payload: Dict[str, Any] = {
        "ok": True,
        "job": args.job,
        "count": len(params),
    }
    if args.query:
        payload["query"] = args.query
        payload["matches"] = match_parameters(params, args.query)
    else:
        payload["parameters"] = [
            {"index": index, **param}
            for index, param in enumerate(params, start=1)
        ]

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
