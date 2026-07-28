#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


CANONICAL_ARTIFACTS = [
    "README.md",
    "DESIGN.md",
    "design_tokens.json",
    "tailwind.config.js",
]

STATUS_BLOCK_START = "<!-- afk-research:design-example-status -->"
STATUS_BLOCK_END = "<!-- /afk-research:design-example-status -->"

SCOPE_CONFIG = {
    "readme_orientation": {
        "readme": True,
        "design_section": None,
        "token_group": None,
        "tailwind_key": None,
    },
    "colors": {
        "readme": False,
        "design_section": "Colors",
        "token_group": "colors",
        "tailwind_key": "colors",
    },
    "typography": {
        "readme": False,
        "design_section": "Typography",
        "token_group": "typography",
        "tailwind_key": "fontFamily",
    },
    "layout_spacing": {
        "readme": False,
        "design_section": "Layout & Spacing",
        "token_group": "spacing",
        "tailwind_key": "spacing",
    },
    "spacing": {
        "readme": False,
        "design_section": "Layout & Spacing",
        "token_group": "spacing",
        "tailwind_key": "spacing",
    },
    "elevation_depth": {
        "readme": False,
        "design_section": "Elevation & Depth",
        "token_group": None,
        "tailwind_key": None,
    },
    "shapes": {
        "readme": False,
        "design_section": "Shapes",
        "token_group": "rounded",
        "tailwind_key": "borderRadius",
    },
    "components": {
        "readme": False,
        "design_section": "Components",
        "token_group": "components",
        "tailwind_key": None,
    },
}

EVIDENCE_LEVELS = {"observed", "inferred", "unknown"}


