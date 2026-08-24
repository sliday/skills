#### Borrowed craft catalog

Mined from local source skills: emil-design-eng, make-interfaces-feel-better, better-frontend, apple-design, frontend-design, 12-principles-of-animation. Deduped against ux-ui-ia SKILL.md v1.1.1 (8px grid + scale, atomic layers, two-tier tokens, contrast floors 4.5:1 and 3:1, UX-law tables, 24/44px targets, type set 12/14/16/20/24/32, google-fonts routing all omitted here). Each rule stands alone.

#### Aesthetic direction

- Name subject, audience, and the page's single job before styling. Derive palette, type, layout from the subject's own world: materials, instruments, vernacular. (frontend-design)
- Kill the three generic-AI looks: cream near #F4F1EA + high-contrast serif + terracotta accent; near-black + single acid-green or vermilion accent; broadsheet hairlines + zero radius + dense columns. Use one only when the brief asks for it. (frontend-design)
- No purple-on-white defaults. No dark-mode bias unless requested. (better-frontend)
- Plan in a compact token brief first: 4-6 named hex values, 2+ type roles (characterful display used with restraint, complementary body, optional utility face), one layout concept, one signature element. (frontend-design)
- Spend boldness in one place. One signature element per page; keep everything around it quiet. Before shipping, remove one accessory. (frontend-design)
- Review the plan against the brief: if any part matches what you would produce for any similar prompt, revise it and state why. (frontend-design)
- Two typefaces maximum. Never default to Inter, Roboto, Arial, or system-ui stacks unless the design system requires them. (better-frontend)
- Do not introduce a paid typeface to satisfy a polish checklist; polish details never override the project's chosen font family. (make-interfaces-feel-better)
- Typography carries the personality; make the type treatment memorable, not a neutral delivery vehicle. (frontend-design)
- No flat single-color backgrounds; build atmosphere with gradients, imagery, subtle pattern, or layered surfaces. (better-frontend)
- Structure encodes meaning: numbering, eyebrows, dividers, labels only when they state something true. 01/02/03 markers only for real sequences. (frontend-design)
- Match complexity to vision: maximalist direction needs elaborate execution, minimal direction needs precision in spacing, type, detail. (frontend-design)

#### Composition and heroes

- One composition per viewport; the first viewport reads as one unified idea, not a cluttered dashboard. (better-frontend)
- Hero budget: brand, one headline, one short supporting sentence, one CTA group, one dominant image. No stats, schedules, promos, metadata rows. (better-frontend)
- Hero is a thesis: open with the most characteristic thing in the subject's world (headline, image, animation, live demo). Big number + small label + gradient accent is the template answer. (frontend-design)
- Brand test: remove the nav; if the first viewport could belong to another brand, branding is too weak. Brand is a hero-level signal, not nav text. (better-frontend)
- Full-bleed hero only on landing pages: edge-to-edge visual plane. No inset heroes, rounded media cards, tiled collages, floating image blocks. (better-frontend)
- No hero overlays: no detached labels, floating badges, promo stickers, info chips on hero media. (better-frontend)
- One job per section: one purpose, one headline, usually one supporting sentence. (better-frontend)
- Default: no cards. Cards only when they contain interaction. Card test: remove border, shadow, background, radius; if nothing is lost, it is not a card. (better-frontend)
- No icon rows or feature grids as first content after the hero; no pill clusters or stat strips. (better-frontend)
- Marketing narrative order: hero, supporting imagery, product detail, social proof, final CTA. (better-frontend)
- Ground in real content, never lorem ipsum; constraints first: one H1, max six sections, one accent color, one primary CTA above the fold. Verify at 375px and 1440px minimum. (better-frontend)

#### Typography rendering

- `text-wrap: balance` on headings; the algorithm only runs on blocks of 6 lines or fewer (Chromium) / 10 (Firefox). (make-interfaces-feel-better)
- `text-wrap: pretty` on short-to-medium body, captions, list items; neither property on 10+ line text. (make-interfaces-feel-better)
- `font-variant-numeric: tabular-nums` on any updating number: counters, timers, prices, table columns, scoreboards. Not on phone numbers, zips, version strings. Inter widens and centers the digit 1 under tabular-nums; verify. (make-interfaces-feel-better)
- `-webkit-font-smoothing: antialiased` + `-moz-osx-font-smoothing: grayscale` once at the root; per-element application creates inconsistent weight. macOS only, safe everywhere. (make-interfaces-feel-better)
- Tracking is size-specific, never one value: negative on large display (about -0.02em), near 0 on body, slightly positive on small text. (apple-design)
- Leading tracks size inversely: tight on large headings, looser on body; increase for tall-ascender scripts, tighten for dense data UI. (apple-design)
- Build hierarchy from weight + size + leading as a set; emphasize with weight, it adds presence without space. (apple-design)
- Respect user text-size settings: spacing in rem/em so layout scales with the text. (apple-design)

