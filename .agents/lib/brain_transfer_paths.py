"""Shared path rules for Second Brain transfer artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_OUTPUT_DIR = ".outputs"
DEFAULT_OUTPUT_IGNORE_RULE = f"{DEFAULT_OUTPUT_DIR}/"
EXPORT_PREFIX = "brain-export"
IMPORT_STAGE_PREFIX = "brain-import-stage"
IMPORT_PLAN_PREFIX = "brain-import-plan"


@dataclass(frozen=True)
class ExportArtifactPaths:
    zip_path: Path
    manifest_path: Path
    checksum_path: Path


def resolve_output_dir(repo_root: Path, output_dir: str | None = None) -> Path:
    return (repo_root / (output_dir or DEFAULT_OUTPUT_DIR)).resolve()


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def default_export_name(timestamp: str) -> str:
    return f"{EXPORT_PREFIX}-{timestamp}"


def export_artifact_paths(output_dir: Path, base_name: str) -> ExportArtifactPaths:
    return ExportArtifactPaths(
        zip_path=output_dir / f"{base_name}.zip",
        manifest_path=output_dir / f"{base_name}.manifest.json",
        checksum_path=output_dir / f"{base_name}.zip.sha256",
    )


def import_stage_root(output_dir: Path, timestamp: str) -> Path:
    return output_dir / f"{IMPORT_STAGE_PREFIX}-{timestamp}"


def import_plan_path(output_dir: Path, timestamp: str) -> Path:
    return output_dir / f"{IMPORT_PLAN_PREFIX}-{timestamp}.json"
