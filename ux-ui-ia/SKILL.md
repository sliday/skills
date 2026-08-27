---
name: ux-ui-ia
version: 1.3.0
description: Use when designing or reviewing interfaces, setting up a spacing scale or design tokens, or restructuring UI into a component system.
author: Sliday
license: MIT
metadata:
  hermes:
    tags: [ux, ui, ia, accessibility, interaction-design, usability, ux-laws]
    related_skills: [agent-visual-verification, google-fonts]
triggers:
  - "design an interface"
  - "review this UI"
  - "improve the UX"
  - "fix the information architecture"
  - "audit this flow"
  - "apply UX laws"
  - "design a form, dashboard, settings page, or onboarding"
  - "make this interface easier to use"
  - "set up a spacing scale or 8px grid"
  - "create design tokens or a component system"
  - "normalize inconsistent spacing, radii, or type sizes"
mutating: false
---

# UX/UI/IA

## When to Use

Use whenever an agent designs, restructures, implements, or reviews an interface: information architecture, navigation, flows, forms, controls, content hierarchy, responsive behavior, accessibility, visual systems, interaction states, or usability.

Use it before aesthetic exploration to establish structure, and again after implementation as a rendered-interface quality gate. Do not use it for pure backend work or as a substitute for user research when the users, domain, or risks are unknown.

## Contract

This skill produces interfaces that are understandable, operable, resilient, and visually coherent. It guarantees that:

- the user, job, product truth, constraints, and success outcome are explicit before styling;
- information architecture and task hierarchy precede component selection;
- the complete flow includes loading, empty, partial, success, error, permission, offline, interruption, and recovery states where relevant;
- UX laws are selected as diagnostic lenses, not treated as universal commandments;
- accessibility, responsive behavior, content stress, and input modes are part of the design—not a cleanup pass;
- recommendations are verified in the rendered interface when implementation access exists;
- the output makes decisions and trade-offs explicit instead of producing generic advice.

## Core principle

Design the shortest honest path from user intent to a recoverable outcome.

“Short” does not mean hiding important context. “Honest” means the interface accurately represents product state, consequences, price, availability, permissions, and uncertainty. “Recoverable” means mistakes, interruptions, and failures do not destroy work or trap the user.

## Mandatory workflow

### 1. Define the real task and product truth

Before drawing or editing screens, state:

- primary user and context;
- job to be done;
- entry point and prior knowledge;
- successful outcome;
- costly or dangerous mistakes;
- product states and unavailable actions;
- device, input, language, accessibility, privacy, and implementation constraints;
- business goal only where it does not conflict with the user's goal.

Resolve contradictions between product behavior and interface promises first. Visual polish cannot rescue a dishonest or impossible flow.

### 2. Build the information architecture

Inventory the objects, attributes, actions, destinations, and lifecycle states the interface must represent. Then:

1. remove content or controls that do not support a real task;
2. use the user's language rather than internal system vocabulary;
3. group by meaning and decision sequence;
4. rank each item as **primary, secondary, tertiary, or metadata**;
5. keep critical context and consequences visible at the decision point;
6. progressively disclose advanced or rare complexity;
7. make navigation location, destination, and escape routes clear;
8. use search, filtering, grouping, or saved views when the information space is genuinely large.

Do not make the site map mirror the org chart or database schema unless users actually think that way.

### 3. Design the flow and state model

Map the smallest complete journey:

```text
entry → orientation → decision → action → feedback → outcome → next step
```

Add relevant non-happy paths:

- loading and slow response;
- zero, one, many, and extreme data;
- partial completion and drafts;
- validation and server errors;
- lost connection and retry;
- expired session or permission changes;
- destructive confirmation and undo/recovery;
- interruption and resumption;
- duplicate submission and idempotency;
- success closure and the next useful action.

Every consequential action must have visible availability, immediate acknowledgment, and a trustworthy final state.

### 4. Select UX laws by the observed problem

Do not decorate a design with law names after the fact. Start with a concrete failure—slow choice, missed target, forgotten context, weak grouping, abandoned flow—and select only the laws that explain it.

#### Decision and memory

