#!/usr/bin/env python3
"""Plan and move non-setup implementation work into .archive."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MANIFEST_PATH = ".agents/afk-research-manifest.json"
ARCHIVE_ROOT = ".archive"
SANDCASTLE_SIDE_EFFECT_FILES = {"package.json", "package-lock.json"}
SANDCASTLE_SIDE_EFFECT_DIRS = {"node_modules"}


class ArchiveError(Exception):
    pass


@dataclass(frozen=True)
class ProtectedPaths:
    exact_files: frozenset[str]
    directories: frozenset[str]


@dataclass(frozen=True)
class Move:
    source: str
    destination: str


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Move implementation work into .archive while preserving AFK setup files.",
    )
    parser.add_argument("--archive-name", required=True, help="Name for the archive folder.")
    parser.add_argument("--root", default=".", help="Project root. Defaults to cwd.")
    parser.add_argument(
        "--allow-missing-manifest",
        action="store_true",
        help="Allow a conservative fallback plan when the AFK manifest is missing.",
    )
    parser.add_argument("--apply", action="store_true", help="Move files after planning.")
    parser.add_argument("--json", action="store_true", help="Print the plan as JSON.")
    args = parser.parse_args(argv)

    try:
        plan = build_plan(
            root=Path(args.root),
            archive_name=args.archive_name,
            allow_missing_manifest=args.allow_missing_manifest,
        )

        if args.apply:
            apply_plan(plan)
            plan["applied"] = True

        if args.json:
            print(json.dumps(plan, indent=2, sort_keys=True))
        else:
            print_plan(plan, applied=args.apply)

        return 0
    except ArchiveError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def build_plan(
    *,
    root: Path,
    archive_name: str,
    allow_missing_manifest: bool,
) -> dict[str, Any]:
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        raise ArchiveError(f"root is not a directory: {root}")

    normalized_name = normalize_archive_name(archive_name)
    archive_root = root / ARCHIVE_ROOT
    archive_path = archive_root / normalized_name
    if archive_path.exists():
        raise ArchiveError(f"archive already exists: {relative_to_root(archive_path, root)}")

    manifest, manifest_found = load_manifest(root, allow_missing_manifest)
    protected = build_protected_paths(manifest)
    moves = collect_moves(root, archive_path, protected)

    for move in moves:
        destination = root / move.destination
        if destination.exists():
            raise ArchiveError(f"planned destination already exists: {move.destination}")

    warnings: list[str] = []
    if normalized_name != archive_name:
        warnings.append(f"Archive name normalized from {archive_name!r} to {normalized_name!r}.")
    if not manifest_found:
        warnings.append(
            "AFK manifest is missing; this fallback plan preserves dot-prefixed top-level paths only.",
        )
    if not moves:
        warnings.append("No implementation paths were found to archive.")

    return {
        "root": str(root),
        "archive_name": normalized_name,
        "archive_path": to_posix(Path(ARCHIVE_ROOT) / normalized_name),
        "manifest_path": MANIFEST_PATH,
        "manifest_found": manifest_found,
        "allow_missing_manifest": allow_missing_manifest,
        "protected_file_count": len(protected.exact_files),
        "protected_directory_count": len(protected.directories),
        "moves": [move.__dict__ for move in moves],
        "warnings": warnings,
        "applied": False,
    }


def normalize_archive_name(raw_name: str) -> str:
    name = raw_name.strip()
    if not name:
        raise ArchiveError("archive name cannot be empty")
    if "/" in name or "\\" in name:
        raise ArchiveError("archive name must not contain path separators")

    normalized = re.sub(r"[^a-z0-9._-]+", "-", name.lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-._")
    if not normalized or normalized in {".", ".."}:
        raise ArchiveError(f"archive name does not produce a safe folder name: {raw_name!r}")
    return normalized


def load_manifest(root: Path, allow_missing_manifest: bool) -> tuple[dict[str, Any] | None, bool]:
    manifest_file = root / MANIFEST_PATH
    if not manifest_file.exists():
        if allow_missing_manifest:
            return None, False
        raise ArchiveError(
            f"{MANIFEST_PATH} is missing. Ask the user before planning with "
            "--allow-missing-manifest.",
        )

    try:
        return json.loads(manifest_file.read_text(encoding="utf-8")), True
    except json.JSONDecodeError as error:
        raise ArchiveError(f"could not parse {MANIFEST_PATH}: {error}") from error


def build_protected_paths(manifest: dict[str, Any] | None) -> ProtectedPaths:
    exact_files: set[str] = set()
    directories: set[str] = set()

    if manifest:
        for entry in manifest.get("files", []):
            path = normalize_manifest_path(entry.get("path"))
            if path:
                exact_files.add(path)

        for entry in manifest.get("conflicts", []):
            path = normalize_manifest_path(entry.get("generatedPath"))
            if path:
                exact_files.add(path)

        options = manifest.get("options", {})
        preserve_sandcastle = bool(options.get("sandcastle")) or bool(
            manifest.get("packageJsonCreated"),
        )
        if preserve_sandcastle:
            exact_files.update(SANDCASTLE_SIDE_EFFECT_FILES)
            directories.update(SANDCASTLE_SIDE_EFFECT_DIRS)

    return ProtectedPaths(frozenset(exact_files), frozenset(directories))


def normalize_manifest_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = to_posix(Path(value.strip()))
    if path == "." or path.startswith("../") or path == "..":
        return None
    return path


def collect_moves(root: Path, archive_path: Path, protected: ProtectedPaths) -> list[Move]:
    moves: list[Move] = []

    def visit(path: Path) -> None:
        rel = relative_to_root(path, root)
        if rel == ".":
            for child in sorted(path.iterdir(), key=lambda item: item.name):
                visit(child)
            return

        if should_preserve(rel, protected):
            return

        if path.is_dir() and not path.is_symlink():
            if has_protected_descendant(rel, protected):
                for child in sorted(path.iterdir(), key=lambda item: item.name):
                    visit(child)
                return

        destination = to_posix(Path(ARCHIVE_ROOT) / archive_path.name / Path(rel))
        moves.append(Move(source=rel, destination=destination))

    visit(root)
    return sorted(moves, key=lambda move: move.source)


def should_preserve(rel: str, protected: ProtectedPaths) -> bool:
    parts = rel.split("/")
    if parts[0].startswith("."):
        return True
    if rel in protected.exact_files:
        return True
    return any(rel == directory or rel.startswith(f"{directory}/") for directory in protected.directories)


def has_protected_descendant(rel: str, protected: ProtectedPaths) -> bool:
    prefix = f"{rel}/"
    if any(path.startswith(prefix) for path in protected.exact_files):
        return True
    return any(directory == rel or directory.startswith(prefix) for directory in protected.directories)


def apply_plan(plan: dict[str, Any]) -> None:
    moves = plan["moves"]
    if not moves:
        return

    root = Path(plan["root"])
    archive_path = root / plan["archive_path"]
    archive_path.mkdir(parents=True, exist_ok=False)

    for move in moves:
        source = root / move["source"]
        destination = root / move["destination"]
        if not source.exists() and not source.is_symlink():
            raise ArchiveError(f"source no longer exists: {move['source']}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))


def print_plan(plan: dict[str, Any], *, applied: bool) -> None:
    status = "Archive applied" if applied else "Archive dry run"
    print(status)
    print(f"Root: {plan['root']}")
    print(f"Archive: {plan['archive_path']}")
    print(f"Manifest: {'found' if plan['manifest_found'] else 'missing'}")

    if plan["warnings"]:
        print("\nWarnings:")
        for warning in plan["warnings"]:
            print(f"  - {warning}")

    print("\nMoves:")
    if not plan["moves"]:
        print("  (none)")
    else:
        for move in plan["moves"]:
            print(f"  - {move['source']} -> {move['destination']}")

    if not applied:
        print("\nRun again with --apply to move these paths.")


def relative_to_root(path: Path, root: Path) -> str:
    return to_posix(path.relative_to(root))


def to_posix(path: Path) -> str:
    return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
