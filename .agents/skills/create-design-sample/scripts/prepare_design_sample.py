#!/usr/bin/env python3
"""Prepare a collision-safe Design Sample folder and seed its README."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path


EMPTY_CORE_TOKEN_PATTERNS = {
    "colors": re.compile(r"(?m)^colors:\s*\{\}\s*$"),
    "typography": re.compile(r"(?m)^typography:\s*\{\}\s*$"),
    "rounded": re.compile(r"(?m)^rounded:\s*\{\}\s*$"),
    "spacing": re.compile(r"(?m)^spacing:\s*\{\}\s*$"),
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "design-sample"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Design Sample output folder and seed README.md.",
    )
    parser.add_argument(
        "--design-system-dir",
        required=True,
        help="Path to .design/design-system/<design-system-slug>.",
    )
    parser.add_argument(
        "--sample-name",
        required=True,
        help="Human-readable sample name, used for the folder slug and README title.",
    )
    parser.add_argument(
        "--request",
        required=True,
        help="Original user request that this sample demonstrates.",
    )
    parser.add_argument(
        "--created-at",
        help="ISO timestamp to write into README.md. Defaults to current UTC time.",
    )
    return parser.parse_args()


def read_design_name(design_md: Path, fallback: str) -> str:
    text = design_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return fallback

    end = text.find("\n---", 4)
    if end == -1:
        return fallback

    for line in text[4:end].splitlines():
        if not line.startswith("name:"):
            continue

        raw = line.split(":", 1)[1].strip()
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw.strip("'\"")
        return str(value).strip() or fallback

    return fallback


def placeholder_warnings(design_md: Path) -> list[str]:
    text = design_md.read_text(encoding="utf-8")
    warnings: list[str] = []

    if re.search(r"(?im)\bTODO\b", text):
        warnings.append("DESIGN.md contains TODO scaffold text.")

    for token_name, pattern in EMPTY_CORE_TOKEN_PATTERNS.items():
        if pattern.search(text):
            warnings.append(f"DESIGN.md has an empty `{token_name}: {{}}` token map.")

    return warnings


def unique_sample_dir(outputs_dir: Path, base_slug: str, created_at: dt.datetime) -> Path:
    candidate = outputs_dir / base_slug
    if not candidate.exists():
        return candidate

    timestamp = created_at.strftime("%Y%m%d-%H%M%S")
    candidate = outputs_dir / f"{base_slug}-{timestamp}"
    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        numbered = outputs_dir / f"{base_slug}-{timestamp}-{counter}"
        if not numbered.exists():
            return numbered
        counter += 1


def readme_content(
    sample_name: str,
    request: str,
    design_name: str,
    design_system_dir: Path,
    created_at: dt.datetime,
) -> str:
    return "\n".join(
        [
            f"# {sample_name}",
            "",
            "## Request",
            "",
            request,
            "",
            "## Design System",
            "",
            f"- Name: {design_name}",
            f"- Path: `{design_system_dir.as_posix()}`",
            "",
            "## Generated Files",
            "",
            "_To be completed after artifact generation._",
            "",
            "## Open / Run",
            "",
            "_To be completed after artifact generation._",
            "",
            "## Verification",
            "",
            "_Not yet verified._",
            "",
            "## Gaps / Notes",
            "",
            "_None recorded._",
            "",
            "## Metadata",
            "",
            f"- Created: {created_at.replace(microsecond=0).isoformat()}Z",
            "",
        ],
    )


def main() -> int:
    args = parse_args()
    design_system_dir = Path(args.design_system_dir).expanduser()
    design_md = design_system_dir / "DESIGN.md"

    if not design_system_dir.is_dir():
        print(f"Design System directory not found: {design_system_dir}", file=sys.stderr)
        return 1

    if not design_md.is_file():
        print(f"DESIGN.md not found: {design_md}", file=sys.stderr)
        return 1

    warnings = placeholder_warnings(design_md)
    if warnings:
        print("Selected Design System still looks unfinished:", file=sys.stderr)
        for warning in warnings:
            print(f"- {warning}", file=sys.stderr)
        return 2

    if args.created_at:
        created_at = dt.datetime.fromisoformat(args.created_at.replace("Z", "+00:00"))
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=dt.timezone.utc)
        created_at = created_at.astimezone(dt.timezone.utc).replace(tzinfo=None)
    else:
        created_at = dt.datetime.utcnow()

    design_name = read_design_name(design_md, design_system_dir.name)
    outputs_dir = design_system_dir / "outputs"
    sample_slug = slugify(args.sample_name)
    sample_dir = unique_sample_dir(outputs_dir, sample_slug, created_at)

    sample_dir.mkdir(parents=True)
    readme = sample_dir / "README.md"
    readme.write_text(
        readme_content(
            sample_name=args.sample_name,
            request=args.request,
            design_name=design_name,
            design_system_dir=design_system_dir,
            created_at=created_at,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "sample_dir": sample_dir.as_posix(),
                "readme": readme.as_posix(),
                "design_system_name": design_name,
                "sample_slug": sample_dir.name,
            },
            indent=2,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
