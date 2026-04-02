from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from openai import OpenAI

from roughbench.openai_compat import build_reasoning_extra_body, normalize_message_content
from roughbench.judging.scorecard import PenaltyHit, SignalHit, TaskScorecard
from roughbench.runners.base import TaskOutput
from roughbench.tasks.models import TaskDefinition


SYSTEM_PROMPT = """You are RoughBenchJudge.

Score one benchmark submission against a fixed rubric.
Be strict, literal, and artifact-aware.
When artifacts exist, treat file contents as higher-trust evidence than prose claims.
Prefer demonstrated implementation details over intent statements.
Only use the ids provided in the prompt.
Do not invent new ids.
If uncertain, prefer leaving an id out rather than guessing.
Return JSON only with this exact schema:
{
  "passed_signal_ids": ["signal_id"],
  "triggered_penalty_ids": ["penalty_id"],
  "judge_summary": "short grounded summary"
}
"""


class ChatJudgeClient(Protocol):
    model_name: str

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        ...


@dataclass
class OpenAICompatibleJudgeClient:
    model_name: str
    base_url: str
    api_key: str = "dummy"
    temperature: float = 0.0
    max_tokens: int = 2000
    timeout_seconds: int = 180
    reasoning_effort: str = ""

    def __post_init__(self) -> None:
        self._client = OpenAI(
            base_url=self.base_url.rstrip("/"),
            api_key=self.api_key,
            timeout=self.timeout_seconds,
        )

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        create_kwargs: dict[str, object] = {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.reasoning_effort:
            create_kwargs["extra_body"] = build_reasoning_extra_body(self.reasoning_effort)

        response = self._client.chat.completions.create(**create_kwargs)
        return normalize_message_content(response.choices[0].message.content)


@dataclass
class AnthropicJudgeClient:
    model_name: str
    api_key: str
    temperature: float = 0.0
    max_tokens: int = 2000

    def __post_init__(self) -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Anthropic judge support requires the 'anthropic' package. "
                "Install it with `pip install anthropic` or `pip install -e '.[anthropic]'`."
            ) from exc

        self._client = anthropic.Anthropic(api_key=self.api_key)

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        response = self._client.messages.create(
            model=self.model_name,
            system=system_prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        )
        parts: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()


@dataclass
class CopilotSDKJudgeClient:
    model_name: str
    reasoning_effort: str | None = None
    timeout_seconds: int = 180
    copilot_package_root: str | None = None
    cwd: str | None = None
    log_level: str = "error"

    def __post_init__(self) -> None:
        package_root = _resolve_copilot_package_root(self.copilot_package_root)
        self._package_root = package_root
        self._sdk_module_path = package_root / "copilot-sdk" / "index.js"
        self._cli_path = package_root / "index.js"
        self._bridge_path = Path(__file__).resolve().parents[1] / "copilot_sdk_bridge.mjs"
        self._cwd = self.cwd or str(Path.cwd())

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "sdk_module_path": str(self._sdk_module_path),
            "cli_path": str(self._cli_path),
            "cwd": self._cwd,
            "model": self.model_name,
            "reasoning_effort": self.reasoning_effort,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "timeout_ms": self.timeout_seconds * 1000,
            "log_level": self.log_level,
        }
        env = os.environ.copy()
        env.setdefault("NODE_NO_WARNINGS", "1")
        proc = subprocess.run(
            ["node", str(self._bridge_path)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
            timeout=self.timeout_seconds + 15,
            env=env,
        )
        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            stdout = proc.stdout.strip()
            detail = stderr or stdout or f"exit status {proc.returncode}"
            raise RuntimeError(f"Copilot SDK judge failed: {detail}")

        try:
            response_payload = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Copilot SDK judge returned non-JSON output: {proc.stdout.strip()}"
            ) from exc

        content = str(response_payload.get("content", "")).strip()
        if not content:
            raise RuntimeError("Copilot SDK judge returned an empty response.")
        return content


@dataclass(frozen=True)
class LLMJudgeDecision:
    passed_signal_ids: tuple[str, ...]
    triggered_penalty_ids: tuple[str, ...]
    judge_summary: str
    raw_response: str
    model_name: str