| Law or effect | Use when | Design move | Misuse to avoid |
|---|---|---|---|
| **Cognitive Load** | A screen requires excessive reading, remembering, switching, or decoding | Reduce extraneous work, externalize memory, sequence complexity, and keep needed context nearby | “Simplifying” by hiding information needed for a safe decision |
| **Miller's Law / working-memory limits** | Users must remember items across screens or compare many unstructured facts | Chunk meaningfully, label groups, preserve context, and favor recognition over recall | Treating `7 ± 2` as a literal maximum for menu items or form fields; capacity varies and is often lower without rehearsal |
| **Hick's Law** | Decision time grows because choices are numerous or hard to distinguish | Remove irrelevant choices, group by meaningful attributes, recommend when evidence supports it, and add search/filtering for large sets | Hiding legitimate options, splitting one decision into unnecessary steps, or forcing a default that benefits the business over the user |
| **Choice Overload** | Users defer, abandon, or regret a decision because the option set feels unmanageable | Curate, compare on discriminating criteria, stage optional choices, and provide a reversible default | Confusing fewer choices with better choices or reducing user autonomy |
| **Tesler's Law** | A task contains irreducible domain complexity | Let the system absorb parsing, calculation, repetition, and safe defaults; expose complexity only where human judgment is required | Hiding consequences, uncertainty, compliance, or expert controls that the user genuinely needs |

#### Targeting and conventions

| Law or effect | Use when | Design move | Misuse to avoid |
|---|---|---|---|
| **Fitts's Law** | Important controls are slow or error-prone to acquire | Increase target and hit-area size, reduce pointer travel, place actions near the object they affect, and separate dangerous neighbors | Reducing the law to arbitrary list ordering; making a visually large element with a tiny actual hit area |
| **Jakob's Law** | Users hesitate because controls or navigation behave unexpectedly | Reuse platform and domain conventions; preserve keyboard and native-control expectations | Copying bad conventions or rejecting a clearly better pattern merely because it is new |
| **Postel's Law, bounded** | Benign human input arrives in varied formatting | Accept safe variation, normalize explicitly, preview the canonical result, and emit consistent data | Applying permissiveness to authentication, security boundaries, money, dates with ambiguous locale, or external protocols where strict validation is safer |

**Target-size floor:** for web pointer inputs, WCAG 2.2 Level AA defines a 24×24 CSS-pixel minimum or sufficient spacing under its exceptions. Treat this as a floor, not an ergonomic goal. Prefer larger targets for primary actions, touch, motion impairment, destructive choices, and use under pressure.

#### Time, momentum, and interruption

| Law or effect | Use when | Design move | Misuse to avoid |
|---|---|---|---|
| **Doherty Threshold / response-time heuristics** | Delay breaks the sense of direct manipulation or flow | Acknowledge input immediately, preserve input, show useful partial state, and provide honest progress/cancellation for longer work | Fake progress bars, decorative delays, blocking the whole screen, or using one fixed threshold for every context |
| **Goal-Gradient Effect** | A finite multi-step task is abandoned because progress is unclear | Show truthful progress, completed and remaining work, and a stable finish line | Moving the finish line, hiding surprise steps, or manufacturing pressure |
| **Zeigarnik Effect** | Users leave work unfinished or are interrupted | Auto-save when safe, label drafts, preserve position, and make resumption obvious | Guilt, nagging, anxiety loops, or retaining sensitive drafts without consent |
| **Peak-End Rule** | Completion, recovery, or a high-friction moment shapes the remembered experience | Make the hardest moment supported and the ending clear: what happened, what remains, and what to do next | Confetti or delight used to compensate for a broken core flow |

Use the classic response-time bands as design heuristics, not service-level guarantees: around **0.1 s** feels direct, around **1 s** preserves thought flow, and beyond roughly **10 s** users need meaningful progress, interruption, and return support. Measure the real product and users.

#### Order, emphasis, and grouping

