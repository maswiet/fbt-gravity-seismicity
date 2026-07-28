#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path


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
    default_export_name,
    export_artifact_paths,
    is_relative_to,
    resolve_output_dir,
)


IGNORED_NAMES = {
    ".DS_Store",
    ".AppleDouble",
    ".LSOverride",
    ".Spotlight-V100",
    ".Trashes",
    "__MACOSX",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    ".git",
}

IGNORED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".tmp",
    ".bak",
    ".swp",
    ".swo",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_skip(path: Path, relative_path: Path) -> bool:
    for part in relative_path.parts:
        if part in IGNORED_NAMES or part.startswith("._"):
            return True
    return path.suffix in IGNORED_SUFFIXES


def iter_brain_entries(brain_dir: Path):
    for path in sorted(brain_dir.rglob("*")):
        relative_path = path.relative_to(brain_dir)
        if should_skip(path, relative_path):
            continue
        yield path, relative_path


def add_directory(zip_file: zipfile.ZipFile, archive_name: str) -> None:
    info = zipfile.ZipInfo(archive_name.rstrip("/") + "/")
    info.external_attr = 0o755 << 16
    zip_file.writestr(info, b"")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export .brain as a portable zip archive.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to the current directory.")
    parser.add_argument("--brain-dir", default=".brain", help="Brain directory relative to repo root.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory relative to repo root.")
    parser.add_argument("--name", help="Base output name without extension.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    brain_dir = (repo_root / args.brain_dir).resolve()
    output_dir = resolve_output_dir(repo_root, args.output_dir)

    if not brain_dir.is_dir():
        print(f"error: brain directory not found: {brain_dir}", file=sys.stderr)
        return 1

    if is_relative_to(output_dir, brain_dir):
        print("error: output directory must not be inside .brain", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    base_name = args.name or default_export_name(timestamp)
    paths = export_artifact_paths(output_dir, base_name)
    zip_path = paths.zip_path
    manifest_path = paths.manifest_path
    checksum_path = paths.checksum_path

    if zip_path.exists() or manifest_path.exists() or checksum_path.exists():
        print(f"error: output files already exist for base name {base_name}", file=sys.stderr)
        return 1

    files = []
    skipped_symlinks = []
    directory_count = 0

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        add_directory(archive, ".brain/")
        for path, relative_path in iter_brain_entries(brain_dir):
            archive_name = ".brain/" + relative_path.as_posix()
            if path.is_symlink():
                skipped_symlinks.append(archive_name)
                continue
            if path.is_dir():
                add_directory(archive, archive_name)
                directory_count += 1
                continue
            digest = sha256_file(path)
            size = path.stat().st_size
            archive.write(path, archive_name)
            files.append(
                {
                    "path": archive_name,
                    "size": size,
                    "sha256": digest,
                }
            )

    archive_sha256 = sha256_file(zip_path)
    total_size = sum(item["size"] for item in files)
    manifest = {
        "schema": "brain-export.v1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "archive_format": "rooted-.brain",
        "brain_dir": str(brain_dir),
        "archive_path": str(zip_path),
        "archive_sha256": archive_sha256,
        "file_count": len(files),
        "directory_count": directory_count,
        "total_uncompressed_file_bytes": total_size,
        "skipped_symlinks": skipped_symlinks,
        "files": files,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    checksum_path.write_text(f"{archive_sha256}  {zip_path.name}\n", encoding="utf-8")

    print(json.dumps(
        {
            "archive": str(zip_path),
            "manifest": str(manifest_path),
            "checksum": str(checksum_path),
            "archive_sha256": archive_sha256,
            "file_count": len(files),
            "directory_count": directory_count,
            "skipped_symlink_count": len(skipped_symlinks),
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
