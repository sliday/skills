# HTML production

## Content first

Write the explanation outline before styling. Use a descriptive title, a one-sentence answer, one worked example, the mechanism, and the main limitation. Include the intended task and conditions when they affect interpretation. Keep sources beside relevant claims or in a short linked source list.

## Portable page

Deliver one `.html` file with inline CSS and, only when needed, small vanilla JavaScript. Prefer system fonts, inline SVG, and no build step. No CDN, analytics, remote fonts, or runtime network requests. External source links are fine: they are references, not rendering dependencies. Embed licensed raster assets when practical. If media makes the file too large, deliver a clearly named local bundle with relative paths and test it offline; do not call it a single self-contained file.

Use semantic HTML: `main`, headings in order, real buttons, labeled form controls, and a viewport meta tag. Make all core content available without JavaScript. Native `details` is often enough for optional detail. Use CSS custom properties for a small consistent type, spacing, and color system. The look should support the topic, not become the topic.

## Responsive and accessible

- Use a readable measure, generous line spacing, and visible focus states.
- Target WCAG AA contrast: 4.5:1 for normal text; 3:1 for large text and necessary graphical/control boundaries. Check rather than guess.
- Never make color the only signal. Use labels, line styles, or shape differences.
- Use a responsive SVG `viewBox`; scaling a wide desktop diagram down is not enough if labels become tiny. Recompose it or offer readable numbered panels on narrow screens.
- Provide a diagram caption or equivalent prose. Give informative images useful alternative text; leave decorative image alt text empty.
- Honor `prefers-reduced-motion`. Animation must not be necessary to read the explanation.
- Do not hide essential content behind hover. Make controls usable with touch and keyboard.

## Interaction must teach

Add a control only when it exposes a relationship: a slider changes one variable; a toggle compares two states; a step button reveals the next causal stage. Show units, input limits, the default state, and the result. State model assumptions. Prefer no interaction over fake precision.

For instance, a queue explainer can let readers change arrival rate while keeping service rate fixed. State the queue model and its stability condition. Do not imply that the toy model predicts every real queue.

## Verification

Open the final file using the host's authorized browser. Test at a narrow mobile viewport and a desktop viewport, for example 390 and 1440 CSS pixels wide. Inspect actual screenshots, not just the DOM. Check horizontal overflow, small labels, long headings, source links, keyboard focus, each control, reduced motion, and the static/no-JavaScript state. If served locally for testing, also verify that the delivered file opens offline. Record the tested viewports and controls in the handoff when helpful.