class ExtractionError(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ExtractionError(f"could not parse JSON at {path}: {error}") from error


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


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


def resolve_design_system(repo_root: Path, design_system: str) -> Path:
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
        raise ExtractionError(
            "Design System Resolution command failed: "
            + (completed.stderr.strip() or completed.stdout.strip() or "unknown error"),
        )

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ExtractionError(f"could not parse Design System Resolution output: {error}") from error

    if result.get("state") != "selected":
        details = "; ".join(str(item) for item in result.get("errors", []))
        raise ExtractionError(
            f"Design System Resolution failed with state {result.get('state')}"
            + (f": {details}" if details else ""),
        )

    selected = result.get("selected") or {}
    selected_path = selected.get("path")
    if not selected_path:
        raise ExtractionError("Design System Resolution returned an incomplete selected result")

    path_value = Path(str(selected_path))
    return path_value if path_value.is_absolute() else repo_root / path_value


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "example"


def resolve_example_path(repo_root: Path, design_system_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        repo_candidate = repo_root / path
        if repo_candidate.exists():
            path = repo_candidate
        else:
            path = design_system_dir / "examples" / raw_path

    if path.is_file() and path.name == "extraction.json":
        path = path.parent

    if not path.is_dir():
        raise ExtractionError(f"example folder not found: {raw_path}")

    extraction = path / "extraction.json"
    if not extraction.is_file():
        raise ExtractionError(f"extraction.json not found in example folder: {raw_path}")

    return path.resolve()


def unwrap_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value and set(value).issubset(
        {"value", "evidence_level", "confidence", "note"},
    ):
        return value["value"]
    if isinstance(value, dict):
        return {key: unwrap_value(child) for key, child in value.items() if key != "evidence_level"}
    if isinstance(value, list):
        return [unwrap_value(child) for child in value]
    return value


def evidence_levels(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        level = value.get("evidence_level")
        if level is not None:
            found.append(str(level))
        for child in value.values():
            found.extend(evidence_levels(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(evidence_levels(child))
    return found


def validate_evidence(scope_id: str, scope: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    levels = evidence_levels(scope)
    for level in levels:
        if level not in EVIDENCE_LEVELS:
            errors.append(f"{scope_id}: unsupported evidence level {level!r}")
    if "unknown" in levels:
        errors.append(f"{scope_id}: unknown evidence cannot be accepted")
    return errors


def scope_updates(scope_id: str, scope: dict[str, Any]) -> dict[str, Any]:
    config = SCOPE_CONFIG.get(scope_id)
    if not config:
        raise ExtractionError(f"unsupported accepted scope: {scope_id}")

    updates: dict[str, Any] = {
        "readme_description": None,
        "design_guidance": None,
        "token_group": config["token_group"],
        "tokens": {},
        "design_tokens": {},
        "tailwind_key": config["tailwind_key"],
        "tailwind": {},
    }

    if config["readme"]:
        readme = scope.get("readme") or {}
        description = readme.get("description") or scope.get("description")
        if description:
            updates["readme_description"] = str(unwrap_value(description)).strip()
        return updates

    guidance = scope.get("guidance") or scope.get("design_guidance")
    if guidance:
        updates["design_guidance"] = str(unwrap_value(guidance)).strip()

    token_group = config["token_group"]
    if token_group:
        token_updates = scope.get("tokens", {}).get(token_group)
        if token_updates is None and token_group in scope:
            token_updates = scope[token_group]
        if token_updates is not None:
            updates["tokens"] = unwrap_value(token_updates)

        design_token_updates = scope.get("design_tokens", {}).get(token_group)
        if design_token_updates is None:
            design_token_updates = scope.get("design_tokens")
        if design_token_updates is not None:
            updates["design_tokens"] = unwrap_value(design_token_updates)
        elif updates["tokens"]:
            updates["design_tokens"] = design_token_values(token_group, updates["tokens"])

    tailwind_key = config["tailwind_key"]
    if tailwind_key:
        tailwind = scope.get("tailwind", {})
        tailwind_extend = tailwind.get("theme", {}).get("extend")
        if isinstance(tailwind_extend, dict):
            updates["tailwind"] = unwrap_value(tailwind_extend)
        else:
            tailwind_updates = tailwind.get(tailwind_key)
            if tailwind_updates is None and updates["tokens"]:
                tailwind_updates = updates["tokens"]
            if tailwind_updates is not None:
                updates["tailwind"] = {tailwind_key: unwrap_value(tailwind_updates)}

    return updates


def design_token_values(group: str, values: Any) -> Any:
    if not isinstance(values, dict):
        return values

    token_type = {
        "colors": "color",
        "typography": "typography",
        "rounded": "dimension",
        "spacing": "dimension",
        "components": "string",
    }.get(group, "string")

    converted = {}
    for key, value in values.items():
        if isinstance(value, dict) and "$value" in value:
            converted[key] = value
        elif isinstance(value, dict):
            converted[key] = design_token_values(group, value)
        else:
            converted[key] = {"$type": token_type, "$value": value}
    return converted


def validate_scope_updates(scope_id: str, updates: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    config = SCOPE_CONFIG[scope_id]
    if config["readme"]:
        if not updates["readme_description"]:
            errors.append(f"{scope_id}: missing readme.description")
        return errors

    if config["design_section"] and not updates["design_guidance"]:
        errors.append(f"{scope_id}: missing guidance for DESIGN.md")

    if config["token_group"]:
        if not updates["tokens"]:
            errors.append(f"{scope_id}: missing tokens.{config['token_group']}")
        if not updates["design_tokens"]:
            errors.append(f"{scope_id}: missing design_tokens.{config['token_group']}")

    if config["tailwind_key"] and not updates["tailwind"]:
        errors.append(f"{scope_id}: missing tailwind update for {config['tailwind_key']}")

    return errors


def merge_or_conflict(
    merged: dict[str, Any],
    path: tuple[str, ...],
    value: Any,
    source: str,
    conflicts: list[dict[str, Any]],
) -> None:
    current = merged
    for part in path[:-1]:
        current = current.setdefault(part, {})
    leaf = path[-1]
    if leaf in current and current[leaf] != value:
        conflicts.append(
            {
                "path": ".".join(path),
                "existing": current[leaf],
                "incoming": value,
                "source": source,
            },
        )
        return
    current[leaf] = value


def collect_plan_data(
    repo_root: Path,
    design_system: str,
    examples: list[str],
) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    design_system_dir = resolve_design_system(repo_root, design_system)
    example_dirs = [resolve_example_path(repo_root, design_system_dir, example) for example in examples]

    errors: list[str] = []
    conflicts: list[dict[str, Any]] = []
    accepted_records: list[dict[str, Any]] = []
    rejected_by_example: dict[str, list[str]] = {}

    merged_updates: dict[str, Any] = {}

    for example_dir in example_dirs:
        extraction_path = example_dir / "extraction.json"
        extraction = read_json(extraction_path)
        if extraction.get("schema") != "design-example-extraction.v1":
            errors.append(f"{repo_relative(extraction_path, repo_root)}: unsupported schema")
            continue

        accepted_scopes = extraction.get("accepted_scopes", [])
        rejected_scopes = extraction.get("rejected_scopes", [])
        if not isinstance(accepted_scopes, list):
            errors.append(f"{repo_relative(extraction_path, repo_root)}: accepted_scopes must be a list")
            continue
        if not isinstance(rejected_scopes, list):
            errors.append(f"{repo_relative(extraction_path, repo_root)}: rejected_scopes must be a list")
            rejected_scopes = []

        example_rel = repo_relative(example_dir, repo_root)
        rejected_by_example[example_rel] = [str(scope) for scope in rejected_scopes]
        scopes = extraction.get("scopes", {})
        if not isinstance(scopes, dict):
            errors.append(f"{repo_relative(extraction_path, repo_root)}: scopes must be an object")
            continue

        for raw_scope_id in accepted_scopes:
            scope_id = str(raw_scope_id)
            scope = scopes.get(scope_id)
            if not isinstance(scope, dict):
                errors.append(f"{repo_relative(extraction_path, repo_root)}: missing scope {scope_id}")
                continue
            if scope_id not in SCOPE_CONFIG:
                errors.append(f"{repo_relative(extraction_path, repo_root)}: unsupported scope {scope_id}")
                continue

            errors.extend(validate_evidence(scope_id, scope))
            updates = scope_updates(scope_id, scope)
            errors.extend(validate_scope_updates(scope_id, updates))

            source = f"{example_rel}:{scope_id}"
            accepted_records.append(
                {
                    "example": example_rel,
                    "scope": scope_id,
                    "evidence_levels": sorted(set(evidence_levels(scope))),
                },
            )

            readme_description = updates.get("readme_description")
            if readme_description:
                merge_or_conflict(
                    merged_updates,
                    ("readme", "description"),
                    readme_description,
                    source,
                    conflicts,
                )

            design_guidance = updates.get("design_guidance")
            if design_guidance:
                section = SCOPE_CONFIG[scope_id]["design_section"]
                merge_or_conflict(
                    merged_updates,
                    ("design_md", "sections", str(section)),
                    design_guidance,
                    source,
                    conflicts,
                )

            token_group = updates.get("token_group")
            if token_group:
                for key, value in flatten_mapping(updates.get("tokens", {})).items():
                    merge_or_conflict(
                        merged_updates,
                        ("design_md", "tokens", token_group, *key),
                        value,
                        source,
                        conflicts,
                    )
                for key, value in flatten_mapping(updates.get("design_tokens", {})).items():
                    merge_or_conflict(
                        merged_updates,
                        ("design_tokens", token_group, *key),
                        value,
                        source,
                        conflicts,
                    )

            tailwind_key = updates.get("tailwind_key")
            if tailwind_key:
                for extend_key, extend_values in updates.get("tailwind", {}).items():
                    for key, value in flatten_mapping(extend_values).items():
                        merge_or_conflict(
                            merged_updates,
                            ("tailwind", str(extend_key), *key),
                            value,
                            source,
                            conflicts,
                        )

    rejected_records = [
        {"example": example, "scopes": scopes}
        for example, scopes in rejected_by_example.items()
    ]
    plan_context = {
        "design_system_dir": design_system_dir,
        "example_dirs": example_dirs,
        "accepted_records": accepted_records,
        "rejected_records": rejected_records,
        "merged_updates": unflatten_merged_updates(merged_updates),
    }
    return plan_context, errors, conflicts


def flatten_mapping(value: Any, prefix: tuple[str, ...] = ()) -> dict[tuple[str, ...], Any]:
    if not isinstance(value, dict):
        return {prefix or ("value",): value}
    flattened: dict[tuple[str, ...], Any] = {}
    for key, child in value.items():
        if isinstance(child, dict) and "$value" not in child:
            flattened.update(flatten_mapping(child, (*prefix, str(key))))
        else:
            flattened[(*prefix, str(key))] = child
    return flattened


def set_nested(target: dict[str, Any], path: list[str], value: Any) -> None:
    current = target
    for part in path[:-1]:
        current = current.setdefault(part, {})
    current[path[-1]] = value


def unflatten_merged_updates(merged: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}

    def visit(prefix: list[str], value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                visit([*prefix, key], child)
        else:
            set_nested(result, prefix, value)

    visit([], merged)
    return result


def build_planned_writes(
    repo_root: Path,
    design_system_dir: Path,
    merged_updates: dict[str, Any],
) -> list[dict[str, Any]]:
    writes: list[dict[str, Any]] = []

    readme_path = design_system_dir / "README.md"
    design_md_path = design_system_dir / "DESIGN.md"
    design_tokens_path = design_system_dir / "design_tokens.json"
    tailwind_path = design_system_dir / "tailwind.config.js"

    if "readme" in merged_updates:
        before = readme_path.read_text(encoding="utf-8")
        after = patch_readme_description(before, merged_updates["readme"]["description"])
        add_write(writes, repo_root, readme_path, before, after)

    if "design_md" in merged_updates:
        before = design_md_path.read_text(encoding="utf-8")
        after = before
        token_updates = merged_updates["design_md"].get("tokens", {})
        for group, values in token_updates.items():
            after = patch_frontmatter_group(after, group, values)
        for section, body in merged_updates["design_md"].get("sections", {}).items():
            after = patch_markdown_section(after, section, body)
        add_write(writes, repo_root, design_md_path, before, after)

    if "design_tokens" in merged_updates:
        before = design_tokens_path.read_text(encoding="utf-8")
        data = json.loads(before)
        for group, values in merged_updates["design_tokens"].items():
            data[group] = deep_merge(data.get(group, {}), values)
        after = json.dumps(data, indent=2, sort_keys=True) + "\n"
        add_write(writes, repo_root, design_tokens_path, before, after)

    if "tailwind" in merged_updates:
        before = tailwind_path.read_text(encoding="utf-8")
        after = before
        for key, values in merged_updates["tailwind"].items():
            after = patch_tailwind_extend_property(after, key, values)
        add_write(writes, repo_root, tailwind_path, before, after)

    return writes


def add_write(
    writes: list[dict[str, Any]],
    repo_root: Path,
    path: Path,
    before: str,
    after: str,
) -> None:
    if before == after:
        return
    writes.append(
        {
            "path": repo_relative(path, repo_root),
            "before_sha256": sha256_bytes(before.encode("utf-8")),
            "after_sha256": sha256_bytes(after.encode("utf-8")),
            "content": after,
        },
    )


def patch_readme_description(content: str, description: str) -> str:
    lines = content.splitlines()
    if not lines:
        return description + "\n"
    if not lines[0].startswith("# "):
        return content.rstrip() + "\n\n" + description.strip() + "\n"

    next_heading = None
    for index, line in enumerate(lines[1:], start=1):
        if line.startswith("## "):
            next_heading = index
            break

    if next_heading is None:
        return lines[0] + "\n\n" + description.strip() + "\n"

    new_lines = [lines[0], "", description.strip(), "", *lines[next_heading:]]
    return "\n".join(new_lines).rstrip() + "\n"


def patch_frontmatter_group(content: str, group: str, values: Any) -> str:
    if not content.startswith("---\n"):
        block = "---\n" + yaml_mapping({group: values}) + "---\n\n"
        return block + content

    end = content.find("\n---", 4)
    if end == -1:
        raise ExtractionError("DESIGN.md frontmatter is not closed")

    frontmatter = content[4:end].splitlines()
    rest = content[end:]
    updated = replace_yaml_group(frontmatter, group, values)
    return "---\n" + "\n".join(updated).rstrip() + "\n" + rest


def replace_yaml_group(lines: list[str], group: str, values: Any) -> list[str]:
    start = None
    for index, line in enumerate(lines):
        if re.match(rf"^{re.escape(group)}\s*:", line):
            start = index
            break

    group_lines = yaml_mapping({group: values}).rstrip().splitlines()
    if start is None:
        return [*lines, *group_lines]

    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line and not line.startswith((" ", "\t")) and re.match(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:", line):
            break
        end += 1

    return [*lines[:start], *group_lines, *lines[end:]]


def yaml_mapping(data: dict[str, Any], indent: int = 0) -> str:
    lines: list[str] = []
    for key, value in data.items():
        prefix = " " * indent + str(key) + ":"
        if isinstance(value, dict):
            if not value:
                lines.append(prefix + " {}")
            else:
                lines.append(prefix)
                lines.append(yaml_mapping(value, indent + 2).rstrip())
        else:
            lines.append(prefix + " " + yaml_scalar(value))
    return "\n".join(lines) + "\n"


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def patch_markdown_section(content: str, heading: str, body: str) -> str:
    pattern = re.compile(rf"(?m)^##\s+{re.escape(heading)}\s*$")
    match = pattern.search(content)
    replacement = f"## {heading}\n\n{body.strip()}\n"
    if not match:
        return content.rstrip() + "\n\n" + replacement

    next_match = re.search(r"(?m)^##\s+", content[match.end() :])
    if next_match:
        end = match.end() + next_match.start()
        return content[: match.start()] + replacement + "\n" + content[end:].lstrip("\n")
    return content[: match.start()] + replacement


def deep_merge(left: Any, right: Any) -> Any:
    if not isinstance(left, dict) or not isinstance(right, dict):
        return copy.deepcopy(right)
    merged = copy.deepcopy(left)
    for key, value in right.items():
        merged[key] = deep_merge(merged.get(key), value)
    return merged


def patch_tailwind_extend_property(content: str, key: str, values: Any) -> str:
    lines = content.splitlines()
    property_index = None
    pattern = re.compile(rf"^(\s*){re.escape(key)}\s*:")
    for index, line in enumerate(lines):
        if pattern.search(line):
            property_index = index
            break

    replacement = tailwind_property_lines(key, values, 6)
    if property_index is not None:
        end = find_js_property_end(lines, property_index)
        return "\n".join([*lines[:property_index], *replacement, *lines[end:]]) + "\n"

    extend_index = None
    for index, line in enumerate(lines):
        if re.match(r"^\s*extend\s*:\s*\{", line):
            extend_index = index
            break
    if extend_index is None:
        raise ExtractionError("tailwind.config.js does not contain theme.extend")

    insert_index = extend_index + 1
    return "\n".join([*lines[:insert_index], *replacement, *lines[insert_index:]]) + "\n"


def find_js_property_end(lines: list[str], start: int) -> int:
    balance = 0
    saw_brace = False
    for index in range(start, len(lines)):
        line = lines[index]
        balance += line.count("{") - line.count("}")
        saw_brace = saw_brace or "{" in line
        if saw_brace and balance <= 0 and line.rstrip().endswith(","):
            return index + 1
        if not saw_brace:
            return index + 1
    return start + 1


def tailwind_property_lines(key: str, values: Any, indent: int) -> list[str]:
    rendered = json.dumps(values, indent=2, sort_keys=True)
    rendered_lines = rendered.splitlines()
    spaces = " " * indent
    if len(rendered_lines) == 1:
        return [f"{spaces}{key}: {rendered_lines[0]},"]
    first = f"{spaces}{key}: {rendered_lines[0]}"
    middle = [" " * indent + line for line in rendered_lines[1:-1]]
    last = " " * indent + rendered_lines[-1] + ","
    return [first, *middle, last]


def build_plan(repo_root: Path, design_system: str, examples: list[str]) -> dict[str, Any]:
    context, errors, conflicts = collect_plan_data(repo_root, design_system, examples)
    design_system_dir = context["design_system_dir"]
    example_dirs = context["example_dirs"]

    artifacts = [
        {
            "path": repo_relative(design_system_dir / artifact, repo_root),
            "sha256": sha256_file(design_system_dir / artifact),
        }
        for artifact in CANONICAL_ARTIFACTS
        if (design_system_dir / artifact).is_file()
    ]
    extraction_inputs = [
        {
            "path": repo_relative(example_dir / "extraction.json", repo_root),
            "sha256": sha256_file(example_dir / "extraction.json"),
        }
        for example_dir in example_dirs
    ]

    planned_writes: list[dict[str, Any]] = []
    if not errors and not conflicts:
        planned_writes = build_planned_writes(repo_root, design_system_dir, context["merged_updates"])

    return {
        "schema": "design-example-apply-plan.v1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "repo_root": str(repo_root),
        "design_system_path": repo_relative(design_system_dir, repo_root),
        "ready": not errors and not conflicts,
        "errors": errors,
        "conflicts": conflicts,
        "canonical_artifacts": artifacts,
        "extraction_inputs": extraction_inputs,
        "accepted_scopes": context["accepted_records"],
        "rejected_scopes": context["rejected_records"],
        "planned_writes": planned_writes,
    }


def validate_plan_fresh(repo_root: Path, plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for group in ("canonical_artifacts", "extraction_inputs"):
        for entry in plan.get(group, []):
            path = repo_root / entry["path"]
            if not path.is_file():
                errors.append(f"stale plan: missing {entry['path']}")
                continue
            current_hash = sha256_file(path)
            if current_hash != entry["sha256"]:
                errors.append(f"stale plan: {entry['path']} changed")
    return errors


def update_metadata(repo_root: Path, plan: dict[str, Any], plan_path: Path) -> None:
    accepted_by_example: dict[str, list[str]] = {}
    for record in plan.get("accepted_scopes", []):
        accepted_by_example.setdefault(record["example"], []).append(record["scope"])

    rejected_by_example = {
        record["example"]: record.get("scopes", [])
        for record in plan.get("rejected_scopes", [])
    }

    for example, accepted in accepted_by_example.items():
        metadata_path = repo_root / example / "metadata.json"
        if not metadata_path.is_file():
            continue
        metadata = read_json(metadata_path)
        metadata["status"] = "applied"
        metadata["accepted_scopes"] = accepted
        metadata["rejected_scopes"] = rejected_by_example.get(example, [])
        metadata["applied_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        metadata["apply_plan_path"] = repo_relative(plan_path, repo_root)
        write_json(metadata_path, metadata)


def update_extraction_status(repo_root: Path, plan: dict[str, Any], plan_path: Path) -> None:
    accepted_by_example: dict[str, list[str]] = {}
    for record in plan.get("accepted_scopes", []):
        accepted_by_example.setdefault(record["example"], []).append(record["scope"])

    rejected_by_example = {
        record["example"]: record.get("scopes", [])
        for record in plan.get("rejected_scopes", [])
    }

    for example, accepted in accepted_by_example.items():
        extraction_path = repo_root / example / "extraction.json"
        if not extraction_path.is_file():
            continue
        extraction = read_json(extraction_path)
        extraction["status"] = "applied"
        extraction["accepted_scopes"] = accepted
        extraction["rejected_scopes"] = rejected_by_example.get(example, [])
        extraction["applied_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        extraction["apply_plan_path"] = repo_relative(plan_path, repo_root)
        write_json(extraction_path, extraction)


def update_analysis_status(repo_root: Path, plan: dict[str, Any], plan_path: Path) -> None:
    accepted_by_example: dict[str, list[str]] = {}
    for record in plan.get("accepted_scopes", []):
        accepted_by_example.setdefault(record["example"], []).append(record["scope"])

    rejected_by_example = {
        record["example"]: record.get("scopes", [])
        for record in plan.get("rejected_scopes", [])
    }

    for example, accepted in accepted_by_example.items():
        analysis_path = repo_root / example / "analysis.md"
        if not analysis_path.is_file():
            continue
        content = analysis_path.read_text(encoding="utf-8")
        block = "\n".join(
            [
                STATUS_BLOCK_START,
                "## Applied Design Example Status",
                "",
                "- Status: applied",
                f"- Accepted scopes: {', '.join(accepted) if accepted else 'none'}",
                f"- Rejected scopes: {', '.join(rejected_by_example.get(example, [])) or 'none'}",
                f"- Plan: `{repo_relative(plan_path, repo_root)}`",
                "- Verification: passed",
                STATUS_BLOCK_END,
                "",
            ],
        )
        content = replace_status_block(content, block)
        analysis_path.write_text(content, encoding="utf-8")


def replace_status_block(content: str, block: str) -> str:
    pattern = re.compile(
        re.escape(STATUS_BLOCK_START) + r"[\s\S]*?" + re.escape(STATUS_BLOCK_END) + r"\n?",
    )
    if pattern.search(content):
        return pattern.sub(block, content)
    return content.rstrip() + "\n\n" + block


def apply_plan(repo_root: Path, plan_path: Path) -> dict[str, Any]:
    plan = read_json(plan_path)
    if plan.get("schema") != "design-example-apply-plan.v1":
        raise ExtractionError("plan file has unsupported schema")
    if not plan.get("ready"):
        raise ExtractionError("plan is not ready; resolve errors or conflicts first")

    stale_errors = validate_plan_fresh(repo_root, plan)
    if stale_errors:
        return {
            "schema": "design-example-apply-result.v1",
            "applied": False,
            "errors": stale_errors,
            "verification": [],
        }

    for write in plan.get("planned_writes", []):
        path = repo_root / write["path"]
        path.write_text(write["content"], encoding="utf-8")

    update_metadata(repo_root, plan, plan_path)
    update_extraction_status(repo_root, plan, plan_path)
    update_analysis_status(repo_root, plan, plan_path)

    verification = []
    for write in plan.get("planned_writes", []):
        path = repo_root / write["path"]
        verification.append(
            {
                "path": write["path"],
                "expected_sha256": write["after_sha256"],
                "actual_sha256": sha256_file(path),
                "passed": sha256_file(path) == write["after_sha256"],
            },
        )

    return {
        "schema": "design-example-apply-result.v1",
        "applied": all(item["passed"] for item in verification),
        "errors": [],
        "verification": verification,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan or apply accepted Design Example extraction updates.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    plan = subcommands.add_parser("plan", help="Plan accepted extraction updates.")
    plan.add_argument("--repo-root", default=".", help="Repository root. Defaults to cwd.")
    plan.add_argument("--design-system", required=True, help="Selected Design System name or slug.")
    plan.add_argument(
        "--example",
        action="append",
        required=True,
        help="Example folder or extraction.json path. May be passed more than once.",
    )
    plan.add_argument("--output", help="Write the plan JSON to this path.")

    apply = subcommands.add_parser("apply", help="Apply a previously generated plan.")
    apply.add_argument("--repo-root", default=".", help="Repository root. Defaults to cwd.")
    apply.add_argument("--plan-file", required=True, help="Plan JSON produced by the plan command.")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = Path(args.repo_root).resolve()
        if args.command == "plan":
            plan = build_plan(repo_root, args.design_system, args.example)
            if args.output:
                output_path = Path(args.output)
                if not output_path.is_absolute():
                    output_path = repo_root / output_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                write_json(output_path, plan)
                plan["plan_path"] = repo_relative(output_path, repo_root)
            print(json.dumps(plan, indent=2, sort_keys=True))
            return 0 if plan["ready"] else 2

        plan_path = Path(args.plan_file)
        if not plan_path.is_absolute():
            plan_path = repo_root / plan_path
        result = apply_plan(repo_root, plan_path)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["applied"] else 2
    except ExtractionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
