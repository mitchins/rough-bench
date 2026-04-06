#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"
RUNS_DIR = REPO_ROOT / "runs"
OUTPUT_PATH = REPO_ROOT / "docs" / "assets" / "data" / "docs_data.json"
SUBJECTS_DIR = REPO_ROOT / "subjects"

CATEGORY_ORDER = [
    "build_systems",
    "ml_nlp_engineering",
    "search_analytics",
    "language_localization",
    "planning_product",
    "judgment_creative",
]

CATEGORY_LABELS = {
    "build_systems": "Build & Systems",
    "ml_nlp_engineering": "ML & NLP Engineering",
    "search_analytics": "Search & Analytics",
    "language_localization": "Language & Localization",
    "planning_product": "Planning & Product",
    "judgment_creative": "Judgment & Creative",
    "uncategorized": "Uncategorized",
}

DOMAIN_TO_CATEGORY = {
    "swe": "build_systems",
    "swe_code_maintenance": "build_systems",
    "swe_networking": "build_systems",
    "swe_data_pipelines": "build_systems",
    "ml_engineering": "ml_nlp_engineering",
    "nlp_engineering": "ml_nlp_engineering",
    "nlp": "ml_nlp_engineering",
    "applied_nlp": "ml_nlp_engineering",
    "quantitative_reasoning": "search_analytics",
    "retrieval_systems": "search_analytics",
    "product_analytics": "search_analytics",
    "language_translation": "language_localization",
    "language_pragmatics": "language_localization",
    "agentic_specification": "planning_product",
    "practical_reasoning": "planning_product",
    "tool_planning": "planning_product",
    "ux_product_design": "planning_product",
    "writing_critique": "judgment_creative",
    "creative_reasoning": "judgment_creative",
    "game_design": "judgment_creative",
    "reasoning_candor": "judgment_creative",
}

EFFICIENCY_QUALITY_FLOOR = 75.0

HOME_ASSISTANT_OVERSIGHT_TASK_IDS = [
    "smarthome_occupancy_inference_alert",
    "smarthome_conflicting_signals_pet_vs_intrusion",
    "smarthome_toolcall_notification_triage",
    "aquarium_ph_crash_triage",
]

HOST_DEPLOYMENT_LABELS = {
    "192.168.1.14": "local",
    "192.168.1.26": "router",
    "192.168.2.216": "compute-test",
    "192.168.4.3": "lab-pc",
    "192.168.4.222": "compute-test",
    "localhost": "local",
}


@dataclass
class TaskMeta:
    id: str
    title: str
    domain: str
    family: str
    counted: bool
    meta_category: str


@dataclass
class SubjectMeta:
    id: str
    params_billion: float | None = None
    params_billion_backbone: float | None = None
    loaded_size_gb: float | None = None


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_task_index() -> dict[str, TaskMeta]:
    tasks: dict[str, TaskMeta] = {}
    for task_path in sorted(BENCHMARKS_DIR.glob("*/task.yaml")):
        data = _load_yaml(task_path)
        task_id = str(data["id"])
        domain = str(data.get("domain", ""))
        tasks[task_id] = TaskMeta(
            id=task_id,
            title=str(data.get("title", task_id)),
            domain=domain,
            family=str(data.get("family", "")),
            counted=bool(data.get("counted", False)),
            meta_category=DOMAIN_TO_CATEGORY.get(domain, "uncategorized"),
        )
    return tasks