class LLMScorecardJudge:
    def __init__(self, client: ChatJudgeClient, label: str | None = None) -> None:
        self.client = client
        self.label = label or client.model_name

    def evaluate(self, task: TaskDefinition, output: TaskOutput) -> TaskScorecard:
        decision = self.decide(task, output)
        return self._decision_to_scorecard(task, output, decision)

    def decide(
        self,
        task: TaskDefinition,
        output: TaskOutput,
        draft_decision: LLMJudgeDecision | None = None,
    ) -> LLMJudgeDecision:
        user_prompt = self._build_user_prompt(task, output, draft_decision)
        raw_response = self.client.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        payload = self._parse_json_response(raw_response)

        signal_ids = _normalize_ids(payload.get("passed_signal_ids"))
        penalty_ids = _normalize_ids(payload.get("triggered_penalty_ids"))
        summary = str(payload.get("judge_summary", "")).strip()
        if not summary:
            summary = f"Judged by {self.label}."

        return LLMJudgeDecision(
            passed_signal_ids=signal_ids,
            triggered_penalty_ids=penalty_ids,
            judge_summary=summary,
            raw_response=raw_response,
            model_name=self.label,
        )

    def _decision_to_scorecard(
        self,
        task: TaskDefinition,
        output: TaskOutput,
        decision: LLMJudgeDecision,
    ) -> TaskScorecard:
        signal_id_set = set(decision.passed_signal_ids)
        penalty_id_set = set(decision.triggered_penalty_ids)

        passed_signals = tuple(
            SignalHit(id=rule.id, description=rule.description)
            for rule in task.rubric.signals
            if rule.id in signal_id_set
        )
        triggered_penalties = tuple(
            PenaltyHit(id=rule.id, points=rule.points, description=rule.description)
            for rule in task.rubric.penalties
            if rule.id in penalty_id_set
        )
        total_penalty = sum(item.points for item in triggered_penalties)
        return TaskScorecard(
            task_id=task.id,
            title=task.title,
            total_penalty=total_penalty,
            max_penalty_possible=sum(item.points for item in task.rubric.penalties),
            triggered_penalties=triggered_penalties,
            passed_signals=passed_signals,
            judge_summary=decision.judge_summary,
            artifacts_seen=output.artifact_names,
        )

    def _build_user_prompt(
        self,
        task: TaskDefinition,
        output: TaskOutput,
        draft_decision: LLMJudgeDecision | None,
    ) -> str:
        signal_lines = "\n".join(
            f"- {rule.id}: {rule.description}" for rule in task.rubric.signals
        )
        penalty_lines = "\n".join(
            f"- {rule.id} (+{rule.points}): {rule.description}"
            for rule in task.rubric.penalties
        )
        latent_lines = _as_bullets(task.latent_requirements)
        failure_lines = _as_bullets(task.hard_failures)
        strength_lines = _as_bullets(task.strong_signals)
        artifact_lines = _as_bullets(task.expected_artifacts)
        artifact_names = _as_bullets(output.artifact_names)
        answer_text = _truncate(output.answer_text, limit=7000)
        artifact_text = _truncate(_format_artifact_bodies(output), limit=9000)

        prompt = f"""Task id: {task.id}
Title: {task.title}
Domain: {task.domain}

Prompt:
{task.prompt}

Intent:
{task.intent}

Latent requirements:
{latent_lines}

Hard failures:
{failure_lines}

Strong signals:
{strength_lines}

Expected artifacts:
{artifact_lines}

Judge instructions:
{task.judge_instructions or "-"}

Allowed signal ids:
{signal_lines or "- none"}

Allowed penalty ids:
{penalty_lines or "- none"}

Submission artifact names:
{artifact_names}

Submission answer text:
<<<ANSWER
{answer_text or "(empty answer text)"}
ANSWER

Submission artifact contents:
<<<ARTIFACTS
{artifact_text or "(no text-like artifacts)"}
ARTIFACTS
"""

        if draft_decision is not None:
            draft_payload = {
                "model_name": draft_decision.model_name,
                "passed_signal_ids": list(draft_decision.passed_signal_ids),
                "triggered_penalty_ids": list(draft_decision.triggered_penalty_ids),
                "judge_summary": draft_decision.judge_summary,
            }
            prompt += (
                "\nDraft judge analysis to review critically:\n"
                "<<<DRAFT\n"
                f"{json.dumps(draft_payload, indent=2)}\n"
                "DRAFT\n"
            )

        prompt += (
            "\nRespond with JSON only. Select only ids from the allowed lists.\n"
            "Do not include markdown fences."
        )
        return prompt

    def _parse_json_response(self, raw_response: str) -> dict:
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError(f"Judge response was not valid JSON:\n{raw_response}")
            return json.loads(cleaned[start : end + 1])


class StackedJudge:
    def __init__(self, draft_judge: LLMScorecardJudge, final_judge: LLMScorecardJudge) -> None:
        self.draft_judge = draft_judge
        self.final_judge = final_judge

    def evaluate(self, task: TaskDefinition, output: TaskOutput) -> TaskScorecard:
        draft_decision = self.draft_judge.decide(task, output)
        final_decision = self.final_judge.decide(task, output, draft_decision=draft_decision)
        return self.final_judge._decision_to_scorecard(task, output, final_decision)


