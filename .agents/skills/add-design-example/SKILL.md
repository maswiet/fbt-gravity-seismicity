---
name: add-design-example
description: Add one or more user-provided visual examples to an existing AFK Research Design System. Use when the user provides PNG, JPG/JPEG, WebP, SVG, PDF, URL, screenshot, attachment, or other visual reference input and asks to update, align, teach, refine, or make a selected `.design/design-system` entry follow that example.
disable-model-invocation: true
---

# Add Design Example

Use this skill to preserve visual reference evidence under a selected Design System, analyze it, ask for acceptance, and update Design Workspace artifacts. The workflow is scoped to `.design`; do not modify product UI source code.

## Startup

1. Invoke `design-workspace` first. Read `.design/AGENTS.md`, inspect `.design/design-system/`, and follow the Design Workspace rules.
2. Require exactly one selected Design System before analysis. If `.design/` or the selected Design System is missing, stop and tell the user to create or select one first.
3. Gather the Design Example inputs:
   - selected Design System name or slug
   - one or more visual sources: PNG, JPG/JPEG, WebP, SVG, PDF, or URL
   - a short Design Example Intent for each source
4. Ask a focused follow-up for any missing required input.

## Preserve Evidence

For each Design Example, create a separate provenance folder under:

```text
.design/design-system/<design-system-slug>/examples/YYYY-MM-DD-<example-intent-slug>/
```

Use `scripts/prepare_design_example.py` for deterministic setup:

```bash
python3 .agents/skills/add-design-example/scripts/prepare_design_example.py \
  --repo-root . \
  --design-system "<name-or-slug>" \
  --intent "<short intent>" \
  --source-file path/to/reference.png
```

For URL examples, capture the accessible rendered page first when possible, then pass both the URL and capture:

```bash
python3 .agents/skills/add-design-example/scripts/prepare_design_example.py \
  --repo-root . \
  --design-system "<name-or-slug>" \
  --intent "<short intent>" \
  --source-url "https://example.com/page" \
  --capture-file path/to/capture.png
```

The helper creates `metadata.json`, `extraction.json`, `analysis.md`, and copied source/capture artifacts. Reject unsupported file types unless they can be safely converted into a preserved visual artifact.

## Analyze

Read `references/extraction-rubric.md` before visual analysis. Verify the preserved artifact or rendered capture is readable before deriving changes from it.

Separate findings into:

- observed values directly visible in the example
- inferred guidance with confidence
- unknowns that need user judgment
- conflicts with existing Design System guidance

For multiple examples, analyze and present each one separately. Do not merge evidence from different examples before acceptance.

## Propose And Accept

Present proposed Design System changes grouped by area:

- README orientation
- colors
- typography
- layout and spacing
- elevation and depth
- shapes
- components
- `design_tokens.json`
- `tailwind.config.js`

Ask the user to accept all changes or selected design-area scopes for each example. Partial acceptance is allowed. Record proposed, accepted, and rejected scopes in that example's `extraction.json`; keep `analysis.md` human-readable.

## Apply

After acceptance, update only Design Workspace artifacts for the selected Design System by using `scripts/apply_design_example_extraction.py`.

Plan first:

```bash
python3 .agents/skills/add-design-example/scripts/apply_design_example_extraction.py \
  plan \
  --repo-root . \
  --design-system "<name-or-slug>" \
  --example ".design/design-system/<slug>/examples/<example-id>" \
  --output ".design/design-system/<slug>/examples/<example-id>/apply-plan.json"
```

For multiple accepted examples, pass `--example` once per example so conflicts are detected before writes.

Apply only after reviewing a ready plan:

```bash
python3 .agents/skills/add-design-example/scripts/apply_design_example_extraction.py \
  apply \
  --repo-root . \
  --plan-file ".design/design-system/<slug>/examples/<example-id>/apply-plan.json"
```

The helper updates:

- `README.md`
- `DESIGN.md`
- `design_tokens.json`
- `tailwind.config.js`
- each example's `extraction.json`, `analysis.md`, and `metadata.json`

The accepted Design Example extraction drives all canonical Design System artifacts together. Keep existing `DESIGN.md` guidance for unrelated or ambiguous areas; update the design areas clearly evidenced by the accepted example. The helper rejects stale plans when canonical artifacts or `extraction.json` inputs changed after planning.

After applying multiple accepted examples, use the helper's verification summary as the final consistency pass across the selected Design System artifacts.

## Completion

Report:

- selected Design System
- example folders created
- accepted and rejected scopes
- Design Workspace files changed
- visual verification performed

Do not automatically commit or push `.design` changes. Do not duplicate Design Example provenance into `.brain`.
