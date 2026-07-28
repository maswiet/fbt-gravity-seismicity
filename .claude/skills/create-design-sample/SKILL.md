---
name: create-design-sample
description: Create self-contained Design Samples that demonstrate a selected `.design` Design System through artifacts such as static landing pages, app mockups, slide decks, PDFs, documents, or images. Use when the user asks to create, generate, build, preview, or compare a design sample, style sample, landing page, sample deck, or other artifact that shows the reproducible look of a Design System without changing product code by default.
disable-model-invocation: true
---

# Create Design Sample

## Core Rule

Create a Design Sample as a self-contained folder under one Design System:

`.design/design-system/<design-system-slug>/outputs/<sample-slug>/`

Invoke the `design-workspace` skill first. If `.agents/skills/design-workspace/SKILL.md` exists, read it and apply it before creating the sample. Keep the work scoped to `.design` unless the artifact explicitly requires repository-level implementation or verification.

## Workflow

1. **Enter the Design Workspace**
   - Apply `design-workspace` startup rules.
   - If `.design` does not exist, stop and tell the user to initialize a Design Workspace or add a Design System first.
   - Inspect `.design/design-system/`.

2. **Select the Design System**
   - If the user named a Design System, use that Design System.
   - If exactly one Design System exists, use it.
   - If zero or multiple Design Systems exist and the user did not name one, ask which Design System to use.
   - Read the selected Design System's `README.md` and `DESIGN.md` before producing any artifact.

3. **Reject unfinished Design Systems**
   - Stop if `DESIGN.md` still contains scaffold TODOs or empty core token maps such as `colors: {}`, `typography: {}`, `rounded: {}`, or `spacing: {}`.
   - Do not invent visual direction, token values, palettes, typography, spacing, or component styling to fill gaps.

4. **Prepare the sample folder**
   - Use `scripts/prepare_design_sample.py` to create a collision-safe folder and seed `README.md`.
   - Prefer the project-local script path:

     ```sh
     python3 .agents/skills/create-design-sample/scripts/prepare_design_sample.py \
       --design-system-dir ".design/design-system/<design-system-slug>" \
       --sample-name "<short sample name>" \
       --request "<original user request>"
     ```

   - If the base sample slug already exists, the script creates a timestamped sibling. Do not overwrite an existing Design Sample unless the user explicitly asks for replacement.

5. **Create the requested artifact**
   - Support any artifact type Codex can reasonably create: static pages, app mockups, presentations, PDFs, documents, images, diagrams, or other visual examples.
   - For web/UI samples, default to a standalone static artifact inside the sample folder, such as `index.html` plus local assets. Do not modify the target app's real source code unless the user explicitly asks.
   - Delegate medium-specific work to the relevant existing skill or tool when available, such as presentations for `.pptx`, documents for `.docx`, pdf for PDFs, imagegen for generated bitmap images, or browser tooling for HTML verification.
   - Apply the selected Design System's tokens and prose guidance. Preserve the system as the source of truth; the sample is evidence of application, not a new design authority.

6. **Verify the visual result**
   - For visual artifacts, render or preview the output whenever practical.
   - For HTML, use a browser screenshot or equivalent visual check.
   - For PDFs, documents, and slides, render preview images when the available toolchain supports it.
   - Put preview artifacts in the sample folder when useful, for example `preview.png`.
   - If verification cannot be performed, record the gap in the sample `README.md`.

7. **Finish the sample manifest**
   - Update the sample `README.md` with:
     - the original user request
     - selected Design System name and path
     - generated files
     - open/run instructions
     - verification performed
     - gaps, assumptions, or unavailable checks

## Completion

Report the Design System used, the Design Sample folder path, key generated files, verification performed, and any gaps. Also report which `.design` files were read or changed, and whether work expanded outside `.design`.
