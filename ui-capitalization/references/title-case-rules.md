# Title case rules

Only needed for Mode 2 and Mode 3. Mode 1 does not use this file.

Pick one standard and name it in the style note. The four in use disagree on the same string, so "title case" alone is not a decision.

## The same string, four standards

Input: `a great tool with the twist but not without its own quirks`

| Standard | Result |
|---|---|
| Apple Style Guide | A Great Tool with the Twist but Not Without Its Own Quirks |
| Chicago 18th ed. | A Great Tool with the Twist but Not Without Its Own Quirks |
| Chicago 17th ed. | A Great Tool with the Twist but Not without Its Own Quirks |
| AP | A Great Tool With the Twist but Not Without Its Own Quirks |
| APA | A Great Tool With the Twist but Not Without Its Own Quirks |
| Broken (what teams ship) | A Great Tool With The Twist But Not Without Its Own Quirks |

The gap between Chicago 17 and 18 is real and recent: the 18th edition moved long prepositions from lowercase to capitalized. Two reviewers working from different editions will correct each other forever. Write the edition down.

Apple and Chicago 18 agree on almost everything, which makes **Apple** the practical default for product UI: it is written for interface text, its rules are enumerated, and it is stable.

## Apple Style Guide rules

Capitalize:

- The first and last word, whatever the part of speech.
- Nouns, pronouns, verbs, adjectives, and adverbs, at any length. That includes `It`, `This`, `You`, `Your`, `My`, `Is`, `Are`, `Be`.
  - `Skip This Backup`, `Apple News Is Offline`, `Passwords Are Locked`
- Conjunctions other than coordinating ones, at any length.
  - `What to Do If Your iPhone Is Lost`
- Prepositions of five letters or more: `About`, `Between`, `Through`, `Without`, `Against`, `During`.
- Prepositions of any length inside a phrasal verb, or used as another part of speech.
  - `Start Up the Computer`, `Turn On Apple Watch`, `Log In to the Server`
  - Inflected forms count: `Starting Up the Computer`, `Logging In to the Server`
- The second word of a hyphenated compound, except `Built-in` and `Plug-in`.
  - `High-Level Events`, `64-Bit Addressing`

Do not capitalize:

- Articles `a`, `an`, `the`, unless first or following a colon.
- Coordinating conjunctions: `and`, `but`, `or`, `nor`, `for`, `yet`, `so`.
- `to` in an infinitive: `How to Start Your Computer`.
- `as`, whatever the part of speech: `Export a Document as a PDF`.
- Words that always begin lowercase: `iPad`, `macOS`, `iPhone`, `npm`, `eBay`.
- Prepositions of four letters or fewer: `at`, `by`, `for`, `from`, `in`, `into`, `of`, `off`, `on`, `onto`, `out`, `over`, `to`, `up`, `with`.

### Older Apple editions say the same thing differently

A team holding an older copy of the guide sees the rule as one exclusion instead of two lists:

> Don't capitalize prepositions of four letters or fewer (at, by, for, from, in, into, of, off, on, onto, out, over, to, up, and with), except when the word is part of a verb phrase or is used as another part of speech.

Long prepositions go unmentioned there, so they stay capitalized by omission. The output is identical to the current edition. If two reviewers are quoting different Apple PDFs, they are not actually disagreeing. Check the edition before relitigating.

Older examples worth keeping, because they cover the inflected case the current edition drops: `Starting Up the Computer`, `Logging In to the Server`, `Getting Started with Your MacBook Pro`.

## Chicago (18th ed.)

1. Capitalize the first and last word.
2. Capitalize nouns, pronouns, adjectives, verbs (including phrasal verbs), adverbs, and subordinating conjunctions.
3. Lowercase articles, coordinating conjunctions, and prepositions of fewer than five letters, except when a preposition works adverbially or adjectivally.
4. Lowercase `to` in an infinitive.

Chicago 17 lowercased prepositions regardless of length. That single line is the whole difference.

## AP

Same first two rules, then it diverges:

- Capitalize any word of four or more letters, including conjunctions and prepositions.
- Capitalize both parts of a hyphenated word.
- Capitalize `to` in an infinitive.

AP produces the most capitals of the four. Use it when the product's editorial style is already AP (newsrooms, press-facing surfaces).

## APA

- Capitalize all major words, including the second part of a hyphenated major word.
- Capitalize all words of four letters or more.

APA is an academic standard. Reach for it only when the surrounding content is academic.

## Phrasal verbs

The single most-failed rule in product UI. The particle is part of the verb, so it is capitalized regardless of length.

`Log In` · `Log Out` · `Sign In` · `Sign Up` · `Sign Out` · `Set Up` · `Back Up` · `Start Up` · `Shut Down` · `Turn On` · `Turn Off` · `Opt In` · `Opt Out` · `Check In` · `Check Out` · `Follow Up` · `Roll Back` · `Top Up` · `Zoom In` · `Zoom Out` · `Fill In` · `Pick Up` · `Drop Off`

Watch the second occurrence in a longer string. In `Log In to the Server`, the first `In` is a particle and capitalized; the following `to` is an ordinary preposition and stays lowercase.

Same trap in reverse: `Always on Top` keeps `on` lowercase, because there `on` is a plain preposition.

## First and last word beats everything

`Save As` and `Go To` capitalize their final word even though `as` and `to` are on every lowercase list. Position wins.

Corollary for lowercase brands: never capitalize `iPhone`, `eBay`, or `npm` to satisfy the first-word rule. Rewrite the string so the brand is not first.

## Words after a colon

Capitalize the first word after a colon, including an article: `Storage: The Basics`.

## Quick test before shipping a title-case string

1. Is it longer than six words? Use sentence case instead.
2. Does it end in punctuation? Use sentence case instead.
3. Are `a`, `an`, `the`, `and`, `but`, `or`, `to`, `as` capitalized anywhere except first or last position? Fix.
4. Is a phrasal-verb particle lowercase? Fix.
5. Did a brand get its casing rewritten? Revert.
