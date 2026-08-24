---
name: ux-ui-ia
version: 1.1.1
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

Create a constrained system rather than styling each screen independently. Two defaults do most of the work: an **8px spatial grid** and **atomic composition**. If the codebase already has an equivalent system, extend it; never run a second system beside it.

#### 5a. Spacing and sizing: the 8px grid

Every padding, margin, gap, and fixed box dimension comes from one scale on an 8px base, with 4px as the half-step for tight pairs (icon-to-label, checkbox-to-text):

```text
4  8  12  16  24  32  48  64  96
```

Define the scale as tokens (`--space-1: 8px` … `--space-12: 96px`, or the framework equivalent) and spend values from tokens, not literals.

Rules that survive real projects:

- **The grid governs boxes, not glyphs.** Apply it to padding, margins, gaps, control heights, and icon sizes. Line-height obeys readability, not the grid: 25.6px or 28px line-height is correct where the grid would force 24px or 32px.
- **The spacing ladder must never invert.** Spacing encodes grouping (Law of Proximity): label-to-control 4–8, siblings inside a group 8–16, between groups 24–32, between page sections 48+. A card whose internal padding (16) exceeds the gap to its neighbor (8) reads as one merged blob.
- **Size controls on the grid.** Control heights 32/40/48; icons 16/20/24; pointer targets at least 24×24 (WCAG 2.2 floor), 44×44 for primary touch actions.
- **Exceptions are declared, not leaked.** A living system tolerates a few off-scale values (a 12px chip padding, an 80px hero offset) when they are named tokens with a stated reason. Silent literals like 9px, 13px, 17px are defects.
- **Audit mechanically.** Grep the styles for `px` values not divisible by 4; that list is the violation report. In rendered review, off-grid values appear as almost-aligned edges: measure, do not eyeball.

#### 5b. Composition: the atomic system

Build in strict layers; each layer consumes only the layer below:

```text
tokens → atoms → molecules → organisms → templates → screens
```

- **Tokens** in two tiers: primitive (`--gray-700`, `--space-2`) and semantic (`--color-text`, `--btn-bg`). Components reference semantic tokens only, so theming and dark mode become token swaps, not rewrites.
- **Atoms:** button, input, label, icon, badge, checkbox. An atom never sets its own external margin; the parent owns spacing via gap.
- **Molecules:** form field (label + control + help + error), search bar, setting row, menu item.
- **Organisms:** form, card list, header, settings section.
- **Templates and screens** compose organisms; a new screen that demands a new atom needs a stated reason.

Rules that survive real projects:

- **Tokens are step zero.** Retrofitting tokens onto already-styled screens is the single largest time sink in system work; hardcoded colors and spacing metastasize. Cut tokens before styling the first screen.
- **Rule of three.** Second appearance of a pattern: note it. Third: extract the component. Two "setting rows" with different backgrounds, radii, and padding are one molecule with a bug, not two designs.
- **Variants, not clones.** Same function, one component, differentiated by modifier (`primary/secondary/ghost/destructive`, `sm/md/lg`), never by copy-pasted styles that drift apart.
- **One radius and one elevation per component level.** Pick a small set (4/8/12/full) and map each component class to one value. Mixed radii inside one card stack is the fastest tell of an unsystematic UI.
- **Type scale is semantic and small.** Roles (display, heading, subheading, body, caption) mapped to a modular set such as 12/14/16/20/24/32; line-height tightens as size grows; body lines stay within 40–80 characters. For typeface selection and pairing, use the `google-fonts` skill (https://www.skills.sh/sliday/google-fonts-skill/google-fonts) instead of picking fonts ad hoc.

Fix the remaining system rules explicitly: semantic color tokens for surface, text, action, status, and focus, with contrast floors of 4.5:1 for body text and 3:1 for large text and essential UI graphics; icon vocabulary; border, elevation, and motion rules; content and error-message voice; keyboard, pointer, touch, focus, hover, selected, disabled, loading, and destructive states.

One-off visual values require a reason. Consistency is not sameness: component variants should communicate different semantics while remaining part of one system.

### 6. Compose hierarchy and layout

Use size, contrast, position, spacing, alignment, and containment to reflect actual importance.

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
- Keep visible labels; placeholders are examples, not labels.
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

This is an original synthesis. A user-provided set of 18 UX-law notes was treated as source material, then rewritten, de-frameworked, corrected, and consolidated rather than republished as separate micro-skills.

Useful public references:

- Laws of UX — practitioner index of UX laws: https://lawsofux.com/
- Nielsen Norman Group — 10 usability heuristics: https://www.nngroup.com/articles/ten-usability-heuristics/
- Nielsen Norman Group — response-time limits: https://www.nngroup.com/articles/response-times-3-important-limits/
- W3C — WCAG 2.2 target size minimum: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
- W3C — WCAG 2.2 focus appearance: https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html

The laws are heuristics. Validate consequential decisions with users, domain evidence, accessibility testing, and the real rendered product.
