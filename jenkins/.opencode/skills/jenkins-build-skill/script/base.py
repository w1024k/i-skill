from __future__ import annotations

import json
import requests
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import jenkins
except ModuleNotFoundError:  # pragma: no cover
    jenkins = None


class ConfigError(RuntimeError):
    pass


@dataclass
class JobMeta:
    full_name: str
    path: str
    name: str
    url: str
    color: Optional[str]
    aliases: List[str]
    note: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "full_name": self.full_name,
            "path": self.path,
            "name": self.name,
            "url": self.url,
            "color": self.color,
            "aliases": self.aliases,
            "note": self.note,
        }


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def config_path() -> Path:
    return skill_root() / "config.json"


def load_config() -> Dict[str, Any]:
    path = config_path()
    if not path.exists():
        raise ConfigError(
            f"未找到配置文件: {path}。请先创建 config.json 并填写 Jenkins 连接信息。"
        )

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    required = ["jenkins_url", "username", "password"]
    missing = [key for key in required if not str(data.get(key, "")).strip()]
    if missing:
        raise ConfigError(
            "config.json 未完成配置，缺少字段: "
            + ", ".join(missing)
            + f"。请编辑 {path} 后再使用。"
        )

    data.setdefault("job_aliases", {})
    data.setdefault("param_aliases", {})
    return data


def get_server() -> jenkins.Jenkins:
    config = load_config()
    if jenkins is None:
        raise ConfigError("未安装 python-jenkins。请先安装依赖后再使用该 skill。")
    server = jenkins.Jenkins(
        config["jenkins_url"],
        username=config["username"],
        password=config["password"],
    )
    session = requests.Session()
    session.verify = False  # 关闭 SSL 校验
    # 替换底层 session（关键）
    server._session = session
    return server


def _job_meta(config: Dict[str, Any], full_name: str) -> Dict[str, Any]:
    return config.get("job_aliases", {}).get(full_name, {})


def job_full_name(job: Dict[str, Any]) -> str:
    return job.get("fullname") or job.get("fullName") or job["name"]


def normalize_text(value: str) -> str:
    return "".join(str(value).strip().lower().split())


def score_text(query: str, *candidates: str) -> int:
    normalized_query = normalize_text(query)
    if not normalized_query:
        return 0

    score = 0
    for candidate in candidates:
        text = normalize_text(candidate)
        if not text:
            continue
        if text == normalized_query:
            score = max(score, 100)
        elif normalized_query in text:
            score = max(score, 80)
        elif text in normalized_query:
            score = max(score, 60)
    return score


def list_all_jobs(server: jenkins.Jenkins, config: Dict[str, Any]) -> List[JobMeta]:
    jobs: List[JobMeta] = []
    seen: set[str] = set()

    getter = getattr(server, "get_all_jobs", None)
    if callable(getter):
        raw_jobs = getter()
    else:
        raw_jobs = server.get_jobs(folder_depth=10, folder_depth_per_request=10)

    for current in raw_jobs:
        full_name = job_full_name(current)
        if full_name in seen:
            continue
        seen.add(full_name)

        class_name = current.get("_class", "")
        if "com.cloudbees.hudson.plugins.folder.Folder" in class_name:
            continue

        meta = _job_meta(config, full_name)
        jobs.append(
            JobMeta(
                full_name=full_name,
                path=full_name,
                name=current["name"],
                url=current.get("url", ""),
                color=current.get("color"),
                aliases=list(meta.get("aliases", [])),
                note=str(meta.get("note", "")),
            )
        )

    jobs.sort(key=lambda item: item.full_name.lower())
    return jobs


def match_jobs(jobs: List[JobMeta], query: str) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []
    for job in jobs:
        score = score_text(query, job.full_name, job.name, job.note, *job.aliases)
        if score <= 0:
            continue
        matches.append({"score": score, **job.to_dict()})

    matches.sort(key=lambda item: (-item["score"], item["full_name"].lower()))
    return matches
