from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def default_jobs_dir() -> Path:
    return Path.cwd() / ".roughbench_jobs"


def create_job(*, jobs_dir: Path, argv: list[str], cwd: Path) -> dict[str, Any]:
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_id = _new_job_id()
    job_dir = jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "job_id": job_id,
        "status": "queued",
        "argv": argv,
        "cwd": str(cwd),
        "created_at": _utc_now(),
        "started_at": None,
        "finished_at": None,
        "pid": None,
        "exit_code": None,
        "log_path": str(job_dir / "job.log"),
    }
    write_metadata(job_dir, metadata)
    return metadata


def launch_job(*, jobs_dir: Path, job_id: str, child_argv: list[str], cwd: Path) -> dict[str, Any]:
    job_dir = jobs_dir / job_id
    log_path = job_dir / "job.log"
    with log_path.open("a", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [sys.executable, "-m", "roughbench", *child_argv],
            cwd=cwd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    metadata = load_metadata(job_dir)
    metadata["pid"] = process.pid
    metadata["launched_at"] = _utc_now()
    write_metadata(job_dir, metadata)
    return metadata


def mark_running(*, jobs_dir: Path, job_id: str, pid: int | None = None) -> dict[str, Any]:
    job_dir = jobs_dir / job_id
    metadata = load_metadata(job_dir)
    metadata["status"] = "running"
    metadata["started_at"] = metadata.get("started_at") or _utc_now()
    metadata["pid"] = pid or metadata.get("pid") or os.getpid()
    write_metadata(job_dir, metadata)
    return metadata


def mark_finished(*, jobs_dir: Path, job_id: str, exit_code: int) -> dict[str, Any]:
    job_dir = jobs_dir / job_id
    metadata = load_metadata(job_dir)
    metadata["status"] = "completed" if exit_code == 0 else "failed"
    metadata["exit_code"] = exit_code
    metadata["finished_at"] = _utc_now()
    write_metadata(job_dir, metadata)
    return metadata


def list_jobs(jobs_dir: Path) -> list[dict[str, Any]]:
    if not jobs_dir.exists():
        return []
    jobs: list[dict[str, Any]] = []
    for metadata_path in sorted(jobs_dir.glob("*/metadata.json")):
        metadata = load_metadata(metadata_path.parent)
        metadata["pid_running"] = _pid_running(metadata.get("pid"))
        jobs.append(metadata)
    jobs.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return jobs


def inspect_job(*, jobs_dir: Path, job_id: str, log_lines: int = 20) -> dict[str, Any]:
    job_dir = jobs_dir / job_id
    metadata = load_metadata(job_dir)
    metadata["pid_running"] = _pid_running(metadata.get("pid"))
    log_path = Path(metadata["log_path"])
    metadata["log_tail"] = _tail_lines(log_path, log_lines)
    return metadata


def load_metadata(job_dir: Path) -> dict[str, Any]:
    return json.loads((job_dir / "metadata.json").read_text(encoding="utf-8"))


def write_metadata(job_dir: Path, metadata: dict[str, Any]) -> None:
    path = job_dir / "metadata.json"
    tmp_path = job_dir / "metadata.json.tmp"
    tmp_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _new_job_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"job-{stamp}-{uuid.uuid4().hex[:8]}"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _pid_running(pid: object) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _tail_lines(path: Path, limit: int) -> list[str]:
    if limit <= 0 or not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-limit:]
