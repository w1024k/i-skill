---
name: jenkins-build
description: Trigger and inspect Jenkins build jobs through predefined python-jenkins scripts. Use when Codex needs to list Jenkins jobs, traverse nested folders to find buildable tasks, show aliases or remarks for jobs and parameters, inspect pipeline parameters, confirm selected job and parameters with the user, or launch a Jenkins build after explicit confirmation.
---

# Jenkins Build

Use the bundled scripts instead of reimplementing Jenkins API calls.

## Workflow

1. Read `config.json` before doing anything else.
2. If `base_url`, `username`, or `api_token` is missing, stop and tell the user to configure `config.json`.
3. If the user supplied a free-form request that may contain both job and parameters, run `scripts/parse_request.py --text <user-request>` first.
4. Run `scripts/list_jobs.py` and match the parsed job candidate or the explicit user choice against `full_name`, `display_name`, and `alias`.
5. If the user did not identify a job, show the returned jobs with index, full path, display name, alias, and remark when present.
6. Accept either a job index or a job name from the user.
7. After the job is identified, run `scripts/get_job_params.py --job <job-full-name>`.
8. Show every available parameter with name, type, default, choices, alias, and remark when present.
9. If `parse_request.py` returned parameter candidates, match them against the real Jenkins parameter definitions by parameter name first, then by alias.
10. If any parsed parameter cannot be matched or the value is ambiguous, ask the user instead of guessing.
11. Before triggering a build, always send a concise confirmation that includes:
   - the resolved Jenkins job full name
   - the selected parameters and values
12. Only after the user explicitly confirms, run `scripts/build_job.py --job <job-full-name> --params '<json>'`.

## Matching Rules

- Prefer exact match on Jenkins `full_name`.
- Fall back to exact match on `display_name`.
- Fall back to exact match on `alias`.
- For parsed free-form requests, treat the parser output as hints, not final truth.
- If multiple jobs or parameters match, do not guess. Show the candidates and ask the user to choose.
- Preserve folder-qualified names. Do not collapse `folder-a/job-x` and `folder-b/job-x`.

## Script Outputs

- Treat the script outputs as source of truth.
- Expect JSON from all scripts.
- If a script reports an error, surface the error directly and stop the workflow.

## Bundled Files

- `config.json`: Jenkins connection settings plus optional alias and remark metadata.
- `scripts/list_jobs.py`: Enumerate jobs across nested folders.
- `scripts/parse_request.py`: Extract a job hint and parameter hints from a free-form user request.
- `scripts/get_job_params.py`: Read parameter definitions for one job.
- `scripts/build_job.py`: Trigger a Jenkins build after explicit confirmation.

## Metadata Conventions In `config.json`

- `job_aliases`: map Jenkins full job name to a short alias shown to the user.
- `job_remarks`: map Jenkins full job name to a human-readable note.
- `param_aliases`: map job full name to per-parameter aliases.
- `param_remarks`: map job full name to per-parameter remarks.

Load only the metadata needed for the current job or parameter prompt.
