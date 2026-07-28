---
name: add-design-template
description: Create or update HTML templates inside a chosen `.design` Design System using that system's `DESIGN.md` as the visual authority. Use when the user asks to add a design template, create reusable HTML for a card, email, section, page, component, or similar artifact, or wants an interview-driven template workflow that follows Design Workspace guidance and records settled decisions with grill-with-docs.
disable-model-invocation: true
---

# Add Design Template

Create a reusable `.html` template inside a user-selected Design System. The template must be guided by that Design System's `DESIGN.md`, not by invented visual choices.

## Startup

1. Use `$query` first for relevant project context, prior decisions, constraints, and open questions.
2. Use `$design-workspace` to locate `.design`, read `.design/AGENTS.md`, and inspect `.design/design-system/`.
3. If the user has not named a Design System:
   - If exactly one Design System exists, use it and say so.
   - If multiple Design Systems exist, ask which one to use.
   - If none exist, stop and ask the user to create or name a Design System; do not invent one.
4. Read the selected Design System's `README.md`, `DESIGN.md`, and supporting token files when present.
5. Use `$grill-with-docs` to interview the user before writing the template unless the request already supplies a complete brief. Ask one question at a time.

## Interview

Resolve only the decisions that cannot be discovered from project files. Recommended order:

1. Template kind: card, email, dashboard panel, landing section, form, page, component, or another specific artifact.
2. Template purpose and audience.
3. Output name and slug. Default to a concise kebab-case slug based on the template kind.
4. Target medium constraints: browser, email client compatibility, print, fixed size, responsive breakpoints, dark mode, or accessibility requirements.
5. Required content slots, sample content, empty states, and variants.
6. Interaction requirements, if any. Static HTML is the default; add JavaScript only when the template genuinely requires interaction.

When terminology is settled or an architectural decision is worth keeping, follow `$grill-with-docs` behavior: update `CONTEXT.md` for glossary terms and create ADRs only for hard-to-reverse, surprising trade-offs.

## Output Location

Write templates under the selected Design System:

```text
.design/design-system/<design-system-slug>/templates/<template-slug>.html
```

Create the `templates/` folder if it does not exist. Do not overwrite an existing template unless the user explicitly asks; otherwise choose a new slug or ask.

## Template Rules

- Use `DESIGN.md` as the source of truth for colors, typography, spacing, shape, component styling, and do's/don'ts.
- Prefer token-aligned CSS custom properties in a `<style>` block for browser templates.
- For email templates, prefer standalone HTML with conservative markup and inline-compatible styles; avoid scripts and layout techniques with poor email-client support.
- Keep the artifact usable as a template: use semantic placeholder content, clear replaceable regions, and no explanatory tutorial copy unless the user asked for it.
- Preserve the Design System's vocabulary and visual rules. If `DESIGN.md` is incomplete, ask for the missing design decision instead of inventing a style.
- Keep the HTML self-contained unless the Design System explicitly requires external assets or fonts.
- Meet basic accessibility expectations: meaningful document title, language attribute, readable contrast, visible focus states for interactive elements, labels for form controls, and useful alt text when images are included.

## Validation

Before finishing:

1. Check that the template file exists in the selected Design System's `templates/` folder.
2. Search the new file for unresolved placeholders such as `TODO`, `FIXME`, or `[placeholder]`; remove or intentionally replace them.
3. Render or inspect the HTML when browser tooling is available. Verify that the layout is nonblank, text is readable, and key regions do not overlap.
4. If the template is for email, sanity-check that it does not rely on JavaScript or external CSS.

## Completion

Report:

- The selected Design System and template path.
- The important interview decisions captured.
- Which `.design` files were read or changed.
- Whether `.brain`, `CONTEXT.md`, or ADR files changed.
- Validation performed and any remaining open questions.
