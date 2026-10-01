# Design for the task

Read the prototype's user, task and constraints before styling it. Keep the client's existing design system and stack. If they supplied a reference, inspect it when tools allow and identify what helps this task: hierarchy, density, typography or interaction. Do not copy an unrelated marketing hero into a working tool.

Choose a visual direction in one sentence. Establish a small set of color, spacing and type choices that support it. Give the primary action emphasis and make secondary actions subordinate. Use meaningful labels and realistic synthetic content, not placeholder slogans. Remove decoration and containers that do not help a user understand or act.

## Typography and fonts

Use one or two font families with explicit roles and a readable size and line height. When the client wants Google Fonts, choose families suited to the content and verify the actual family names, required weights and license from the supplied source or official provider. Load only the weights used, with `display=swap` and metric-compatible local fallbacks where practical. Test the fallback when fonts fail to load. Avoid downloading or adding a font package unless the environment needs it; never require a font account, framework or global install. Follow an existing self-hosting or content-security-policy requirement.

## States and accessibility

Design the task's initial, loading, empty, success and error states, plus disabled controls when the task needs them. Keep errors beside their inputs and offer recovery. Label live, local and simulated behavior. Use semantic controls, visible keyboard focus and accessible labels. Check contrast against the actual background; do not rely on color alone. Keep touch targets usable and allow text enlargement. Respect reduced motion and avoid animating reading text.

## Rendered review

Inspect the actual flow at mobile and desktop sizes, with long content, keyboard input and font fallback. Check clipping, horizontal overflow, hierarchy and whether a user can finish the task. Use build-loop guide for repeated build/render/critic/repair checks against the fixed BAR. Inspect after each material UI change, then compare current and reference or previous captures with matched viewport, pose, state and content under neutral A/B labels when possible. Keep builder history from an authorized independent critic. Inspect motion through video or interaction. Label self-review and missing comparison or execution tools. Source inspection alone does not establish visual acceptance.

With conversation-only tools, return screen descriptions, type/color choices and state specifications the next team can implement. Do not claim screenshots, contrast measurements or browser checks you did not perform. Finish with the visual decisions, checks performed and the largest remaining design gap.