#### Surfaces and depth

- Concentric radius: outerRadius = innerRadius + padding. When padding exceeds 24px, treat layers as separate surfaces and pick radii independently. (make-interfaces-feel-better)
- Shadows over borders for depth. Light-mode 3-layer token: `0 0 0 1px rgba(0,0,0,.06), 0 1px 2px -1px rgba(0,0,0,.06), 0 2px 4px 0 rgba(0,0,0,.04)`; hover raises alphas to .08/.08/.06. Dark mode: single ring `0 0 0 1px rgba(255,255,255,.08)`, hover `.13`. (make-interfaces-feel-better)
- Keep real borders for dividers, table cells, form input outlines; the shadow swap is for elevation only. (make-interfaces-feel-better)
- One box-shadow depth per section. (better-frontend)
- Image outlines: `1px` at `rgba(0,0,0,0.1)` light / `rgba(255,255,255,0.1)` dark, `outline-offset: -1px`. Pure black/white only; tinted neutrals (slate, zinc, #0a0a0a) read as dirt on the edge. Never the accent color. (make-interfaces-feel-better)
- Translucent chrome: `backdrop-filter: blur(20px) saturate(180%)` + semi-transparent background; content scrolls under nav and toolbars. (apple-design)
- Material weight encodes hierarchy: heavier materials for structural regions, lighter for interactive elements. Never stack two light translucent surfaces; legibility collapses. (apple-design)
- Bigger surfaces read thicker: stronger blur, deeper shadow than small chips. Context-aware shadow: heavier over busy content, lighter over plain. (apple-design)
- Scroll-edge fade instead of a 1px border under sticky headers; fade a small blur/gradient mask only where floating chrome overlaps content. (apple-design)
- Dim to focus: modal tasks get a dimming scrim (about black at alpha 0.4); parallel non-blocking panels get translucency + offset without a scrim. Stacked sheets progressively dim and push back parents. (apple-design, 12-principles-of-animation)
- Vibrancy over blur: no flat gray text on translucent surfaces; raise contrast, weight, and letter-spacing slightly. Put color on solid layers. (apple-design)
- Materialize glass surfaces: animate blur radius and scale together on enter/exit, not a plain opacity fade. (apple-design)

#### Optical alignment

- Optical over geometric. When centered math looks off, trust the eye and adjust. (make-interfaces-feel-better)
- Icon-side padding = text-side padding minus 2px on buttons with trailing icons (e.g. pl 16px / pr 14px). (make-interfaces-feel-better)
- Play triangles: shift about 2px right; geometric center is not visual center. (make-interfaces-feel-better)
- Asymmetric icons (stars, arrows, carets): fix in the SVG viewBox/path itself; margin nudges are the fallback. (make-interfaces-feel-better)

#### Interaction feel

- Respond on pointer-down, not release. Highlight the instant of press; feedback continuous during the interaction, never only at the end. (apple-design)
- Scale on press: `scale(0.96)` on `:active` with a 150ms ease-out transition; emil range 0.95-0.98; never below 0.95. Provide a `static` escape hatch to disable. (make-interfaces-feel-better, emil-design-eng)
- Gate hover effects behind `@media (hover: hover) and (pointer: fine)`; touch devices fire hover on tap. (emil-design-eng)
- Extend hit areas with a pseudo-element when the visible control is smaller: 44×44px touch/mobile, at least 40×40px dense desktop. Never let two hit areas overlap. (make-interfaces-feel-better)
- Tooltips: delay the first, then open adjacent tooltips instantly with no animation while one is open. (emil-design-eng)
- Tap gesture: highlight on touch-down, commit on touch-up, about 10px hysteresis, allow cancel-by-drag-away and back. (apple-design)
- Audit every latency on the input path: debounces, artificial timers, transition waits, the ~300ms tap delay. (apple-design)
- Wayfinding: every screen answers where am I, where can I go, what is there, how do I get out. Never trap the user. (apple-design)
- Direct specific labels beat generic ones: "Progress", "Library", not "Home". If a control needs a label to explain its mapping, the mapping is weak. (apple-design)

#### Motion decision and timing

- Frequency gate before animating: 100+ times/day (keyboard shortcuts, command palette) never animate; tens/day remove or drastically reduce; occasional (modals, drawers, toasts) standard; rare/first-time can delight. (emil-design-eng)
- Never animate keyboard-initiated actions. (emil-design-eng)
- Valid purposes only: spatial consistency, state indication, explanation, feedback, preventing jarring changes. "Looks cool" + seen often = no animation. (emil-design-eng)
- Context menus: no entrance animation, exit only. (12-principles-of-animation)
- Durations: press feedback 100-160ms; tooltips and small popovers 125-200ms; dropdowns and selects 150-250ms; modals and drawers 200-500ms; marketing can run longer. UI ceiling 300ms. (emil-design-eng, 12-principles-of-animation)
- Exits shorter and softer than enters (150ms vs 300ms); small fixed translateY (about -12px), not full container height; keep directional movement so context survives. (make-interfaces-feel-better)
- Similar elements use identical timing values; timing drift between button variants is a defect. (12-principles-of-animation)
- Asymmetric intent timing: slow where the user decides (hold-to-delete 2s linear), fast where the system responds (release 200ms ease-out). (emil-design-eng)
- Perceived performance: a fast spinner makes identical load time feel faster; a 180ms select feels more responsive than 400ms. (emil-design-eng)

#### Easing

- Enter: ease-out. Exit: ease-in. On-screen move/morph: ease-in-out. Hover/color: ease. Constant motion (marquee, progress) only: linear. (emil-design-eng, 12-principles-of-animation)
- Never ease-in on entrances; it delays movement in the exact moment the user watches. (emil-design-eng)
- Built-in CSS easings are too weak; use custom curves: strong ease-out `cubic-bezier(0.23, 1, 0.32, 1)`; strong ease-in-out `cubic-bezier(0.77, 0, 0.175, 1)`; iOS drawer `cubic-bezier(0.32, 0.72, 0, 1)`; icon cross-fade `cubic-bezier(0.2, 0, 0, 1)`. Sources: easing.dev, easings.co. (emil-design-eng, make-interfaces-feel-better)
- Natural decay uses exponential ramps, not linear (audio gain: exponentialRampToValueAtTime(0.001), not linearRampTo 0). (12-principles-of-animation)
- Mirror the easing on reversible transitions (inverse cubic-bezier control points) so outbound matches return. (apple-design)

#### Enter, exit, stagger

- Never enter from `scale(0)`; nothing real appears from nothing. Start `scale(0.95)` (0.9+) with `opacity: 0`. (emil-design-eng)
- Enter recipe: `opacity: 0` + `translateY(8-12px)` + `filter: blur(4px)` resolving to clear. (make-interfaces-feel-better)
- Split and stagger: break content into semantic chunks (title, description, buttons), about 100ms between groups; words in a title about 80ms; list items 30-80ms; 12-principles caps at 50ms/item for dense lists. Stagger is decorative; never block interaction. (make-interfaces-feel-better, emil-design-eng, 12-principles-of-animation)
- One focal point: only one element animates prominently at a time. (12-principles-of-animation)
- Popovers scale from their trigger: `transform-origin: var(--radix-popover-content-transform-origin)` (Radix) or `var(--transform-origin)` (Base UI). Modals are exempt, stay centered. (emil-design-eng)
- Enter and exit along the same path; in-from-right must dismiss to the right. (apple-design)
- Icon swap: scale 0.25 to 1, opacity 0 to 1, blur 4px to 0; spring `{ duration: 0.3, bounce: 0 }` with Motion, or both icons in DOM cross-faded with `cubic-bezier(0.2, 0, 0, 1)` without a library. Bounce always 0 here. (make-interfaces-feel-better)
- `initial={false}` on AnimatePresence so default-state elements skip mount animation; verify intentional entrances still fire. (make-interfaces-feel-better)
- `@starting-style` for CSS-only entry animation; `data-mounted` attribute as the legacy fallback. (emil-design-eng)
- Blur masks imperfect crossfades: `filter: blur(2px)` during the transition bridges the two overlapping states; keep blur under 20px (Safari cost). (emil-design-eng)
- clip-path inset() for reveals, tab highlight transitions (clipped duplicate list), hold-to-delete overlays, comparison sliders; hardware-accelerated, no extra DOM. (emil-design-eng)
- translateY(100%) percentages are relative to the element's own size; prefer them over pixel offsets for drawers and toasts. (emil-design-eng)

#### Springs and gestures

- CSS transitions for interactive state (they retarget mid-flight); keyframes only for one-shot sequences; keyframes on rapidly-triggered elements restart from zero and feel broken. (emil-design-eng, make-interfaces-feel-better)
- Springs for anything a user can touch: interruptible and velocity-aware by default. Apple parameters: damping 1.0 (no bounce) default; damping ~0.8 only when the gesture carried momentum. Shipping values: move/reposition damping 1.0 response 0.4; rotation 0.8/0.4; drawer/sheet 0.8/0.3. Motion mapping: `{ type: "spring", bounce: 0, duration: 0.4 }`. (apple-design, emil-design-eng)
- Bounce subtle when used: 0.1-0.3; springs (not easing) when overshoot-and-settle is wanted. (emil-design-eng, 12-principles-of-animation)
- Always animate from the live presentation value on interrupt; never the logical target; never lock input during a transition. (apple-design)
- Velocity handoff at gesture end: pass release velocity as spring initial velocity; relative form `gestureVelocity / (target - current)`. (apple-design)
- Momentum projection: `project(v, d=0.998) = (v/1000)*d/(1-d)`; snap to the point nearest the projection, not the release point; 0.99 for snappier feel. (apple-design)
- Decide reverse vs commit by velocity sign at release, not position. Decompose 2D motion into independent X and Y springs. (apple-design)
- Momentum dismissal: velocity = |dragDistance| / elapsedTime; dismiss when velocity > ~0.11 regardless of distance. (emil-design-eng)
- Rubber-band boundaries: `rubberband(o, dim, c=0.55) = (o*dim*c)/(dim + c*|o|)`; progressive resistance, never hard stops. (apple-design, emil-design-eng)
- Drag: setPointerCapture, respect grab offset, ~10px movement threshold before committing direction, ignore extra touch points mid-drag, track a short position+timestamp history for velocity. (apple-design, emil-design-eng)
- 1:1 tracking during drag; update UI with the pointer the whole way, never only on completion. (apple-design)
- Hint the direction of the gesture: intermediate frames telegraph the outcome. (apple-design)

#### Performance

- Animate only transform, opacity, filter, clip-path; padding/margin/height/width trigger layout + paint. (emil-design-eng, make-interfaces-feel-better)
- Never `transition: all` (or bare Tailwind `transition`); list exact properties. Tailwind `transition-transform` covers transform, translate, scale, rotate; bracket syntax `transition-[scale,opacity,filter]` for mixes. (emil-design-eng, make-interfaces-feel-better)
- `will-change` only for transform/opacity/filter/clip-path, only after observed first-frame stutter (Safari benefits most); never `will-change: all`; each layer costs memory. (make-interfaces-feel-better)
- Framer Motion `x`/`y`/`scale` shorthands are main-thread rAF, not hardware-accelerated; pass the full `transform` string for GPU. CSS animations stay smooth under main-thread load. WAAPI gives JS control at CSS performance. (emil-design-eng)
- Do not animate inherited CSS variables on a parent during drag (recalcs all children); set transform directly on the element. (emil-design-eng)
- Multimodal feedback: visual, sound, haptic on the same frame; obvious causality; only at meaningful moments (success, error, commit, snap). (apple-design)

#### Reduced motion and motion accessibility

- `prefers-reduced-motion: reduce` means gentler, not zero: keep opacity/color changes that aid comprehension; replace slides, springs, parallax with short cross-fades (about 200ms); drop elastic/overshoot; `transform: none` on sheets. (emil-design-eng, apple-design)
- `prefers-reduced-transparency: reduce`: raise background opacity, drop backdrop blur. `prefers-contrast: more`: near-solid backgrounds with defined contrasting border. (apple-design)
- Avoid full-viewport moving backgrounds, slow loops near 0.2 Hz (one cycle per 5s), abrupt brightness jumps; ease dark/light theme changes; large moving objects go semi-transparent while traveling. (apple-design)
- Keep per-frame positional change below the perception threshold to avoid strobing; subtle motion blur/stretch for very fast motion. (apple-design)

#### Copy in the interface

- Copy is design material. Name things by what users control, not how the system is built (notifications, not webhook config). (frontend-design)
- Active voice, exact action verbs: "Save changes", not "Submit". Same action name through the whole flow: "Publish" button yields "Published" toast. (frontend-design)
- Errors: what went wrong and how to fix it, interface voice, no apologies, never vague. Empty states are invitations to act. (frontend-design)
- Sentence case, plain verbs, no filler; one job per element: a label labels, an example demonstrates. (frontend-design)

#### Process and review

- Review animations the next day with fresh eyes; play in slow motion (2-5x duration or DevTools) and frame-by-frame to catch overlap, wrong transform-origin, desynced properties. (emil-design-eng)
- Prototype interactively; design interaction and visuals together; test touch gestures on real hardware via remote devtools, not only simulators. (apple-design, emil-design-eng)
- Match motion to component personality: playful can bounce, professional dashboards stay crisp and fast; cohesion across easing, duration, visual design, and name. (emil-design-eng)
- Good defaults beat options; handle edge cases invisibly (pause timers when tab hidden, fill hover gaps between stacked items with pseudo-elements). (emil-design-eng)
- Review output as a Before/After/Why markdown table, one row per diff, grouped by principle, citing file and property. (emil-design-eng, make-interfaces-feel-better)
- Watch CSS selector specificity when generating styles; type-based and class-based section selectors cancel each other on paddings/margins. (frontend-design)
- Craft is defensible values: every spacing, timing, alignment number is a deliberate choice you can defend; nothing random. (apple-design)
