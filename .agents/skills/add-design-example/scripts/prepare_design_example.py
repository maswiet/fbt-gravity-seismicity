#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import sys
import subprocess
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse


SUPPORTED_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".svg",
    ".pdf",
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "example"


def is_supported_visual_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_SUFFIXES


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return str(path.resolve())


def afk_research_command(repo_root: Path) -> list[str]:
    configured = os.environ.get("AFK_RESEARCH_BIN")
    if configured:
        return shlex.split(configured)

    local_bin = repo_root / "node_modules" / ".bin" / "afk-research"
    if local_bin.is_file():
        return [str(local_bin)]

    for parent in Path(__file__).resolve().parents:
        cli = parent / "dist" / "cli.js"
        if cli.is_file():
            return ["node", str(cli)]

    return ["afk-research"]


def resolve_design_system(repo_root: Path, design_system: str) -> tuple[str, Path]:
    command = [
        *afk_research_command(repo_root),
        "design",
        "resolve",
        design_system,
        "--path",
        str(repo_root),
        "--json",
    ]
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        raise ValueError(
            "Design System Resolution command failed: "
            + (completed.stderr.strip() or completed.stdout.strip() or "unknown error"),
        )

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ValueError(f"could not parse Design System Resolution output: {error}") from error

    if result.get("state") != "selected":
        details = "; ".join(str(item) for item in result.get("errors", []))
        raise ValueError(
            f"Design System Resolution failed with state {result.get('state')}"
            + (f": {details}" if details else ""),
        )

    selected = result.get("selected") or {}
    slug = selected.get("slug")
    selected_path = selected.get("path")
    if not slug or not selected_path:
        raise ValueError("Design System Resolution returned an incomplete selected result")

    path_value = Path(str(selected_path))
    path = path_value if path_value.is_absolute() else repo_root / path_value
    return str(slug), path