def load_subject_meta_index() -> dict[str, SubjectMeta]:
    subjects: dict[str, SubjectMeta] = {}
    for yaml_path in sorted(SUBJECTS_DIR.glob("*.yaml")):
        try:
            data = _load_yaml(yaml_path)
        except Exception:
            continue
        subject_rows = data.get("subjects")
        if not isinstance(subject_rows, list):
            continue
        for item in subject_rows:
            if not isinstance(item, dict):
                continue
            subject_id = str(item.get("id", "")).strip()
            if not subject_id:
                continue
            params_billion_raw = item.get("params_billion")
            params_billion = None
            if params_billion_raw not in (None, ""):
                try:
                    params_billion = float(params_billion_raw)
                except (TypeError, ValueError):
                    params_billion = None
            params_billion_backbone_raw = item.get("params_billion_backbone")
            params_billion_backbone = None
            if params_billion_backbone_raw not in (None, ""):
                try:
                    params_billion_backbone = float(params_billion_backbone_raw)
                except (TypeError, ValueError):
                    params_billion_backbone = None
            loaded_size_gb_raw = item.get("loaded_size_gb")
            loaded_size_gb = None
            if loaded_size_gb_raw not in (None, ""):
                try:
                    loaded_size_gb = float(loaded_size_gb_raw)
                except (TypeError, ValueError):
                    loaded_size_gb = None
            subjects[subject_id] = SubjectMeta(
                id=subject_id,
                params_billion=params_billion,
                params_billion_backbone=params_billion_backbone,
                loaded_size_gb=loaded_size_gb,
            )
    return subjects


def _quality_from_pct(suite_demerit_pct: Any) -> float | None:
    if suite_demerit_pct is None:
        return None
    try:
        value = float(suite_demerit_pct)
    except (TypeError, ValueError):
        return None
    return round(100.0 - value, 1)


def _canonical_title(title: str) -> str:
    value = str(title or "").strip()
    value = re.sub(r"\s+\(z\.?a\.?i(?:\s+coding\s+plan)?\)$", "", value, flags=re.I)
    value = re.sub(r"\s+\(ethernet\)$", "", value, flags=re.I)
    value = re.sub(r"\s+lab-pc$", "", value, flags=re.I)
    value = re.sub(r"\s+compute-test$", "", value, flags=re.I)
    value = re.sub(r"\s+router$", "", value, flags=re.I)
    value = re.sub(r"\s+local$", "", value, flags=re.I)
    value = re.sub(r"\s+anthropic$", "", value, flags=re.I)
    return value.strip()


def _deployment_label(*, title: str, subject_id: str, provider: str, base_url: str) -> str:
    lower_title = str(title or "").casefold()
    lower_subject_id = str(subject_id or "").casefold()
    if "compute-test" in lower_title or "compute_test" in lower_subject_id:
        return "compute-test"
    if "lab-pc" in lower_title or "labpc" in lower_subject_id or "lab_pc" in lower_subject_id:
        return "lab-pc"
    if lower_title.endswith(" router") or "_router" in lower_subject_id:
        return "router"
    if lower_title.endswith(" local") or "_local" in lower_subject_id:
        return "local"
    if lower_title.endswith(" anthropic") or provider == "anthropic":
        return "anthropic"
    parsed = urlparse(base_url or "")
    host = (parsed.hostname or "").strip().casefold()
    if host in HOST_DEPLOYMENT_LABELS:
        return HOST_DEPLOYMENT_LABELS[host]
    if provider == "openai":
        return "openai"
    return ""


def _variant_label(*, title: str, subject_id: str, reasoning_effort: Any, reasoning_effort_profile: Any) -> str:
    lower_subject_id = str(subject_id or "").casefold()
    if str(reasoning_effort_profile or "").strip():
        return "auto"
    lower_title = str(title or "").casefold()
    if lower_title.endswith(" auto") or lower_subject_id.endswith("_auto"):
        return "auto"
    if not lower_subject_id.startswith("gpt_oss_"):
        return ""
    effort = str(reasoning_effort or "").strip().casefold()
    if effort in {"low", "medium", "high"}:
        return effort
    return ""


