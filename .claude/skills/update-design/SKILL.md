---
name: update-design
description: Update a project Design System through a focused Design Workspace session and documented grill. Use when the user wants to change, refine, audit, or extend files under `.design/design-system/`, especially when multiple Design Systems may exist and the user must choose which one to update first.
disable-model-invocation: true
---

# Update Design

## Core Rule

Focus all design-system update work through `.design`, require the user to choose the Design System before any update discussion or edits, then run a `/grill-with-docs` session to sharpen the intended change and preserve the resulting decisions.

## Startup

1. Invoke the `/design-workspace` behavior first:
   - Read and apply `.agents/skills/design-workspace/SKILL.md` when it exists.
   - Follow its startup sequence, including root `AGENTS.md`, `.brain/AGENTS.md` when present, `.design/AGENTS.md`, and `.design/design-system/` inspection.
2. If `.design` does not exist, say the project has no initialized Design Workspace and stop unless the user explicitly asks to initialize one.
3. Inspect `.design/design-system/` before asking update questions.

## Design System Selection

- If the user already named a Design System, verify it exists under `.design/design-system/` before continuing.
- If multiple Design Systems exist and the user did not name one, list the available systems and ask which one should be updated first.
- If exactly one Design System exists and the user did not name it, ask the user to confirm that it is the one to update.
- If no Design Systems exist, ask which Design System should be created or used. Do not invent a name, visual direction, tokens, or style language.
- Do not discuss specific design changes, run the grill, or edit files until the target Design System is selected.

## Update Interview

After the target Design System is selected:

1. Read the selected Design System's `README.md` and `DESIGN.md` when present.
2. Invoke the `/grill-with-docs` behavior:
   - Run the `/grilling` session it requires.
   - Use `/domain-modeling` as directed by `/grill-with-docs` to capture ADRs, glossary updates, and domain context.
3. Keep the interview anchored to the selected Design System. Ask what specifically needs to change, why it matters, what files or design surfaces are in scope, and what should remain unchanged.
4. Prefer one sharp question at a time. Stop grilling when the next action is clear enough to produce a focused design-system update or a documented update plan.

## Editing Boundary

- Edit only the selected Design System unless the user explicitly expands scope.
- Treat existing Design System files as user-authored product decisions. Preserve them unless the interview establishes a replacement or refinement.
- When implementation is requested, update the Design System files first, then update product code only when the user explicitly asks to apply the design change.
- Store design decisions and docs according to the `/grill-with-docs` and `/domain-modeling` instructions.

## Completion

Report:

- The selected Design System.
- The `.design` files read and changed.
- The docs or domain artifacts created or updated by the grill session.
- Any unresolved design questions or follow-up implementation work.
