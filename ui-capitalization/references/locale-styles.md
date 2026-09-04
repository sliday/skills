# Regional English styles

Pick one locale per product and record it. Mixing en-US spelling with en-GB punctuation is the same failure as mixing title and sentence case, and users notice it faster.

## Which mode each locale expects

| Locale | Prevailing convention | Authority |
|---|---|---|
| en-US | Title case is normal in product UI and marketing | Chicago, AP, Apple Style Guide |
| en-GB | Sentence case | GOV.UK content style, most UK house guides |
| en-CA | Sentence case | Canadian Press style |
| en-AU | Sentence case, stated as a rule | Australian Government Style Manual |
| en-NZ | Sentence case | NZ government and education guides, following AU and UK |

The Australian Style Manual frames this as minimal capitalisation: lowercase common nouns and adjectives, never set headings in all capitals, and capitalize `government` only inside a formal name.

Shipping title case into en-GB, en-AU, or en-NZ is not forbidden, but it reads as an American import. Say so before design starts, not during review.

## Spelling axes

Six axes cover nearly every UI string. Get the axis right and individual words follow.

| Axis | en-US | en-GB | en-CA | en-AU | en-NZ |
|---|---|---|---|---|---|
| -or / -our | color, behavior, favorite | colour, behaviour, favourite | colour | colour | colour |
| -er / -re | center, meter, theater | centre, metre, theatre | centre | centre | centre |
| -ize / -ise | organize, customize, analyze | organise, customise, analyse | organize, analyze | organise, analyse | organise, analyse |
| -se / -ce (noun) | license, defense, practice | licence, defence, practice (n) | licence, defence | licence, defence | licence, defence |
| single / double l | canceled, traveled, labeled, modeling | cancelled, travelled, labelled, modelling | cancelled | cancelled | cancelled |
| -og / -ogue | catalog, dialog, analog | catalogue, dialogue, analogue | catalogue | catalogue | catalogue |

Notes that trip people up:

- **en-CA is the split case.** British `-our` and `-re`, American `-ize`. `colour` and `organize` in the same sentence is correct Canadian.
- **Oxford spelling** is British `-our` plus `-ize` (`colour`, `organize`), used by Oxford University Press and some journals. Valid en-GB, but pick it deliberately and stay on it.
- **`licence` vs `license`**: outside the US, the noun is `licence` and the verb is `license`. Same pattern for `practice` (noun) and `practise` (verb) in en-GB, en-AU, en-NZ.
- **`program`**: en-AU and en-CA use `program` for everything. en-GB and en-NZ use `programme` for schemes, courses, and broadcasts, and `program` only for software.
- **`dialog`**: keep `dialog box` everywhere as the computing term. `dialogue` is the conversation.
- **`gray` / `grey`**: en-US `gray`, all others `grey`. Never change it inside a CSS token, color name, or design-system value.

## Vocabulary that differs in UI

| Concept | en-US | en-GB | en-CA | en-AU | en-NZ |
|---|---|---|---|---|---|
| Postal identifier | ZIP code | Postcode | Postal code | Postcode | Postcode |
| Region field | State | County | Province | State | Region |
| Phone | Cell phone | Mobile | Cell | Mobile | Mobile |
| Payment slip | Check | Cheque | Cheque | Cheque | Cheque |
| Basket | Cart | Basket | Cart | Cart | Cart |
| Residence | Apartment | Flat | Apartment | Apartment | Flat |
| Timetable | Schedule | Timetable | Schedule | Timetable | Timetable |
| Enrolment | Enrollment | Enrolment | Enrolment | Enrolment | Enrolment |

Form field labels are where this shows most. A `State` field on an en-GB signup form is a localization bug, not a wording preference.

## Punctuation

| Item | en-US | en-GB | en-CA | en-AU | en-NZ |
|---|---|---|---|---|---|
| Honorifics | Mr., Dr., Ms. | Mr, Dr, Ms | Mr., Dr. | Mr, Dr, Ms | Mr, Dr, Ms |
| Primary quotes | "double" | 'single' common | "double" | 'single' common | 'single' common |
| Punctuation vs quotes | Inside the quotes | Logical, outside unless quoted | Inside | Logical | Logical |
| Serial comma | Chicago yes, AP no | Usually no, only for clarity | Usually no | Only for clarity | Only for clarity |
| Time | 9:00 a.m. | 9am or 09:00 | 9 a.m. | 9am | 9am |
| Date, numeric | 05/30/2026 | 30/05/2026 | 2026-05-30 preferred | 30/05/2026 | 30/05/2026 |
| Date, spelled | May 30, 2026 | 30 May 2026 | May 30, 2026 | 30 May 2026 | 30 May 2026 |
| Collective nouns | the team is | the team are | the team is | the team are | the team are |

Numeric dates in UI are a data bug waiting to happen: `05/06` is two different days depending on the reader. Prefer the spelled month, or format from the user's locale rather than hardcoding a string.

## Capitalization details that are locale-specific

- **`Internet`**: lowercase in current US practice (AP dropped the capital), lowercase elsewhere. Capitalize only inside a proper name.
- **`Government`**: en-AU and en-GB capitalize it inside a formal name (`the Australian Government`) and lowercase it otherwise. US style lowercases it more often.
- **Job titles**: capitalize before a name (`Chief Executive Jane Doe`), lowercase after (`Jane Doe, chief executive`). Same rule across locales, broken everywhere.
- **Seasons, days of the week, months**: seasons lowercase everywhere. Days and months capitalized everywhere.

## Applying a locale change

1. Set the locale in the style note before touching strings.
2. Run the spelling axes as a batch, one axis at a time, reviewing each diff.
3. Fix vocabulary fields by hand. `State` to `County` may need a schema or validation change, not just a label.
4. Leave code identifiers, CSS tokens, API fields, and third-party strings alone. `background-color` stays American forever.
5. Check that a locale change did not silently change the case mode. Switching to en-GB does not authorize rewriting every button, unless the mode changed too and that was recorded.