def _category_summary(
    task_results: list[dict[str, Any]],
    failed_task_penalties: list[dict[str, Any]],
    task_index: dict[str, TaskMeta],
) -> tuple[dict[str, Any], dict[str, dict[str, float]]]:
    summary: dict[str, dict[str, float]] = {
        category: {"demerits": 0.0, "max_demerits": 0.0, "task_count": 0.0}
        for category in CATEGORY_ORDER
    }
    summary["uncategorized"] = {"demerits": 0.0, "max_demerits": 0.0, "task_count": 0.0}

    per_task: dict[str, dict[str, float]] = {}
    for task in task_results:
        task_id = str(task.get("task_id", ""))
        task_meta = task_index.get(task_id)
        category = task_meta.meta_category if task_meta else "uncategorized"
        total_penalty = float(task.get("total_penalty") or 0.0)
        max_penalty = float(task.get("max_penalty_possible") or 0.0)
        slot = summary.setdefault(category, {"demerits": 0.0, "max_demerits": 0.0, "task_count": 0.0})
        slot["demerits"] += total_penalty
        slot["max_demerits"] += max_penalty
        slot["task_count"] += 1.0
        per_task[task_id] = {
            "total_penalty": total_penalty,
            "max_penalty_possible": max_penalty,
            "quality": round(100.0 * (1.0 - (total_penalty / max_penalty)), 1) if max_penalty else None,
        }

    for failure in failed_task_penalties:
        task_id = str(failure.get("task_id", ""))
        task_meta = task_index.get(task_id)
        category = task_meta.meta_category if task_meta else "uncategorized"
        total_penalty = float(
            failure.get("failure_demerits")
            or failure.get("max_penalty_possible")
            or 0.0
        )
        max_penalty = float(
            failure.get("max_penalty_possible")
            or failure.get("failure_demerits")
            or 0.0
        )
        slot = summary.setdefault(category, {"demerits": 0.0, "max_demerits": 0.0, "task_count": 0.0})
        slot["demerits"] += total_penalty
        slot["max_demerits"] += max_penalty
        slot["task_count"] += 1.0
        per_task[task_id] = {
            "total_penalty": total_penalty,
            "max_penalty_possible": max_penalty,
            "quality": 0.0 if max_penalty else None,
            "failed": True,
        }

    category_rows: dict[str, Any] = {}
    for category, row in summary.items():
        max_demerits = row["max_demerits"]
        demerits = row["demerits"]
        quality = round(100.0 * (1.0 - (demerits / max_demerits)), 1) if max_demerits else None
        category_rows[category] = {
            "id": category,
            "label": CATEGORY_LABELS.get(category, category),
            "demerits": round(demerits, 1),
            "max_demerits": round(max_demerits, 1),
            "quality": quality,
            "task_count": int(row["task_count"]),
        }
    return category_rows, per_task


