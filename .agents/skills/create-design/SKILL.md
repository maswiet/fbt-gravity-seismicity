---
name: create-design
description: Add a new project Design System by asking for the Design System Name, running the project CLI to create it, then running a grill-with-docs interview to produce a spec-compliant DESIGN.md with YAML design tokens and markdown guidance. Use when the user asks to create a design, new design system, brand/style guide, product visual language, or Design Workspace DESIGN.md before UI implementation.
disable-model-invocation: true
---

# Create Design

## Core Rule

Add a new user-authored Design System, not an invented theme and not an update to an existing one. First obtain the Design System Name, then run the project CLI to create the Design System, then use `/grill-with-docs` as the baseline: run `/grilling` with `/domain-modeling`, ask one question at a time, provide a recommended answer, and write the resolved decisions into the proper design and domain documents as they crystallize.

Load `references/design-md-format.md` before writing or validating any `DESIGN.md`.

## Startup

1. Follow repo instructions first. If the repo requires `/query`, ask the `.brain` wiki for relevant design, domain, and constraint context before planning or editing.
2. Use `/design-workspace` when available to inspect `.design`, `.design/AGENTS.md`, and existing `.design/design-system/` names for collision awareness. Do not ask which existing Design System to use; this skill creates a new one.
3. If the user did not provide a Design System Name, ask for it as the first question. Include a recommended name when the product name is discoverable.
4. Run the project CLI to create the Design System before asking visual-language questions. Prefer `afk-research design add "<Design System Name>"`; use the command's supported path flag, usually `--path <repo>`, when targeting a repo other than the current working directory.
5. If the CLI is unavailable, stop and report the blocker instead of hand-creating `.design` files. If the CLI fails because the derived slug already exists, ask for a different Design System Name or explicit permission to work on the existing Design System.
6. After the CLI succeeds, read the generated Design System files, especially `README.md` and `DESIGN.md`, then continue the interview against that new target.
7. Search the existing product, docs, screenshots, and design files for answers before asking the user anything discoverable.

## Interview Flow

Ask exactly one unresolved decision at a time and wait for the answer. Include your recommended answer in the question.

Resolve decisions in dependency order:

1. Design System Name, unless already provided; create it with the CLI before continuing.
2. Product, audience, brand personality, and desired emotional response.
3. Target `DESIGN.md` location created by the CLI.
4. Accessibility and platform constraints, including minimum contrast expectations.
5. Color palettes and semantic roles.
6. Typography families, levels, weights, line heights, and usage rules.
7. Layout model, spacing scale, breakpoints, density, and responsive behavior.
8. Elevation or flat hierarchy strategy.
9. Shape language and corner-radius scale.
10. Component atoms, variants, states, and token references.
11. Do's and Don'ts that prevent the design from drifting.

For each answer, challenge vague language into canonical terms. Update `CONTEXT.md` immediately for stable domain vocabulary. Offer an ADR only when the decision is hard to reverse, surprising without context, and the result of a real trade-off.

## Writing DESIGN.md

Write the newly created Design System's `DESIGN.md` according to `references/design-md-format.md`.

- Use YAML frontmatter for normative tokens whenever the design has enough specificity: `version`, `name`, optional `description`, `colors`, `typography`, `rounded`, `spacing`, and `components`.
- Treat tokens as normative and prose as guidance. If they conflict, fix the conflict before finishing.
- Use valid CSS color values, preferably `#RRGGBB` unless the user intentionally chooses another CSS-supported format.
- Use valid typography objects: `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, optional `letterSpacing`, `fontFeature`, and `fontVariation`.
- Use valid dimensions for spacing and radius values: `px`, `em`, or `rem`, with unitless values only where the format allows them.
- Use `{path.to.token}` references for component tokens when referencing colors, typography, spacing, or rounded values.
- Keep markdown sections in this order when present: `Overview`, `Colors`, `Typography`, `Layout`, `Elevation & Depth`, `Shapes`, `Components`, `Do's and Don'ts`.
- Preserve unknown user-authored sections and custom tokens. Reject or fix duplicate `##` section headings.
- Do not leave placeholders, TODOs, or unresolved recommendations in the final file.

Only update an existing `DESIGN.md` when the CLI reported that the requested Design System already exists and the user explicitly chose to work on it. Preserve user-authored content unless the user agreed to replace it. Make the smallest edits that encode the resolved decisions.

## Validation

Before reporting completion:

1. Re-read `references/design-md-format.md`.
2. Parse the YAML frontmatter or inspect it carefully for schema mistakes.
3. Check for duplicate parsed section headings and incorrect section order.
4. Check obvious text/background component pairs for WCAG AA contrast when colors are known.
5. Confirm every token referenced by `{...}` exists.
6. Report files changed, validation performed, unresolved design questions, and any `.brain` or domain-doc updates.