class HybridJudge:
    def __init__(self, anchor_judge: object, review_judge: object) -> None:
        self.anchor_judge = anchor_judge
        self.review_judge = review_judge

    def evaluate(self, task: TaskDefinition, output: TaskOutput) -> TaskScorecard:
        anchor_scorecard = self.anchor_judge.evaluate(task, output)
        review_scorecard = self.review_judge.evaluate(task, output)

        summary = anchor_scorecard.judge_summary
        drift = _scorecard_drift(anchor_scorecard, review_scorecard)
        if drift:
            summary = f"{summary} LLM review drift noted: {drift}. Anchor score retained."
        elif review_scorecard.judge_summary:
            summary = f"{summary} LLM review: {review_scorecard.judge_summary}"

        return TaskScorecard(
            task_id=anchor_scorecard.task_id,
            title=anchor_scorecard.title,
            total_penalty=anchor_scorecard.total_penalty,
            max_penalty_possible=anchor_scorecard.max_penalty_possible,
            triggered_penalties=anchor_scorecard.triggered_penalties,
            passed_signals=anchor_scorecard.passed_signals,
            judge_summary=summary,
            artifacts_seen=anchor_scorecard.artifacts_seen,
        )


def _normalize_ids(values: object) -> tuple[str, ...]:
    if not isinstance(values, list):
        return ()
    deduped: dict[str, None] = {}
    for value in values:
        if not isinstance(value, str):
            continue
        normalized = value.strip()
        if normalized:
            deduped[normalized] = None
    return tuple(deduped)


def _as_bullets(values: tuple[str, ...]) -> str:
    if not values:
        return "- none"
    return "\n".join(f"- {value}" for value in values)


def _truncate(text: str, *, limit: int) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 15].rstrip() + "\n...[truncated]"


def _format_artifact_bodies(output: TaskOutput) -> str:
    chunks: list[str] = []
    for artifact in output.artifacts:
        if artifact.text is None:
            continue
        chunks.append(f"### {artifact.relative_path}\n{artifact.text.strip()}")
    return "\n\n".join(chunk for chunk in chunks if chunk).strip()


def _scorecard_drift(anchor: TaskScorecard, review: TaskScorecard) -> str:
    anchor_penalties = {item.id for item in anchor.triggered_penalties}
    review_penalties = {item.id for item in review.triggered_penalties}
    anchor_signals = {item.id for item in anchor.passed_signals}
    review_signals = {item.id for item in review.passed_signals}

    parts: list[str] = []
    extra_penalties = sorted(review_penalties - anchor_penalties)
    missed_penalties = sorted(anchor_penalties - review_penalties)
    extra_signals = sorted(review_signals - anchor_signals)
    missed_signals = sorted(anchor_signals - review_signals)

    if extra_penalties:
        parts.append(f"extra penalties {', '.join(extra_penalties)}")
    if missed_penalties:
        parts.append(f"missed penalties {', '.join(missed_penalties)}")
    if extra_signals:
        parts.append(f"extra signals {', '.join(extra_signals)}")
    if missed_signals:
        parts.append(f"missed signals {', '.join(missed_signals)}")

    return "; ".join(parts)


def _resolve_copilot_package_root(explicit_root: str | None) -> Path:
    if explicit_root:
        path = Path(explicit_root).expanduser().resolve()
        if _is_copilot_package_root(path):
            return path
        raise RuntimeError(
            f"ROUGHBENCH_COPILOT_PACKAGE_ROOT does not point to a valid @github/copilot package: {path}"
        )

    candidates = _candidate_copilot_package_roots()
    if not candidates:
        raise RuntimeError(
            "Could not find a local @github/copilot package with the bundled SDK. "
            "Set ROUGHBENCH_COPILOT_PACKAGE_ROOT to a valid package root."
        )
    return candidates[0]


def _candidate_copilot_package_roots() -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.expanduser().resolve()
        if resolved in seen:
            return
        if _is_copilot_package_root(resolved):
            seen.add(resolved)
            candidates.append(resolved)

    add(Path.cwd() / "node_modules" / "@github" / "copilot")

    npm_root = _try_npm_root_global()
    if npm_root is not None:
        add(npm_root / "@github" / "copilot")

    npx_root = Path.home() / ".npm" / "_npx"
    if npx_root.exists():
        for path in sorted(
            npx_root.glob("*/node_modules/@github/copilot"),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        ):
            add(path)

    return candidates


def _try_npm_root_global() -> Path | None:
    try:
        proc = subprocess.run(
            ["npm", "root", "-g"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    output = proc.stdout.strip()
    if not output:
        return None
    return Path(output)


def _is_copilot_package_root(path: Path) -> bool:
    return (path / "index.js").exists() and (path / "copilot-sdk" / "index.js").exists()