def _normalize_run(
    subject_item: dict[str, Any],
    run_dir: Path,
    task_index: dict[str, TaskMeta],
    subject_meta_index: dict[str, SubjectMeta],
) -> dict[str, Any]:
    report = subject_item.get("report", {})
    task_results = report.get("task_results", []) or []
    failed_task_penalties = report.get("failed_task_penalties", []) or []
    categories, task_penalties = _category_summary(task_results, failed_task_penalties, task_index)
    overall_quality = _quality_from_pct(report.get("suite_demerit_pct"))
    subject_id = str(subject_item.get("subject_id") or "")
    title = str(subject_item.get("title") or "")
    provider = str(subject_item.get("provider") or "")
    base_url = str(subject_item.get("base_url") or "")
    reasoning_effort = subject_item.get("reasoning_effort")
    reasoning_effort_profile = subject_item.get("reasoning_effort_profile")
    canonical_title = _canonical_title(title)
    deployment = _deployment_label(
        title=title,
        subject_id=subject_id,
        provider=provider,
        base_url=base_url,
    )
    variant = _variant_label(
        title=title,
        subject_id=subject_id,
        reasoning_effort=reasoning_effort,
        reasoning_effort_profile=reasoning_effort_profile,
    )
    display_title = canonical_title
    if variant and not canonical_title.casefold().endswith(f" {variant}"):
        display_title = f"{canonical_title} · {variant}"
    usage_total = report.get("usage_total_tokens")
    usage_prompt_tokens = report.get("usage_prompt_tokens")
    usage_completion_tokens = report.get("usage_completion_tokens")
    usage_reasoning_tokens = report.get("usage_reasoning_tokens")
    usage_answer_tokens = None
    usage_unsplit_completion_tokens = None
    try:
        completion_value = None if usage_completion_tokens is None else int(usage_completion_tokens)
        reasoning_value = None if usage_reasoning_tokens is None else int(usage_reasoning_tokens)
        if completion_value is not None:
            if reasoning_value is None:
                usage_unsplit_completion_tokens = completion_value
            else:
                usage_answer_tokens = max(0, completion_value - reasoning_value)
    except (TypeError, ValueError):
        usage_answer_tokens = None
        usage_unsplit_completion_tokens = None
    demerits_per_1k = report.get("demerits_per_1k_total_tokens")
    utility_points = None
    utility_per_1k = None
    try:
        suite_max_value = float(report.get("suite_max_demerits") or 0.0)
        demerits_value = float(report.get("roughbench_demerits") or 0.0)
        tokens_value = int(usage_total or 0)
        if suite_max_value > 0:
            utility_points = max(0.0, suite_max_value - demerits_value)
            if tokens_value > 0:
                utility_per_1k = utility_points / (tokens_value / 1000.0)
    except (TypeError, ValueError):
        utility_points = None
        utility_per_1k = None
    tainted = bool(report.get("tainted") or report.get("warning_output_cap_task_count"))
    status = subject_item.get("status")
    failed_task_count = int(subject_item.get("failed_task_count") or 0)
    headline_eligible = status == "complete" and failed_task_count == 0
    subject_meta = subject_meta_index.get(subject_id)
    unique_signal_ids = sorted(
        {
            str(signal.get("id"))
            for task_result in task_results
            for signal in (task_result.get("passed_signals") or [])
            if isinstance(signal, dict) and signal.get("id")
        }
    )
    return {
        "run_id": run_dir.name,
        "run_path": str(run_dir.relative_to(REPO_ROOT)),
        "subject_id": subject_id,
        "title": title,
        "canonical_title": canonical_title,
        "display_title": display_title,
        "deployment_label": deployment,
        "variant_label": variant,
        "model": subject_item.get("model"),
        "provider": provider,
        "base_url": base_url,
        "reasoning_effort": reasoning_effort,
        "reasoning_effort_profile": reasoning_effort_profile,
        "status": status,
        "completed_task_count": int(subject_item.get("completed_task_count") or 0),
        "requested_task_count": int(subject_item.get("requested_task_count") or 0),
        "failed_task_count": failed_task_count,
        "summary": report.get("summary"),
        "roughbench_demerits": report.get("roughbench_demerits"),
        "suite_max_demerits": report.get("suite_max_demerits"),
        "suite_demerit_pct": report.get("suite_demerit_pct"),
        "overall_quality": overall_quality,
        "utility_points": None if utility_points is None else round(utility_points, 1),
        "utility_per_1k_total_tokens": None if utility_per_1k is None else round(utility_per_1k, 2),
        "usage_total_tokens": usage_total,
        "usage_prompt_tokens": usage_prompt_tokens,
        "usage_completion_tokens": usage_completion_tokens,
        "usage_reasoning_tokens": usage_reasoning_tokens,
        "usage_answer_tokens": usage_answer_tokens,
        "usage_unsplit_completion_tokens": usage_unsplit_completion_tokens,
        "demerits_per_1k_total_tokens": demerits_per_1k,
        "params_billion": None if subject_meta is None else subject_meta.params_billion,
        "params_billion_active": None if subject_meta is None else subject_meta.params_billion,
        "params_billion_backbone": None if subject_meta is None else subject_meta.params_billion_backbone,
        "loaded_size_gb": None if subject_meta is None else subject_meta.loaded_size_gb,
        "headline_eligible": headline_eligible,
        "tainted": tainted,
        "tainted_task_count": int(report.get("tainted_task_count") or report.get("warning_output_cap_task_count") or 0),
        "taint_reason": report.get("taint_reason"),
        "context_retry_task_count": int(report.get("warning_context_retry_task_count") or 0),
        "unique_signal_ids": unique_signal_ids,
        "categories": categories,
        "task_penalties": task_penalties,
        "failed_task_penalties": failed_task_penalties,
    }


