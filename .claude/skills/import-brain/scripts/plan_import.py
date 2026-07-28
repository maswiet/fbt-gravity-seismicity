#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath


def _add_local_lib_to_path() -> None:
    for parent in Path(__file__).resolve().parents:
        if parent.name in {".agents", ".claude"}:
            candidate = parent / "lib"
            if candidate.is_dir():
                sys.path.insert(0, str(candidate))
                return

    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".agents" / "lib"
        if candidate.is_dir():
            sys.path.insert(0, str(candidate))
            return


_add_local_lib_to_path()

from brain_transfer_paths import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    import_plan_path,
    import_stage_root,
    is_relative_to,
    resolve_output_dir,
)


ALLOWED_CONTENT_ROOTS = {"AGENTS.md", "CLAUDE.md", "raw", "wiki"}
IGNORED_PARTS = {"__MACOSX"}
IGNORED_NAMES = {".DS_Store"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_parts(name: str) -> tuple[str, ...] | None:
    raw_name = name.replace("\\", "/")
    if raw_name.startswith("/"):
        raise ValueError(f"unsafe absolute archive path: {name}")
    parts = PurePosixPath(raw_name).parts
    if not parts:
        return None
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"unsafe relative archive path: {name}")
    if any(part in IGNORED_PARTS for part in parts):
        return None
    if parts[-1] in IGNORED_NAMES or parts[-1].startswith("._"):
        return None
    if any(part == ".git" for part in parts):
        raise ValueError(f"git metadata is not allowed in a Brain Archive: {name}")
    return parts


def classify(relative_path: str) -> str:
    if relative_path in {"AGENTS.md", "CLAUDE.md"}:
        return "schema"
    if relative_path == "wiki/index.md":
        return "operational-index"
    if relative_path == "wiki/log.md":
        return "operational-log"
    if relative_path.startswith("raw/"):
        return "raw"
    if relative_path.startswith("wiki/") and relative_path.endswith(".md"):
        return "wiki-markdown"
    if relative_path.startswith("wiki/"):
        return "wiki-other"
    return "other"


def action_for(kind: str, current_exists: bool, same_hash: bool) -> str:
    if current_exists and same_hash:
        return "skip-identical"
    if kind == "schema":
        return "archive-schema-review"
    if kind == "operational-index":
        return "archive-imported-index"
    if kind == "operational-log":
        return "archive-imported-log"
    if not current_exists:
        return "add"
    if kind == "raw":
        return "preserve-raw-collision"
    if kind == "wiki-markdown":
        return "semantic-merge"
    if kind == "wiki-other":
        return "archive-wiki-collision"
    return "archive-other-collision"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and plan a non-destructive .brain import.")
    parser.add_argument("archive", help="Path to a .brain zip archive.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to the current directory.")
    parser.add_argument("--brain-dir", default=".brain", help="Current brain directory relative to repo root.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for staged files and plan JSON.")
    return parser.parse_args()


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.name}-{index}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not find available path near {path}")


def normalize_members(zip_file: zipfile.ZipFile) -> tuple[str, list[tuple[zipfile.ZipInfo, str]]]:
    candidates: list[tuple[zipfile.ZipInfo, tuple[str, ...]]] = []
    for info in zip_file.infolist():
        parts = safe_parts(info.filename)
        if parts is None:
            continue
        if info.is_dir():
            continue
        candidates.append((info, parts))

    if not candidates:
        raise ValueError("archive does not contain any importable files")

    top_levels = {parts[0] for _, parts in candidates}
    if top_levels == {".brain"}:
        normalized = []
        seen = set()
        for info, parts in candidates:
            if len(parts) == 1:
                continue
            relative_path = PurePosixPath(*parts[1:]).as_posix()
            if relative_path in seen:
                raise ValueError(f"duplicate normalized archive path: {relative_path}")
            seen.add(relative_path)
            normalized.append((info, relative_path))
        return "rooted-.brain", normalized

    if top_levels.issubset(ALLOWED_CONTENT_ROOTS) and top_levels.intersection(ALLOWED_CONTENT_ROOTS):
        normalized = []
        seen = set()
        for info, parts in candidates:
            relative_path = PurePosixPath(*parts).as_posix()
            if relative_path in seen:
                raise ValueError(f"duplicate normalized archive path: {relative_path}")
            seen.add(relative_path)
            normalized.append((info, relative_path))
        return "contents-only", normalized

    raise ValueError(
        "ambiguous archive shape: expected a single .brain/ root or direct .brain contents; "
        f"found top-level entries {sorted(top_levels)}"
    )


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    brain_dir = (repo_root / args.brain_dir).resolve()
    archive_path = Path(args.archive).expanduser().resolve()
    output_dir = resolve_output_dir(repo_root, args.output_dir)

    if not brain_dir.is_dir():
        print(f"error: current brain directory not found: {brain_dir}", file=sys.stderr)
        print("run setup-brain before importing into this repository", file=sys.stderr)
        return 1
    if not archive_path.is_file():
        print(f"error: archive not found: {archive_path}", file=sys.stderr)
        return 1
    if is_relative_to(output_dir, brain_dir):
        print("error: output directory must not be inside .brain", file=sys.stderr)
        return 1

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    stage_root = unique_path(import_stage_root(output_dir, timestamp))
    staged_brain = stage_root / "brain"
    plan_path = unique_path(import_plan_path(output_dir, timestamp))
    staged_brain.mkdir(parents=True)

    try:
        with zipfile.ZipFile(archive_path, "r") as zip_file:
            archive_shape, normalized = normalize_members(zip_file)
            entries = []
            for info, relative_path in sorted(normalized, key=lambda item: item[1]):
                data = zip_file.read(info)
                staged_path = staged_brain / relative_path
                staged_path.parent.mkdir(parents=True, exist_ok=True)
                staged_path.write_bytes(data)

                current_path = brain_dir / relative_path
                current_exists = current_path.exists()
                imported_hash = sha256_bytes(data)
                current_hash = sha256_file(current_path) if current_path.is_file() else None
                same_hash = current_exists and current_hash == imported_hash
                kind = classify(relative_path)
                action = action_for(kind, current_exists, same_hash)
                entries.append(
                    {
                        "relative_path": relative_path,
                        "kind": kind,
                        "action": action,
                        "current_exists": current_exists,
                        "current_path": str(current_path),
                        "staged_path": str(staged_path),
                        "imported_size": len(data),
                        "imported_sha256": imported_hash,
                        "current_sha256": current_hash,
                    }
                )
    except Exception:
        shutil.rmtree(stage_root, ignore_errors=True)
        raise

    summary = Counter(entry["action"] for entry in entries)
    plan = {
        "schema": "brain-import-plan.v1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "archive_path": str(archive_path),
        "archive_shape": archive_shape,
        "current_brain_dir": str(brain_dir),
        "stage_dir": str(staged_brain),
        "plan_path": str(plan_path),
        "entry_count": len(entries),
        "summary": dict(sorted(summary.items())),
        "entries": entries,
    }
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(
        {
            "plan": str(plan_path),
            "stage_dir": str(staged_brain),
            "archive_shape": archive_shape,
            "entry_count": len(entries),
            "summary": dict(sorted(summary.items())),
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