| Law or effect | Use when | Design move | Misuse to avoid |
|---|---|---|---|
| **Serial Position Effect** | Important items disappear in a long ordered sequence | Put high-priority or frequently needed items in strong positions and create meaningful sections | Ordering everything for memorability when task sequence, chronology, or alphabetical retrieval matters more |
| **Von Restorff Effect** | One action or status must stand out among similar elements | Create one controlled contrast in shape, weight, position, label, or color plus non-color meaning | Multiple “special” elements, novelty without meaning, or inaccessible color-only emphasis |
| **Law of Proximity** | Relationships are unclear because spacing is uniform | Use tighter spacing within groups and larger spacing between groups | Inferring semantic meaning from proximity alone without labels or structure |
| **Law of Similarity** | Repeated functions look inconsistent or different functions look identical | Make same-function controls consistent and distinct meanings visibly distinct | Making destructive and safe actions look the same; relying on appearance without accessible names |
| **Law of Common Region** | A boundary would clarify a real section or object | Use a container, fieldset, panel, or background only where it communicates membership | Card soup, nested boxes, and borders around every element |
| **Aesthetic-Usability Effect** | Trust and perceived ease suffer from incoherent craft | Use a deliberate type, spacing, color, motion, and component system; remove visual defects | Assuming attractive means usable or letting polish conceal accessibility and behavior failures |

### 5. Define the interface system

Create a constrained system rather than styling each screen independently. Two defaults do most of the work: an **8px spatial grid** and **atomic composition**. If the codebase already has an equivalent system, extend it; never run a second system beside it. Set direction before spending the grid:

#### 5a. Aesthetic direction

- Commit before styling: name the subject, audience, and the page's single job; derive palette, type, and layout from the subject's own world (frontend-design).
- Kill the generic-AI looks: cream near #F4F1EA + serif + terracotta; near-black + lone acid-green/vermilion accent; broadsheet hairlines + zero radius. Use one only when the brief asks (frontend-design).
- No purple-on-white default; no dark-mode bias unless requested; no flat single-color backgrounds, layer gradient/imagery/pattern for atmosphere (better-frontend).
- Plan a token brief first: 4-6 named hex values, 2+ type roles (characterful display used with restraint, complementary body), one layout concept, one signature element. If any part matches what you would make for any similar prompt, revise it (frontend-design).
- Spend boldness in one place: one signature element, everything around it quiet; remove one accessory before shipping (frontend-design).
- Work in grayscale first. Color is the easiest way to fake hierarchy; removing it forces spacing, size, and contrast to carry the structure. Add the palette once the gray version already reads correctly (refactoring-ui).

**Typography-led hierarchy**

- Two typefaces max; never default to Inter/Roboto/Arial/system-ui unless the design system requires them. Type carries the page's personality (better-frontend, frontend-design).
- Build hierarchy from weight + size + leading as a set; emphasize with weight, it adds presence without space (apple-design).
- Tracking is size-specific: about -0.02em on display, near 0 on body, slightly positive on small text; leading inversely with size (apple-design).

#### 5b. Spacing and sizing: the 8px grid

Every padding, margin, gap, and fixed box dimension comes from one scale on an 8px base, with 4px as the half-step for tight pairs (icon-to-label, checkbox-to-text):

```text
4  8  12  16  24  32  48  64  96
```

Define the scale as tokens (`--space-1: 8px` … `--space-12: 96px`, or the framework equivalent) and spend values from tokens, not literals.

Rules that survive real projects:

- **The grid governs boxes, not glyphs.** Apply it to padding, margins, gaps, control heights, and icon sizes. Line-height obeys readability, not the grid: 25.6px or 28px line-height is correct where the grid would force 24px or 32px.
- **The spacing ladder must never invert.** Spacing encodes grouping (Law of Proximity): label-to-control 4–8, siblings inside a group 8–16, between groups 24–32, between page sections 48+. A card whose internal padding (16) exceeds the gap to its neighbor (8) reads as one merged blob.
- **Size controls on the grid.** Control heights 32/40/48; icons 16/20/24; pointer targets at least 24×24 (WCAG 2.2 floor), 44×44 for primary touch actions.
- **Start generous and subtract.** Adding space until a layout stops looking bad lands on the minimum tolerable amount. Starting from too much and trimming lands on the right amount (refactoring-ui).
- **Steps must be far enough apart to choose between.** Adjacent values differ by roughly 25% or more; that is what makes the pick unambiguous. A plain every-4px list gives no basis to decide between 120 and 124. Above 96, continue the ratio rather than the increment: 128, 192, 256, 384 (refactoring-ui).
- **Exceptions are declared, not leaked.** A living system tolerates a few off-scale values (a 12px chip padding, an 80px hero offset) when they are named tokens with a stated reason. Silent literals like 9px, 13px, 17px are defects.
- **Audit mechanically.** Run `scripts/grid-audit.sh`: it flags off-grid px per property (0/1/2 and line-height/letter-spacing exempt; font-size checked against the type set). In rendered review, off-grid values appear as almost-aligned edges: measure, do not eyeball.