def _is_current_full_suite_run(run: dict[str, Any], *, total_task_count: int) -> bool:
    return (
        run.get("status") == "complete"
        and int(run.get("failed_task_count") or 0) == 0
        and int(run.get("requested_task_count") or 0) == total_task_count
        and int(run.get("completed_task_count") or 0) == total_task_count
    )


def load_runs(task_index: dict[str, TaskMeta], subject_meta_index: dict[str, SubjectMeta]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    seen_run_dirs: set[Path] = set()

    for compare_path in sorted(RUNS_DIR.glob("*/.roughbench_compare.json")):
        try:
            payload = json.loads(compare_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        run_dir = compare_path.parent
        seen_run_dirs.add(run_dir)
        for subject_item in payload.get("subjects", []) or []:
            if isinstance(subject_item, dict):
                runs.append(_normalize_run(subject_item, run_dir, task_index, subject_meta_index))

    for subject_progress in sorted(RUNS_DIR.glob("*/*/.roughbench_compare_subject.json")):
        run_dir = subject_progress.parents[1]
        if run_dir in seen_run_dirs:
            continue
        try:
            subject_item = json.loads(subject_progress.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(subject_item, dict):
            runs.append(_normalize_run(subject_item, run_dir, task_index, subject_meta_index))

    return runs


def _overall_leaderboard(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    headline_runs = [row for row in runs if row.get("current_full_suite_eligible")]

    def sort_key(row: dict[str, Any]) -> tuple[int, float, str]:
        demerits = float(row.get("roughbench_demerits") or 0.0)
        return (demerits, str(row.get("subject_id") or ""))

    return sorted(headline_runs, key=sort_key)


def _efficiency_leaderboard(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = []
    for row in runs:
        if not row.get("current_full_suite_eligible"):
            continue
        quality = row.get("overall_quality")
        if row.get("tainted"):
            continue
        if row.get("usage_total_tokens") in (None, 0):
            continue
        if quality is None or float(quality) < EFFICIENCY_QUALITY_FLOOR:
            continue
        if row.get("utility_per_1k_total_tokens") in (None, 0):
            continue
        eligible.append(row)
    return sorted(
        eligible,
        key=lambda row: (
            -float(row.get("utility_per_1k_total_tokens") or 0.0),
            int(row.get("usage_total_tokens") or 0),
            float(row.get("roughbench_demerits") or 0.0),
        ),
    )


def _category_leaderboards(runs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    headline_runs = [run for run in runs if run.get("current_full_suite_eligible")]
    output: dict[str, list[dict[str, Any]]] = {}
    for category in CATEGORY_ORDER:
        rows = []
        for run in headline_runs:
            row = run["categories"].get(category)
            if not row or row.get("quality") is None:
                continue
            rows.append(
                {
                    "run_id": run["run_id"],
                    "subject_id": run["subject_id"],
                    "title": run["display_title"],
                    "deployment_label": run.get("deployment_label"),
                    "model": run["model"],
                    "status": run["status"],
                    "tainted": run["tainted"],
                    "quality": row["quality"],
                    "demerits": row["demerits"],
                    "max_demerits": row["max_demerits"],
                    "task_count": row["task_count"],
                }
            )
        output[category] = sorted(rows, key=lambda row: (-float(row["quality"]), float(row["demerits"]), row["subject_id"]))
    return output


def _category_reference_scores(runs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    clean_runs = [run for run in runs if run.get("current_full_suite_eligible") and not run.get("tainted")]
    headline_runs = [run for run in runs if run.get("current_full_suite_eligible")]
    reference_runs = clean_runs or headline_runs

    output: dict[str, dict[str, Any]] = {}
    for category in CATEGORY_ORDER:
        best_quality: float | None = None
        best_run_id: str | None = None
        for run in reference_runs:
            row = run.get("categories", {}).get(category)
            quality = row.get("quality") if isinstance(row, dict) else None
            if quality is None:
                continue
            quality_value = float(quality)
            if best_quality is None or quality_value > best_quality:
                best_quality = quality_value
                best_run_id = str(run.get("run_id") or "")
        output[category] = {
            "quality": round(best_quality, 1) if best_quality is not None else None,
            "run_id": best_run_id,
            "basis": "clean" if clean_runs else "headline",
        }
    return output


def _award_eligible_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [run for run in runs if run.get("current_full_suite_eligible") and not run.get("tainted")]


def _safe_harmonic_mean(values: list[float]) -> float:
    if not values or any(value <= 0 for value in values):
        return 0.0
    return len(values) / sum(1.0 / value for value in values)


def _subset_quality(run: dict[str, Any], task_ids: list[str]) -> float | None:
    if not task_ids:
        return None
    task_rows = run.get("task_penalties", {})
    rows = []
    for task_id in task_ids:
        row = task_rows.get(task_id)
        if not isinstance(row, dict):
            return None
        rows.append(row)
    max_penalty = sum(float(row.get("max_penalty_possible") or 0.0) for row in rows)
    demerits = sum(float(row.get("total_penalty") or 0.0) for row in rows)
    if max_penalty <= 0:
        return None
    return round(100.0 * (1.0 - (demerits / max_penalty)), 1)


def _build_awards(
    runs: list[dict[str, Any]],
    task_index: dict[str, TaskMeta],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, str]]]]:
    eligible = _award_eligible_runs(runs)
    awards: list[dict[str, Any]] = []
    run_awards: dict[str, list[dict[str, str]]] = {str(run.get("run_id")): [] for run in runs}

    def add_award(
        *,
        award_id: str,
        label: str,
        description: str,
        winner: dict[str, Any] | None,
        metric_value: float | int | None,
        metric_display: str,
    ) -> None:
        if not winner:
            return
        award = {
            "id": award_id,
            "label": label,
            "description": description,
            "winner_run_id": winner["run_id"],
            "winner_subject_id": winner["subject_id"],
            "winner_title": winner["display_title"],
            "winner_deployment_label": winner.get("deployment_label"),
            "winner_model": winner["model"],
            "metric_value": metric_value,
            "metric_display": metric_display,
        }
        awards.append(award)
        run_awards.setdefault(str(winner["run_id"]), []).append({"id": award_id, "label": label})

    efficiency_candidates = [
        run
        for run in eligible
        if run.get("usage_total_tokens") not in (None, 0)
        and run.get("overall_quality") is not None
        and float(run["overall_quality"]) >= EFFICIENCY_QUALITY_FLOOR
        and run.get("utility_per_1k_total_tokens") not in (None, 0)
    ]
    if efficiency_candidates:
        winner = max(
            efficiency_candidates,
            key=lambda run: (
                float(run.get("utility_per_1k_total_tokens") or 0.0),
                -int(run.get("usage_total_tokens") or 0),
            ),
        )
        add_award(
            award_id="most_efficient",
            label="Best Token Efficiency",
            description=(
                f"Highest utility per 1k tokens among clean current full-suite runs "
                f"at or above the {EFFICIENCY_QUALITY_FLOOR:.0f} pass mark, where utility = suite_max_demerits - demerits."
            ),
            winner=winner,
            metric_value=float(winner["utility_per_1k_total_tokens"]),
            metric_display=f'{float(winner["utility_per_1k_total_tokens"]):.2f} util/1k',
        )
        loser = min(
            efficiency_candidates,
            key=lambda run: (
                float(run.get("utility_per_1k_total_tokens") or 0.0),
                int(run.get("usage_total_tokens") or 0),
            ),
        )
        add_award(
            award_id="least_efficient",
            label="Worst Token Efficiency",
            description=(
                f"Lowest utility per 1k tokens among clean current full-suite runs "
                f"at or above the {EFFICIENCY_QUALITY_FLOOR:.0f} pass mark, where utility = suite_max_demerits - demerits."
            ),
            winner=loser,
            metric_value=float(loser["utility_per_1k_total_tokens"]),
            metric_display=f'{float(loser["utility_per_1k_total_tokens"]):.2f} util/1k',
        )

    noisy_candidates = [run for run in eligible if run.get("usage_total_tokens") not in (None, 0)]
    if noisy_candidates:
        winner = max(
            noisy_candidates,
            key=lambda run: (
                int(run["usage_total_tokens"]),
                float(run.get("overall_quality") or 0.0),
            ),
        )
        add_award(
            award_id="noisiest",
            label="Highest Token Burn",
            description="Most total tokens consumed among clean current full-suite runs.",
            winner=winner,
            metric_value=int(winner["usage_total_tokens"]),
            metric_display=f'{int(winner["usage_total_tokens"]):,} tok',
        )

    params_candidates = [
        run
        for run in eligible
        if run.get("params_billion") not in (None, 0)
        and run.get("overall_quality") is not None
    ]
    if params_candidates:
        for run in params_candidates:
            run["_quality_per_billion"] = float(run["overall_quality"]) / float(run["params_billion"])
        winner = max(params_candidates, key=lambda run: (run["_quality_per_billion"], float(run["overall_quality"])))
        add_award(
            award_id="underdog",
            label="Best Throughput Efficiency",
            description=(
                "Best overall quality per active billion parameters among runs with known size metadata. "
                "This is a rough throughput-side proxy, not a VRAM or backbone-size metric."
            ),
            winner=winner,
            metric_value=winner["_quality_per_billion"],
            metric_display=f'{winner["_quality_per_billion"]:.2f} quality/active-B',
        )
        for run in params_candidates:
            run.pop("_quality_per_billion", None)

    category_candidates: list[tuple[dict[str, Any], list[float]]] = []
    for run in eligible:
        values = [
            float(run["categories"][category]["quality"])
            for category in CATEGORY_ORDER
            if run.get("categories", {}).get(category, {}).get("quality") is not None
        ]
        if len(values) == len(CATEGORY_ORDER):
            category_candidates.append((run, values))

    if category_candidates:
        scored = []
        for run, values in category_candidates:
            scored.append((run, values, _safe_harmonic_mean(values), max(values) - min(values)))
        all_rounder = max(scored, key=lambda item: (item[2], -item[3], float(item[0].get("overall_quality") or 0.0)))
        add_award(
            award_id="all_rounder",
            label="All-Rounder",
            description="Best harmonic mean across the six meta-category quality scores.",
            winner=all_rounder[0],
            metric_value=all_rounder[2],
            metric_display=f"{all_rounder[2]:.1f} HM",
        )
        specialist = max(scored, key=lambda item: (item[3], item[2]))
        add_award(
            award_id="specialist",
            label="Specialist",
            description="Biggest gap between best and worst category quality.",
            winner=specialist[0],
            metric_value=specialist[3],
            metric_display=f"{specialist[3]:.1f} span",
        )

    signal_candidates = [run for run in eligible if run.get("unique_signal_ids")]
    if signal_candidates:
        prevalence: dict[str, int] = {}
        for run in signal_candidates:
            for signal_id in run["unique_signal_ids"]:
                prevalence[signal_id] = prevalence.get(signal_id, 0) + 1

        def rarity_score(run: dict[str, Any]) -> float:
            total = 0.0
            for signal_id in run["unique_signal_ids"]:
                count = prevalence.get(signal_id, 0)
                if count:
                    total += 1.0 / count
            return total

        winner = max(
            signal_candidates,
            key=lambda run: (
                rarity_score(run),
                len(run["unique_signal_ids"]),
                float(run.get("overall_quality") or 0.0),
            ),
        )
        score = rarity_score(winner)
        add_award(
            award_id="nitpicker",
            label="Nitpicker",
            description="Highest weighted total of rare rubric signals passed, using inverse signal prevalence across clean runs.",
            winner=winner,
            metric_value=score,
            metric_display=f"{score:.2f} rarity pts",
        )

    language_task_ids = sorted(
        task.id
        for task in task_index.values()
        if task.counted and task.meta_category == "language_localization"
    )
    if language_task_ids:
        language_candidates = []
        for run in eligible:
            quality = _subset_quality(run, language_task_ids)
            if quality is None:
                continue
            language_candidates.append((run, quality))
        if language_candidates:
            winner, quality = max(
                language_candidates,
                key=lambda item: (item[1], float(item[0].get("overall_quality") or 0.0)),
            )
            add_award(
                award_id="linguist",
                label="The Linguist",
                description="Best aggregate quality across the full counted language and localization task set.",
                winner=winner,
                metric_value=quality,
                metric_display=f"{quality:.1f}%",
            )

    smarthome_task_ids = [
        task_id for task_id in HOME_ASSISTANT_OVERSIGHT_TASK_IDS if task_id in task_index
    ]
    if smarthome_task_ids:
        smarthome_candidates = []
        for run in eligible:
            quality = _subset_quality(run, smarthome_task_ids)
            if quality is None:
                continue
            smarthome_candidates.append((run, quality))
        if smarthome_candidates:
            winner, quality = max(
                smarthome_candidates,
                key=lambda item: (item[1], float(item[0].get("overall_quality") or 0.0)),
            )
            add_award(
                award_id="sentry",
                label="The Sentry",
                description="Best aggregate quality across the explicit Home Assistant-style household oversight set: occupancy, ambiguous security triage, tool-call notification triage, and aquarium monitoring.",
                winner=winner,
                metric_value=quality,
                metric_display=f"{quality:.1f}%",
            )

    return awards, run_awards


def _task_rows(task_index: dict[str, TaskMeta]) -> list[dict[str, Any]]:
    rows = []
    for task in task_index.values():
        rows.append(
            {
                "id": task.id,
                "title": task.title,
                "domain": task.domain,
                "family": task.family,
                "counted": task.counted,
                "meta_category": task.meta_category,
                "meta_category_label": CATEGORY_LABELS.get(task.meta_category, task.meta_category),
            }
        )
    return sorted(rows, key=lambda row: row["id"])


def build_docs_data() -> dict[str, Any]:
    task_index = load_task_index()
    current_task_count = len(task_index)
    subject_meta_index = load_subject_meta_index()
    runs = load_runs(task_index, subject_meta_index)
    runs = sorted(runs, key=lambda row: row["run_id"])
    for run in runs:
        run["current_full_suite_eligible"] = _is_current_full_suite_run(
            run,
            total_task_count=current_task_count,
        )
    headline_runs = [run for run in runs if run.get("current_full_suite_eligible")]
    category_reference_scores = _category_reference_scores(runs)

    for run in runs:
        for category in CATEGORY_ORDER:
            category_row = run.get("categories", {}).get(category)
            if not isinstance(category_row, dict):
                continue
            quality = category_row.get("quality")
            reference_quality = category_reference_scores.get(category, {}).get("quality")
            if quality is None or reference_quality in (None, 0):
                category_row["relative_quality"] = None
                continue
            category_row["relative_quality"] = round(100.0 * float(quality) / float(reference_quality), 1)

    awards, run_awards = _build_awards(runs, task_index)
    for run in runs:
        run["awards"] = run_awards.get(str(run.get("run_id")), [])
        run.pop("unique_signal_ids", None)

    data = {
        "generated_at": datetime.now(UTC).isoformat(),
        "current_suite_task_count": current_task_count,
        "efficiency_quality_floor": EFFICIENCY_QUALITY_FLOOR,
        "category_order": CATEGORY_ORDER,
        "category_reference_scores": category_reference_scores,
        "awards": awards,
        "categories": [
            {
                "id": category,
                "label": CATEGORY_LABELS.get(category, category),
                "task_count": sum(1 for task in task_index.values() if task.meta_category == category),
            }
            for category in CATEGORY_ORDER
        ],
        "tasks": _task_rows(task_index),
        "runs": runs,
        "headline_runs": headline_runs,
        "leaderboards": {
            "overall": _overall_leaderboard(runs),
            "efficiency": _efficiency_leaderboard(runs),
            "categories": _category_leaderboards(runs),
        },
    }
    return data


def main() -> None:
    data = build_docs_data()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
