# Design Example Extraction Rubric

Use this rubric after the example source has been preserved and visually verified.

## Evidence Levels

- **Observed**: directly visible in the source or capture. Use for concrete colors, visible component treatments, spacing tendencies, density, and shape language.
- **Inferred**: plausible but not directly provable. Use for typography families, token scale names, responsive behavior, interaction states, and design intent.
- **Unknown**: not supported by the example. Keep as an open question rather than encoding it as a token.

Never turn an inference into a normative token without user acceptance.

## Extraction Areas

### README Orientation

Note whether the example changes how the Design System should be introduced, navigated, or described.

### Colors

Capture visible palette roles, semantic use, contrast expectations, and obvious constraints. Prefer exact sampled colors when available; otherwise describe the color and mark it inferred.

### Typography

Record visible hierarchy, relative scale, weight, line height, capitalization, and tracking. Treat exact font family as inferred unless the source itself proves it.

### Layout And Spacing

Describe density, grid behavior, rhythm, alignment, page/container width, responsive clues, and repeated spacing patterns.

### Elevation And Depth

Capture shadows, overlays, borders, layering, translucency, and depth cues. Distinguish component-specific depth from global elevation rules.

### Shapes

Record corner radius, stroke weight, icon style, container shape, and recurring geometric motifs.

### Components

Extract only components evidenced by the example. Include variants, states, and interaction rules only when visible or explicitly provided.

### Tokens And Config

Map accepted observations into `DESIGN.md`, `design_tokens.json`, and `tailwind.config.js` together. Do not let the files diverge from the accepted example extraction.

## Conflict Handling

When the example conflicts with existing guidance, update only the areas clearly related to the accepted extraction. Preserve existing `DESIGN.md` guidance for unrelated or ambiguous areas.

## Proposal Format

Group proposed updates by area and label each item as observed, inferred, or unknown. Include confidence and the provenance folder path for every group.

## extraction.json Format

Write the structured proposal and acceptance state to `extraction.json` in the Design Example folder. Use schema `design-example-extraction.v1`.

Top-level fields:

- `accepted_scopes`: design-area scope ids the user accepted.
- `rejected_scopes`: design-area scope ids the user rejected.
- `scopes`: object keyed by scope id.

Supported scope ids are:

- `readme_orientation`
- `colors`
- `typography`
- `layout_spacing`
- `elevation_depth`
- `shapes`
- `components`

Every accepted scope must carry enough structured data for all affected canonical artifacts. `unknown` evidence can be recorded but must not be accepted. `inferred` evidence can be applied only when the user explicitly accepts that scope.

For token-bearing scopes, include:

- `guidance`: prose for the matching `DESIGN.md` section.
- `tokens.<group>`: token values for `DESIGN.md` frontmatter.
- `design_tokens.<group>`: token values for `design_tokens.json` when they differ from `tokens`.
- `tailwind.theme.extend.<key>`: Tailwind theme values when the scope affects Tailwind config.

For `readme_orientation`, include `readme.description`. Keep README orientation separate from visual token decisions.