#### 5c. Composition: the atomic system

Build in strict layers; each layer consumes only the layer below:

```text
tokens → atoms → molecules → organisms → templates → screens
```

- **Tokens** in two tiers: primitive (`--gray-700`, `--space-2`) and semantic (`--color-text`, `--btn-bg`). Components reference semantic tokens only, so theming and dark mode become token swaps, not rewrites.
- **Build the ramps up front, in HSL.** Two related HSL values look related; two related hex codes do not. Give each hue 8–10 steps (three runs out immediately), name them 100 lightest to 900 darkest, and fix 500 first as a color that works as a button fill, then the ends, then fill the gaps. Start the dark end at a very dark neutral rather than true black. Never derive shades at runtime, which yields dozens of near-identical blues (refactoring-ui).
- **Atoms:** button, input, label, icon, badge, checkbox. An atom never sets its own external margin; the parent owns spacing via gap.
- **Molecules:** form field (label + control + help + error), search bar, setting row, menu item.
- **Organisms:** form, card list, header, settings section.
- **Templates and screens** compose organisms; a new screen that demands a new atom needs a stated reason.

Rules that survive real projects:

- **Tokens are step zero.** Retrofitting tokens onto already-styled screens is the single largest time sink in system work; hardcoded colors and spacing metastasize. Cut tokens before styling the first screen.
- **Rule of three.** Second appearance of a pattern: note it. Third: extract the component. Two "setting rows" with different backgrounds, radii, and padding are one molecule with a bug, not two designs.
- **Variants, not clones.** Same function, one component, differentiated by modifier (`primary/secondary/ghost/destructive`, `sm/md/lg`), never by copy-pasted styles that drift apart.
- **One radius and one elevation per component level.** Pick a small set (4/8/12/full) and map each component class to one value. Mixed radii inside one card stack is the fastest tell of an unsystematic UI.
- **Type scale is semantic and hand-picked.** Roles (display, heading, subheading, body, caption) map to a fixed set: 12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72. Hand-picked beats ratio-derived: modular scales produce fractional pixels that round unevenly, and they run too sparse at interface density and too dense at display sizes (refactoring-ui). Size the scale in px or rem, never em, since nested em values compound off the scale. The type scale and the spacing scale are separate sets: 32 is a valid spacing step and not a type step (use 30 or 36), and 30 is a type step but not a spacing step. Line-height tightens as size grows; body lines stay within 40–80 characters. For typeface selection and pairing, use the `google-fonts` skill (https://www.skills.sh/sliday/google-fonts-skill/google-fonts) instead of picking fonts ad hoc.

Fix the remaining system rules explicitly: semantic color tokens for surface, text, action, status, and focus, with contrast floors of 4.5:1 for body text and 3:1 for large text and essential UI graphics (large means 24px regular or 18.66px bold, not 18px; the separate 3:1 non-text floor covers borders that identify a control, not decorative dividers); icon vocabulary; border, elevation, and motion rules; content and error-message voice; keyboard, pointer, touch, focus, hover, selected, disabled, loading, and destructive states.

One-off visual values require a reason. Consistency is not sameness: component variants should communicate different semantics while remaining part of one system.

#### 5d. Craft details

##### Surfaces

- Concentric radius: outerRadius = innerRadius + padding. Above 24px padding, treat layers as separate surfaces (make-interfaces-feel-better).
- Shadows over borders for elevation. Light token: `0 0 0 1px rgba(0,0,0,.06), 0 1px 2px -1px rgba(0,0,0,.06), 0 2px 4px 0 rgba(0,0,0,.04)`; hover .08/.08/.06. Dark: single ring `0 0 0 1px rgba(255,255,255,.08)`, hover .13. Keep real borders for dividers and input outlines (make-interfaces-feel-better).
- One box-shadow depth per section (better-frontend).
- Image outlines: `1px` `rgba(0,0,0,0.1)` light / `rgba(255,255,255,0.1)` dark, `outline-offset: -1px`. Pure black/white only; tinted neutrals read as dirt (make-interfaces-feel-better).
- Translucent chrome: `backdrop-filter: blur(20px) saturate(180%)` + semi-transparent bg; never stack two light translucent surfaces; scroll-edge fade instead of a 1px border under sticky headers (apple-design).
- Dim scrim behind modal tasks; parallel non-blocking panels get no scrim (apple-design).

##### Optical alignment

- Optical beats geometric. Icon-side button padding = text-side minus 2px; play triangles shift about 2px right; fix asymmetric icons in the SVG itself (make-interfaces-feel-better).
- Align mixed type sizes on one line by baseline, not center; centering misaligns them in a way that reads as subtly broken (refactoring-ui).
- Add roughly +0.05em tracking to all-caps text: caps are uniform blocks that crowd at default spacing (refactoring-ui).
- Keep icons near their intended size. A 16–24px icon blown up to 48px reads chunky and detail-starved; nest it in a colored circle instead (refactoring-ui).
- Choose elevation by the element's z-position, not by which shadow looks best; shrinking a shadow on press reads as depressed (refactoring-ui).
- Constrain user-uploaded imagery: fixed containers, cover-fit, crop the overflow. When an upload's edges dissolve into the page, use a faint inset shadow rather than a border, which fights the image's own colors (refactoring-ui).

##### Text rendering

- `text-wrap: balance` on headings (works only up to 6 lines Chromium / 10 Firefox); `text-wrap: pretty` on short-to-medium body; neither on 10+ lines (make-interfaces-feel-better).
- `font-variant-numeric: tabular-nums` on any updating number (counters, timers, prices, table columns); not on phone numbers or version strings (make-interfaces-feel-better).
- `-webkit-font-smoothing: antialiased` + `-moz-osx-font-smoothing: grayscale` once at the root (make-interfaces-feel-better).
- Author the spacing scale in rem so it tracks user text size: 4px = 0.25rem, 8px = 0.5rem, 16px = 1rem. The px values in 5b name design-time grid steps, not literal units (apple-design).

##### Interaction feel

- Feedback on pointer-down, not release; continuous during the interaction (apple-design).
- Scale on press: `:active { scale: 0.96 }` with 150ms ease-out; never below 0.95; offer a `static` opt-out (make-interfaces-feel-better, emil-design-eng).
- Gate hover behind `@media (hover: hover) and (pointer: fine)` (emil-design-eng).
- Extend small controls to full hit size with a pseudo-element; never overlap two hit areas (make-interfaces-feel-better).
- Tooltips: delay the first, open adjacent ones instantly with no animation while one is open (emil-design-eng).
- Same action name through the flow: "Publish" button yields "Published" toast; errors say what happened and how to fix, no apology, never vague (frontend-design).

##### Self-check

- Review with fresh eyes next day; play animations at 2-5x duration and frame-by-frame to catch overlap, wrong transform-origin, desynced properties (emil-design-eng).
- Report polish diffs as a Before/After/Why table, one row per change (emil-design-eng).

#### 5e. Motion

##### Decide first

- Frequency gate: 100+ uses/day (keyboard shortcuts, command palette) never animate; tens/day reduce drastically; occasional (modals, drawers, toasts) standard; rare moments may delight. Never animate keyboard-initiated actions; context menus animate exit only (emil-design-eng, 12-principles-of-animation).
- Every animation names a purpose: spatial consistency, state indication, feedback, explanation, or preventing a jarring change. "Looks cool" + frequent = cut (emil-design-eng).

##### Durations

- Press feedback 100-160ms; tooltips/small popovers 125-200ms; dropdowns/selects 150-250ms; modals/drawers 200-300ms, large drawers up to 500ms only as a declared exception (the craft audit flags >=400ms for review); general UI ceiling 300ms (emil-design-eng).
- Exits shorter and softer than enters (150ms vs 300ms); exit with small fixed translateY about -12px, not container height (make-interfaces-feel-better).
- Identical timing for similar elements; slow only where the user decides (hold-to-delete 2s linear), fast where the system responds (release 200ms ease-out) (12-principles-of-animation, emil-design-eng).

##### Easing

- Enter ease-out, exit ease-in, on-screen move ease-in-out, hover/color ease, linear only for constant motion. Never ease-in on entrances (emil-design-eng, 12-principles-of-animation).
- Built-ins are weak; tokens: `--ease-out: cubic-bezier(0.23,1,0.32,1)`, `--ease-in-out: cubic-bezier(0.77,0,0.175,1)`, drawer `cubic-bezier(0.32,0.72,0,1)` (emil-design-eng).

##### What and how

- Animate only transform, opacity, filter, clip-path; never `transition: all`, list exact properties (emil-design-eng, make-interfaces-feel-better).
- Never enter from `scale(0)`: use `scale(0.95)` + `opacity: 0`; enter recipe adds `translateY(8-12px)` + `blur(4px)` (emil-design-eng, make-interfaces-feel-better).
- Popovers scale from their trigger's transform-origin; modals stay centered. Enter and exit along the same path (emil-design-eng, apple-design).
- Stagger semantic chunks about 100ms apart, list items 30-80ms (50ms cap for dense lists); one focal point at a time; never block interaction (make-interfaces-feel-better, 12-principles-of-animation).
- CSS transitions for interactive state (interruptible, retargets); keyframes only for one-shot sequences; `@starting-style` for entry; `initial={false}` so default-state elements skip mount animation (emil-design-eng, make-interfaces-feel-better).
- Springs for gestures: bounce 0 default, 0.1-0.3 only after a flick; animate from the live on-screen value; hand off release velocity; rubber-band boundaries instead of hard stops (apple-design).

##### Reduced motion

- `prefers-reduced-motion: reduce` means gentler, not zero: keep opacity/color changes, replace slides/springs/parallax with about 200ms cross-fades, drop overshoot; `prefers-reduced-transparency` raises bg opacity and drops blur (emil-design-eng, apple-design).

### 6. Compose hierarchy and layout

Use size, contrast, position, spacing, alignment, and containment to reflect actual importance.

When reviewing an interface you did not design, or when the only report is "it looks off", start from `references/visual-diagnostics.md`: a symptom-to-fix index covering hierarchy, spacing, borders, typography, imagery, polish, and accessibility.

Weight and color do more of this work than size. Leaning on size alone pushes the primary element to cartoon proportions and squeezes the secondary one below readability; keep sizes nearer the middle of the scale and separate levels with weight (600/700) and text color instead. Cap text colors at three (primary, secondary, tertiary), and hold all three to 4.5:1, which puts the lightest around the middle of the ramp rather than the pale end. When one element still refuses to lead, de-emphasize its neighbors instead of amplifying it (refactoring-ui).

Rank actions by importance, not by semantics: primary is one solid high-contrast action per surface, secondary is outline or low-contrast fill, tertiary reads as a link. A destructive action is not automatically a large red button; give Delete tertiary treatment where it sits, then make it the primary action inside its confirmation dialog (refactoring-ui).

When a component looks generic, the cause is usually an inherited mental picture of what that component is. Break the box: dropdowns can carry columns, icons, and per-item descriptions; a table column can hold two related fields; a radio group can become selectable cards that show the actual differences (refactoring-ui).

Marketing-surface composition rules:

- Hero budget: brand, one headline, one supporting sentence, one CTA group, one dominant image. No stat strips, pill clusters, icon rows, promo chips (better-frontend).
- Brand test: remove the nav; if the first viewport could belong to another brand, branding is too weak (better-frontend).
- Full-bleed hero on landing pages; no inset/rounded media-card heroes, no floating badges on hero media (better-frontend).
- Cards only when they contain interaction. Card test: strip border/shadow/background; if nothing is lost, it is not a card (better-frontend).
- Structure encodes meaning: 01/02/03 markers only for real sequences; marketing narrative runs hero, supporting imagery, product detail, social proof, final CTA (frontend-design, better-frontend).

Required checks:

- the primary task is obvious within a few seconds;
- section boundaries survive a squint/blur test;
- labels sit with the controls or values they describe;
- primary, secondary, and destructive actions do not compete;
- content remains readable at narrow widths and zoom;
- long labels, translations, large numbers, missing images, and dense data do not collapse the layout;
- visual centering is inspected, not assumed from equal CSS offsets.

Avoid centering long reading text, excessive line length, ornamental cards, ambiguous icons, and decorative whitespace that pushes the next action off-screen.

### 7. Design controls, forms, and content

- Use familiar native semantics before custom widgets.
- Keep visible labels on inputs; placeholders are examples, not labels.
- In read-only data display, labels are a last resort: most values identify themselves by format or context. Fold the label into the value ("12 left in stock") or make it clearly secondary. Spec sheets, where people scan for the label itself, are the exception. This never licenses removing input labels (refactoring-ui).
- Design the empty state as a real screen: one illustration or mark, one clear headline, one emphasized action. Hide tabs, filters, and search until content exists to act on (refactoring-ui).
- Ask only for information required now.
- Match controls to the decision: checkbox for independent choices, radio for a small exclusive set, select/combobox for larger known sets, search/filter for large spaces.
- Preserve entered data after errors.
- Validate at a useful moment without fighting normal typing.
- Explain errors in plain language: what happened, where, and how to recover.
- Make destructive consequences explicit and proportional; prefer undo when feasible.
- Use action-specific button labels and destination-specific links.
- Never rely on color, position, gesture, hover, or iconography as the only carrier of meaning.

### 8. Accessibility and resilience gate

At minimum verify:

- semantic structure and accessible names;
- logical reading and focus order;
- keyboard operation and visible focus;
- contrast and non-color status meaning;
- target size and target spacing;
- zoom, reflow, and text resizing;
- screen-reader exposure of hidden/intermediate content;
- error identification and recovery;
- reduced motion and animation control;
- touch, pointer, keyboard, and assistive-input paths;
- loading, partial, offline, empty, and permission states.

Do not claim accessibility conformance from a visual review alone. Use automated checks as a floor and manually exercise keyboard, screen-reader, zoom, and state behavior relevant to the interface.

### 9. Verify the rendered product

Source code, a design file, or a component test is not enough. When implementation access exists:

1. open the real interface;
2. exercise the primary flow and at least one recovery flow;
3. capture representative wide and narrow viewports;
4. inspect actual pixels, content, alignment, focus, and state changes;
5. test realistic and extreme content;
6. verify console/network behavior when relevant;
7. compare before/after evidence;
8. distinguish verified behavior from assumptions and remaining risks.

Use `agent-visual-verification` when a deterministic screenshot evidence path is needed. Use full browser automation when the flow requires navigation, typing, state mutation, network inspection, or assertions.

## Automated guards

The skill ships mechanical checks; run them instead of eyeballing:

- **`scripts/grid-audit.sh <file-or-dir>`** flags every px value off the 8px grid, per CSS property: margins/padding/gap/radius must be 0/1/2 or divisible by 4; `font-size` must be in the 12/14/16/18/20/24/30/36/48/60/72 set; `line-height` and `letter-spacing` are exempt (readability beats grid). Exit 1 on violations, with `file:line: property value` output.
- **`hooks/design-guard.sh`** is a PostToolUse hook: after any Edit/Write to a `.css/.scss/.less/.html/.jsx/.tsx/.vue/.svelte` file, it audits that file and feeds violations back to the agent as a fix prompt. Silent on clean files, non-style files, and malformed input; never blocks the edit itself; no retries.
- Install: merge `hooks/hooks.json` into `.claude/settings.json` (project) or `~/.claude/settings.json` (global); adjust the script path to where this skill is installed.

The guard catches literals, not judgment: it cannot see an inverted proximity ladder, a cloned component, or a missing state. Those still require the review workflow above.

## Review severity

Classify findings by user impact:

- **Blocker:** prevents completion, causes data loss, exposes unsafe action, or creates a critical accessibility barrier.
- **Major:** likely confusion, abandonment, repeated error, inaccessible path, or material loss of trust.
- **Minor:** local inconsistency or friction with a clear workaround.
- **Polish:** aesthetic improvement without meaningful task impact.

Lead with blockers and majors. Do not bury a broken flow under spacing comments.

## Output format

1. **User, job, and interface promise**
2. **Product truth and constraints**
3. **IA hierarchy** — primary, secondary, tertiary, metadata
4. **Flow and state model**
5. **Relevant UX laws** — problem → law → design move → trade-off
6. **System rules** — spacing grid, tokens, atomic component inventory, type, color, motion, copy
7. **Screen/component decisions**
8. **Accessibility and resilience requirements**
9. **Rendered verification evidence**
10. **Findings by severity and remaining risks**

For implementation tasks, make the changes and cite concrete files/components. Do not stop at critique when the user asked for a fix.

## Compact release checklist

- [ ] Primary user, job, success, and failure are explicit.
- [ ] Product state and action availability are truthful.
- [ ] IA follows user meaning and decision sequence.
- [ ] One clear primary action exists per decision surface.
- [ ] Needed context is visible; rare complexity is progressively disclosed.
- [ ] Relevant UX laws were selected by problem, with misuse checks.
- [ ] Every padding, margin, and gap sits on the spacing scale; exceptions are named tokens with reasons.
- [ ] Repeated patterns are extracted components with variants; no near-duplicate clones.
- [ ] Components consume semantic tokens; no hardcoded color or spacing literals.
- [ ] Loading, empty, partial, success, error, interruption, and recovery states are covered.
- [ ] Controls have honest hierarchy, labels, target size, focus, and states.
- [ ] Forms preserve work and explain recovery.
- [ ] Color is not the only signal; contrast and focus are visible.
- [ ] Narrow viewport, zoom, long content, and translation stress were tested.
- [ ] Keyboard and relevant assistive-technology paths were exercised.
- [ ] The actual rendered interface was inspected.
- [ ] Verified facts and unverified assumptions are separated.

## Anti-patterns

- Starting with components, visual references, or a design trend before understanding the task.
- Citing UX laws as proof without observing the actual user problem.
- Applying arbitrary numeric limits such as “never show more than seven items.”
- Hiding complexity that users need to understand consequences.
- Using progressive disclosure to conceal price, risk, permissions, or destructive effects.
- Adding cards, borders, icons, motion, gradients, or color without informational purpose.
- Off-scale spacing literals (9px, 13px, 17px) instead of scale tokens.
- Cloned near-identical components that drift in radius, padding, or background instead of one component with variants.
- Forcing line-height and letter-spacing onto the 8px grid at the cost of readability.
- Multiple competing primary actions.
- Placeholder-only labels, icon-only meaning, or color-only status.
- Custom controls that lose native keyboard and accessibility behavior.
- Fake progress, manipulative urgency, guilt-driven incompletion, or surprise steps.
- Treating responsive design as shrinking the desktop layout.
- Declaring success from source inspection without exercising the rendered interface.
- Reporting dozens of polish notes while a core flow is broken.

## Do Not Use When

- The task has no user interface or user-facing workflow.
- The real blocker is an unresolved product, policy, legal, or business decision that design cannot safely invent.
- The user needs empirical research with a specific population; run research rather than presenting heuristics as evidence.
- A specialized domain standard—medical, aviation, automotive, financial trading, public safety—supersedes generic UX guidance.

## Sources and provenance

This is an original synthesis. Version 1.2 additionally merges concrete craft rules mined from installed design skills (better-frontend, make-interfaces-feel-better, emil-design-eng, apple-design, frontend-design, 12-principles-of-animation, ui-ux-pro-max, landing-page-design, web-design-guidelines, google-fonts); the full deduped catalog with per-rule attribution lives in `references/borrowed-craft.md`. Version 1.3 adds a visual symptom-to-fix index in `references/visual-diagnostics.md` and inline hierarchy, palette, and type-scale rules distilled from Refactoring UI (Adam Wathan, Steve Schoger) by way of the refactoring-ui-skill notes, rewritten and reconciled with this skill's existing systems. A user-provided set of 18 UX-law notes was treated as source material, then rewritten, de-frameworked, corrected, and consolidated rather than republished as separate micro-skills.

Useful public references:

- Laws of UX — practitioner index of UX laws: https://lawsofux.com/
- Nielsen Norman Group — 10 usability heuristics: https://www.nngroup.com/articles/ten-usability-heuristics/
- Nielsen Norman Group — response-time limits: https://www.nngroup.com/articles/response-times-3-important-limits/
- W3C — WCAG 2.2 target size minimum: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
- W3C — WCAG 2.2 focus appearance: https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html

The laws are heuristics. Validate consequential decisions with users, domain evidence, accessibility testing, and the real rendered product.
