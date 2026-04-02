from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _as_tuple(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        return (values,)
    return tuple(str(value) for value in values)


def _as_groups(values: Any) -> tuple[tuple[str, ...], ...]:
    if values is None:
        return ()
    return tuple(tuple(str(item) for item in group) for group in values)


@dataclass(frozen=True)
class SignalRule:
    id: str
    description: str
    any: tuple[str, ...] = ()
    all: tuple[str, ...] = ()
    groups: tuple[tuple[str, ...], ...] = ()
    artifact_any: tuple[str, ...] = ()
    artifact_text_any: tuple[str, ...] = ()
    artifact_text_all: tuple[str, ...] = ()
    artifact_text_groups: tuple[tuple[str, ...], ...] = ()

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "SignalRule":
        return cls(
            id=str(data["id"]),
            description=str(data["description"]),
            any=_as_tuple(data.get("any")),
            all=_as_tuple(data.get("all")),
            groups=_as_groups(data.get("groups")),
            artifact_any=_as_tuple(data.get("artifact_any")),
            artifact_text_any=_as_tuple(data.get("artifact_text_any")),
            artifact_text_all=_as_tuple(data.get("artifact_text_all")),
            artifact_text_groups=_as_groups(data.get("artifact_text_groups")),
        )


@dataclass(frozen=True)
class PenaltyRule:
    id: str
    description: str
    points: int
    present_any: tuple[str, ...] = ()
    present_unnegated_any: tuple[str, ...] = ()
    present_all: tuple[str, ...] = ()
    present_groups: tuple[tuple[str, ...], ...] = ()
    present_head_any: tuple[str, ...] = ()
    present_head_all: tuple[str, ...] = ()
    present_head_groups: tuple[tuple[str, ...], ...] = ()
    missing_any: tuple[str, ...] = ()
    missing_all: tuple[str, ...] = ()
    missing_groups: tuple[tuple[str, ...], ...] = ()
    missing_head_any: tuple[str, ...] = ()
    missing_head_all: tuple[str, ...] = ()
    missing_head_groups: tuple[tuple[str, ...], ...] = ()
    missing_artifacts_any: tuple[str, ...] = ()
    present_artifact_text_any: tuple[str, ...] = ()
    present_artifact_text_all: tuple[str, ...] = ()
    present_artifact_text_groups: tuple[tuple[str, ...], ...] = ()
    missing_artifact_text_any: tuple[str, ...] = ()
    missing_artifact_text_all: tuple[str, ...] = ()
    missing_artifact_text_groups: tuple[tuple[str, ...], ...] = ()

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "PenaltyRule":
        return cls(
            id=str(data["id"]),
            description=str(data["description"]),
            points=int(data["points"]),
            present_any=_as_tuple(data.get("present_any")),
            present_unnegated_any=_as_tuple(data.get("present_unnegated_any")),
            present_all=_as_tuple(data.get("present_all")),
            present_groups=_as_groups(data.get("present_groups")),
            present_head_any=_as_tuple(data.get("present_head_any")),
            present_head_all=_as_tuple(data.get("present_head_all")),
            present_head_groups=_as_groups(data.get("present_head_groups")),
            missing_any=_as_tuple(data.get("missing_any")),
            missing_all=_as_tuple(data.get("missing_all")),
            missing_groups=_as_groups(data.get("missing_groups")),
            missing_head_any=_as_tuple(data.get("missing_head_any")),
            missing_head_all=_as_tuple(data.get("missing_head_all")),
            missing_head_groups=_as_groups(data.get("missing_head_groups")),
            missing_artifacts_any=_as_tuple(data.get("missing_artifacts_any")),
            present_artifact_text_any=_as_tuple(data.get("present_artifact_text_any")),
            present_artifact_text_all=_as_tuple(data.get("present_artifact_text_all")),
            present_artifact_text_groups=_as_groups(data.get("present_artifact_text_groups")),
            missing_artifact_text_any=_as_tuple(data.get("missing_artifact_text_any")),
            missing_artifact_text_all=_as_tuple(data.get("missing_artifact_text_all")),
            missing_artifact_text_groups=_as_groups(data.get("missing_artifact_text_groups")),
        )


@dataclass(frozen=True)
class Rubric:
    signals: tuple[SignalRule, ...] = ()
    penalties: tuple[PenaltyRule, ...] = ()

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Rubric":
        signals = tuple(
            SignalRule.from_mapping(item) for item in data.get("signals", [])
        )
        penalties = tuple(
            PenaltyRule.from_mapping(item) for item in data.get("penalties", [])
        )
        return cls(signals=signals, penalties=penalties)


@dataclass(frozen=True)
class TaskDefinition:
    id: str
    title: str
    domain: str
    prompt: str
    intent: str
    family: str = ""
    counted: bool = True
    execution_backed: bool = False
    execution_gated_signals: tuple[str, ...] = ()
    latent_requirements: tuple[str, ...] = ()
    hard_failures: tuple[str, ...] = ()
    strong_signals: tuple[str, ...] = ()
    penalty_notes: tuple[str, ...] = ()
    expected_artifacts: tuple[str, ...] = ()
    visible_constraints: tuple[str, ...] = ()
    hidden_stressors: tuple[str, ...] = ()
    judge_instructions: str = ""
    path: Path = field(default_factory=Path)
    prompt_path: Path = field(default_factory=Path)
    rubric_path: Path = field(default_factory=Path)
    rubric: Rubric = field(default_factory=Rubric)