def copy_artifact(source: Path, destination: Path) -> None:
    if destination.exists():
        raise ValueError(f"refusing to overwrite existing artifact: {destination}")
    shutil.copy2(source, destination)


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def analysis_template(
    *,
    intent: str,
    design_system_slug: str,
    source_label: str,
    stored_source: str | None,
    stored_capture: str | None,
) -> str:
    lines = [
        f"# Design Example Analysis: {intent}",
        "",
        "- Status: proposed",
        f"- Selected Design System: `{design_system_slug}`",
        f"- Source: {source_label}",
        f"- Stored source: {stored_source or 'none'}",
        f"- Capture: {stored_capture or 'none'}",
        "",
        "## Verification",
        "",
        "- [ ] Preserved artifact or rendered capture opens and is readable.",
        "- [ ] Analysis is based on the preserved evidence in this folder.",
        "",
        "## Observed Values",
        "",
        "### Colors",
        "",
        "### Typography",
        "",
        "### Layout And Spacing",
        "",
        "### Elevation And Depth",
        "",
        "### Shapes",
        "",
        "### Components",
        "",
        "## Inferred Guidance",
        "",
        "## Unknowns",
        "",
        "## Conflicts With Existing Design System",
        "",
        "## Proposed Updates",
        "",
        "### README",
        "",
        "### DESIGN.md",
        "",
        "### design_tokens.json",
        "",
        "### tailwind.config.js",
        "",
        "## Acceptance",
        "",
        "- Accepted scopes: none yet",
        "- Rejected scopes: none yet",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare standard provenance files for a Design Example.",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--design-system", required=True, help="Selected Design System name or slug.")
    parser.add_argument("--intent", required=True, help="Short user-provided Design Example Intent.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--source-file", help="Local visual source file.")
    source.add_argument("--source-url", help="HTTP(S) URL source.")
    parser.add_argument("--capture-file", help="Rendered capture for a URL or converted visual artifact.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Date prefix for the example folder.")
    parser.add_argument(
        "--created-at",
        default=None,
        help="ISO timestamp for metadata. Defaults to current local time.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = Path(args.repo_root).resolve()
        design_system_slug, design_system_dir = resolve_design_system(repo_root, args.design_system)
        intent_slug = slugify(args.intent)
        example_id = f"{args.date}-{intent_slug}"
        example_dir = design_system_dir / "examples" / example_id

        if example_dir.exists():
            raise ValueError(f"Design Example folder already exists: {example_dir}")

        stored_source_path: Path | None = None
        stored_capture_path: Path | None = None
        source_metadata: dict[str, object]
        source_label: str

        source_file = Path(args.source_file).resolve() if args.source_file else None
        if source_file is not None:
            if not source_file.is_file():
                raise ValueError(f"source file not found: {source_file}")
            if not is_supported_visual_file(source_file):
                raise ValueError(
                    f"unsupported source file type: {source_file.suffix or '(none)'}",
                )
            source_label = str(source_file)
            source_metadata = {
                "type": "file",
                "original_path": str(source_file),
                "original_name": source_file.name,
            }
        else:
            if not is_http_url(args.source_url):
                raise ValueError(f"unsupported URL source: {args.source_url}")
            source_label = args.source_url
            source_metadata = {
                "type": "url",
                "url": args.source_url,
            }

        capture_file = Path(args.capture_file).resolve() if args.capture_file else None
        if capture_file is not None:
            if not capture_file.is_file():
                raise ValueError(f"capture file not found: {capture_file}")
            if not is_supported_visual_file(capture_file):
                raise ValueError(
                    f"unsupported capture file type: {capture_file.suffix or '(none)'}",
                )

        example_dir.mkdir(parents=True)

        if source_file is not None:
            stored_source_path = example_dir / f"source{source_file.suffix.lower()}"
            copy_artifact(source_file, stored_source_path)
        else:
            stored_source_path = example_dir / "source-url.txt"
            stored_source_path.write_text(args.source_url + "\n", encoding="utf-8")

        if capture_file is not None:
            stored_capture_path = example_dir / f"capture{capture_file.suffix.lower()}"
            copy_artifact(capture_file, stored_capture_path)

        stored_source_relative = repo_relative(stored_source_path, repo_root)
        stored_capture_relative = (
            repo_relative(stored_capture_path, repo_root) if stored_capture_path else None
        )
        source_metadata["stored_path"] = stored_source_relative

        metadata = {
            "schema": "design-example.v1",
            "status": "proposed",
            "created_at": args.created_at
            or datetime.now().astimezone().isoformat(timespec="seconds"),
            "design_system_slug": design_system_slug,
            "design_system_path": repo_relative(design_system_dir, repo_root),
            "example_id": example_id,
            "intent": args.intent,
            "intent_slug": intent_slug,
            "source": source_metadata,
            "capture": (
                {
                    "stored_path": stored_capture_relative,
                }
                if stored_capture_relative
                else None
            ),
            "accepted_scopes": [],
            "rejected_scopes": [],
        }
        write_json(example_dir / "metadata.json", metadata)
        extraction = {
            "schema": "design-example-extraction.v1",
            "example_id": example_id,
            "design_system_slug": design_system_slug,
            "status": "proposed",
            "accepted_scopes": [],
            "rejected_scopes": [],
            "scopes": {},
        }
        write_json(example_dir / "extraction.json", extraction)

        (example_dir / "analysis.md").write_text(
            analysis_template(
                intent=args.intent,
                design_system_slug=design_system_slug,
                source_label=source_label,
                stored_source=stored_source_relative,
                stored_capture=stored_capture_relative,
            ),
            encoding="utf-8",
        )

        print(
            json.dumps(
                {
                    "example_dir": repo_relative(example_dir, repo_root),
                    "metadata": repo_relative(example_dir / "metadata.json", repo_root),
                    "extraction": repo_relative(example_dir / "extraction.json", repo_root),
                    "analysis": repo_relative(example_dir / "analysis.md", repo_root),
                    "stored_source": stored_source_relative,
                    "stored_capture": stored_capture_relative,
                },
                indent=2,
            ),
        )
        return 0
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
