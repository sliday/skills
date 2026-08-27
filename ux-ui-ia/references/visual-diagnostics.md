# Visual diagnostics: symptom to fix

Reverse index for the visual layer. SKILL.md section 4 selects UX laws from an
observed behavioral failure; this file does the same for an observed visual
failure. Use it when a human says "looks off", "feels cheap", "looks amateur",
or when reviewing an interface you did not design.

Each row: the symptom you can see, the cause that usually produces it, the fix.
Fixes are mechanical. Apply the one matching the cause, not every one listed.

Lineage: distilled from Refactoring UI (Adam Wathan, Steve Schoger) via the
refactoring-ui-skill notes, rewritten and reconciled with this skill's systems.

## Hierarchy and emphasis

| Symptom | Cause | Fix |
|---|---|---|
| Wall of content, nothing leads | Every element carries the same weight | Demote secondary and tertiary material rather than inflating the primary one |
| The hero refuses to stand out | Neighbors compete with it | De-emphasize the competitors: fade inactive nav, drop the sidebar background, mute surrounding chrome |
| Primary is huge, secondary is unreadable | Size carries the whole hierarchy | Move the work to weight (600/700) and text color; pull both sizes toward the middle of the scale |
| Delete is a large red button | Styled by meaning instead of importance | Give destructive actions tertiary treatment where they live; promote to primary only inside the confirmation dialog |
| Page title dominates the screen | An `h1` treated as a size instruction | Section titles are usually labels; 16px is fine, and some belong visually hidden |
| Icon shouts louder than its label | Solid icons cover more area than text at the same size | Lower the icon's contrast until it sits behind the text |
| Everything is bold, so nothing is | Weight used as decoration | Reserve heavy weight for one emphasis level per surface |

## Spacing and grouping

| Symptom | Cause | Fix |
|---|---|---|
| Cramped, airless | Space added incrementally until it stopped hurting | Restart from generous space and subtract; additive spacing lands on the minimum, not the right amount |
| Grouping is ambiguous | Identical spacing inside and between groups | More space around a group than within it. Ambiguous spacing is a functional defect, not a cosmetic one |
| Bullet list reads as a block | Line-height used as item separation | Separate items with gap, keep line-height for reading |
| Layout smeared across a wide screen | Container takes all available width | Take only the width the content needs, or split into columns |
| Sidebar wrong at every size | Percentage widths | Fix the sidebar, let the main area flex |

## Borders, color, contrast

| Symptom | Cause | Fix |
|---|---|---|
| Over-compartmentalized, boxes in boxes | A border for every relationship | Replace with shadow, a background tint, or spacing. When a border and a background change coexist, drop the border |
| 1px border invisible, darker version harsh | Treating color as the only lever | Keep the soft color and go to 2px |
| Text on a colored panel looks disabled | Grey or translucent white over color | Pick a solid color sharing the background's hue, tuned in saturation and lightness. Translucent white also lets patterns bleed through the glyphs |
| Headline over a photo unreadable | The image, not the type | Overlay a scrim, raise image brightness, desaturate and multiply a brand color, or apply a large-blur zero-offset shadow as a glow |
| Elevation reads as decoration | Shadow chosen by looks | Choose elevation by the element's z-position: barely raised, floating, modal. Shrink on press to read as depressed |

## Typography

| Symptom | Cause | Fix |
|---|---|---|
| Reads like a database dump (`Name:`, `Email:`) | Labels on self-identifying data | Drop labels implied by format or context, or fold them into the value ("3 bedrooms", "12 left in stock"). Applies to read-only display only; form inputs keep visible labels |
| Mobile headline enormous | Type sized in `em` inherited from desktop | Set sizes per breakpoint. Large text shrinks faster than body text |
| Mixed sizes on one line look wrong | Vertical centering | Align on the baseline |
| All-caps hard to read | Caps are uniform blocks and crowd at default tracking | Add roughly +0.05em letter-spacing |
| Body face used large looks loose | Legibility faces track wider than display faces | Tighten roughly -0.05em. The reverse fails: loosening a display face will not make it legible small |
| Sea of colored links | Prose link styling inside a link-dense interface | Use weight or a darker color; reserve underlines and hover-only styling for minor links |
| Centered paragraph looks broken | Centering past two or three lines | Left-align, or shorten the copy until centering holds |
| Numeric column hard to scan | Left-aligned numbers | Right-align numbers and use tabular figures |
| Rivers running through justified text | Justification without hyphenation | Enable hyphenation or abandon justification |

## Images and assets

| Symptom | Cause | Fix |
|---|---|---|
| Large icon looks chunky and detail-starved | A 16-24px icon scaled up | Keep the icon at its intended size inside a colored circle or square |
| Screenshot is mush | Full desktop viewport shrunk into a small frame | Shrink the captured viewport, crop to the region that matters, or illustrate a simplified version |
| Logo unreadable as a favicon | One artwork used at every size | Draw a simplified mark at the target size |
| Overlapping images clash | Two competing images meeting directly | Give one a border in the page background color, an invisible border that forces a gap |
| Avatar dissolves into the page | Image background matches the UI background | Add a subtle inset shadow. A border fights the image's own colors |
| User uploads break the layout | Arbitrary intrinsic aspect ratios | Fixed containers, cover-fit, crop the overflow |

## Polish and personality

| Symptom | Cause | Fix |
|---|---|---|
| Flat: nothing wrong, nothing right | No accent anywhere | Add one: a colored edge on a card or heading, a shifted section background, a shallow two-hue gradient (under 30 degrees), or a subtle pattern along a single edge |
| Prototype-ish | Browser defaults left in place | Icons for bullets, branded checkboxes and radios, distinct link styling, testimonials treated as visual elements |
| Blank screen on first run | Empty state left as an afterthought | Illustration, one clear headline, one emphasized action. Hide tabs, filters, and search until content exists |
| Component looks generic | An inherited mental picture of what the component is | Break the box: dropdowns with columns, icons, and per-item descriptions; tables folding a non-sortable field into a related column; radio groups as selectable cards showing the real differences |
| Elements look pasted on | Each element sits in its own rectangle | Overlap layers with negative offsets so a card spans two backgrounds or overhangs its parent |

## Accessibility

| Symptom | Cause | Fix |
|---|---|---|
| Chart fails colorblind readers | Series distinguished by hue | Distinguish by lightness within one hue, and add icons, labels, or direction arrows |
| Status reads only as color | Color used as the sole carrier | Add shape, icon, or text |
| Grey text technically passes, still unreadable | Tertiary grey drifted toward the pale end | All three text colors need 4.5:1. The lightest is mid-ramp, not pale |
