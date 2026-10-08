# Diagram and image production

## Choose the visual model

| Question | Useful model |
|---|---|
| What happens next? | Numbered flow or sequence |
| What causes what? | Directed causal graph with qualified edges |
| What belongs inside what? | Nested groups or hierarchy |
| What changes? | Before/after panels or timeline |
| How do options differ? | Aligned comparison or common-scale chart |
| How does a system connect? | Nodes, boundaries, labeled paths |

Choose one main question. A diagram that tries to answer all of them becomes a poster, not an explanation.

## Meaning before geometry

List entities, states, relationships, units, and exceptions before positioning shapes. Give each arrow one clear meaning: flow, dependency, causation, or sequence. Use a legend if meanings differ. Do not imply causation when evidence shows only association. Do not imply scale, duration, or probability through shape size unless that encoding is intentional and labeled.

Example: cache hit/miss needs one request, a cache lookup, two explicit branches, and the origin on the miss branch. A miss returning from origin may populate the cache if the stated policy permits it. Two labeled paths teach more than generic server icons.

## Build exact visuals

Use inline SVG/HTML for technical labels, charts, and relationships. Define a consistent grid and text sizes. Route connectors away from labels. Attach endpoints to actual boundaries. Keep arrowheads visible. Provide `title` and `desc` or equivalent nearby prose.

Use generated raster images for illustration, not as the authority for exact facts. Prefer Replicate GPT Image 2 where the host has approved access. Inspect current schemas instead of guessing model identifiers. Generate a text-free base if labels or figures must be exact, then overlay them deterministically. Keep evidence and analogy visually distinct. Respect image licensing and do not upload private references without permission.

## Inspect

Render at the final intended dimensions. Inspect the full diagram and zoom into small labels. Check every edge against the relationship list. Check clipping, collisions, arrow endpoints, caption accuracy, and mobile readability. Screenshot after changes: correct source coordinates do not guarantee a correct visual result. If the output is PNG, inspect that PNG, not just the SVG that produced it.
