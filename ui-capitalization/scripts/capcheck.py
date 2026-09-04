#!/usr/bin/env python3
"""capcheck: audit UI strings for capitalization mode and locale consistency.

Stdlib only for JSON and text. YAML needs PyYAML and degrades with a warning
when it is absent. Reads i18n files flat or nested, or newline-delimited text.

    python3 capcheck.py --detect locales/en.json
    python3 capcheck.py --mode hybrid --locale en-GB locales/en.json
    python3 capcheck.py --mode sentence --locale en-AU --json src/i18n/*.json
    cat strings.txt | python3 capcheck.py --stdin --mode title

Exit codes: 0 clean, 1 findings at error severity, 2 usage error.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

# --------------------------------------------------------------------------
# Word data
# --------------------------------------------------------------------------

ARTICLES = {"a", "an", "the"}
COORD_CONJ = {"and", "but", "or", "nor", "for", "yet", "so"}
SHORT_PREPS = {"at", "by", "for", "from", "in", "into", "of", "off", "on",
               "onto", "out", "over", "to", "up", "with", "via", "per"}
LONG_PREPS = {"about", "above", "across", "after", "against", "along", "among",
              "around", "before", "behind", "below", "beneath", "beside",
              "between", "beyond", "during", "except", "inside", "outside",
              "through", "throughout", "toward", "towards", "under",
              "underneath", "until", "upon", "within", "without"}

# Verbs whose following particle stays capitalized in title case.
PARTICLE_VERBS = {"log", "sign", "set", "back", "start", "shut", "turn", "opt",
                  "check", "follow", "roll", "top", "zoom", "fill", "pick",
                  "drop", "print", "hold", "break", "look", "sync", "power"}
PARTICLES = {"in", "on", "off", "out", "up", "down", "over", "back", "through"}

ABBREVIATIONS = {"e.g.", "i.e.", "etc.", "vs.", "no.", "approx.", "min.", "max.",
                 "mr.", "mrs.", "ms.", "dr.", "prof.", "st.", "inc.", "ltd.",
                 "co.", "jan.", "feb.", "aug.", "sept.", "oct.", "nov.", "dec."}

ACRONYMS = {"API", "APIs", "CSV", "CSS", "CTA", "DNS", "FAQ", "GIF", "HTML",
            "HTTP", "HTTPS", "ID", "IDs", "JSON", "JPG", "MFA", "OK", "PDF",
            "PIN", "PNG", "QR", "SAML", "SDK", "SEO", "SMS", "SQL", "SSL",
            "SSO", "SVG", "TLS", "TOTP", "URL", "URLs", "UI", "UX", "VAT",
            "XML", "YAML", "ZIP", "AI", "IP", "OS", "PC", "TV", "USB", "GST"}

# Locale spelling axes. Each row maps locale -> preferred base form.
SPELLING = [
    # -or / -our
    {"en-US": "color", "en-GB": "colour", "en-CA": "colour", "en-AU": "colour", "en-NZ": "colour"},
    {"en-US": "behavior", "en-GB": "behaviour", "en-CA": "behaviour", "en-AU": "behaviour", "en-NZ": "behaviour"},
    {"en-US": "favorite", "en-GB": "favourite", "en-CA": "favourite", "en-AU": "favourite", "en-NZ": "favourite"},
    {"en-US": "honor", "en-GB": "honour", "en-CA": "honour", "en-AU": "honour", "en-NZ": "honour"},
    {"en-US": "labor", "en-GB": "labour", "en-CA": "labour", "en-AU": "labour", "en-NZ": "labour"},
    {"en-US": "neighbor", "en-GB": "neighbour", "en-CA": "neighbour", "en-AU": "neighbour", "en-NZ": "neighbour"},
    {"en-US": "flavor", "en-GB": "flavour", "en-CA": "flavour", "en-AU": "flavour", "en-NZ": "flavour"},
    # -er / -re
    {"en-US": "center", "en-GB": "centre", "en-CA": "centre", "en-AU": "centre", "en-NZ": "centre"},
    {"en-US": "theater", "en-GB": "theatre", "en-CA": "theatre", "en-AU": "theatre", "en-NZ": "theatre"},
    {"en-US": "liter", "en-GB": "litre", "en-CA": "litre", "en-AU": "litre", "en-NZ": "litre"},
    # -ize / -ise  (en-CA sides with en-US here)
    {"en-US": "organize", "en-GB": "organise", "en-CA": "organize", "en-AU": "organise", "en-NZ": "organise"},
    {"en-US": "organization", "en-GB": "organisation", "en-CA": "organization", "en-AU": "organisation", "en-NZ": "organisation"},
    {"en-US": "customize", "en-GB": "customise", "en-CA": "customize", "en-AU": "customise", "en-NZ": "customise"},
    {"en-US": "personalize", "en-GB": "personalise", "en-CA": "personalize", "en-AU": "personalise", "en-NZ": "personalise"},
    {"en-US": "authorize", "en-GB": "authorise", "en-CA": "authorize", "en-AU": "authorise", "en-NZ": "authorise"},
    {"en-US": "synchronize", "en-GB": "synchronise", "en-CA": "synchronize", "en-AU": "synchronise", "en-NZ": "synchronise"},
    {"en-US": "recognize", "en-GB": "recognise", "en-CA": "recognize", "en-AU": "recognise", "en-NZ": "recognise"},
    {"en-US": "analyze", "en-GB": "analyse", "en-CA": "analyze", "en-AU": "analyse", "en-NZ": "analyse"},
    {"en-US": "apologize", "en-GB": "apologise", "en-CA": "apologize", "en-AU": "apologise", "en-NZ": "apologise"},
    {"en-US": "summarize", "en-GB": "summarise", "en-CA": "summarize", "en-AU": "summarise", "en-NZ": "summarise"},
    # -se / -ce
    {"en-US": "license", "en-GB": "licence", "en-CA": "licence", "en-AU": "licence", "en-NZ": "licence"},
    {"en-US": "defense", "en-GB": "defence", "en-CA": "defence", "en-AU": "defence", "en-NZ": "defence"},
    {"en-US": "offense", "en-GB": "offence", "en-CA": "offence", "en-AU": "offence", "en-NZ": "offence"},
    # single / double l
    {"en-US": "canceled", "en-GB": "cancelled", "en-CA": "cancelled", "en-AU": "cancelled", "en-NZ": "cancelled"},
    {"en-US": "canceling", "en-GB": "cancelling", "en-CA": "cancelling", "en-AU": "cancelling", "en-NZ": "cancelling"},
    {"en-US": "traveled", "en-GB": "travelled", "en-CA": "travelled", "en-AU": "travelled", "en-NZ": "travelled"},
    {"en-US": "labeled", "en-GB": "labelled", "en-CA": "labelled", "en-AU": "labelled", "en-NZ": "labelled"},
    {"en-US": "modeling", "en-GB": "modelling", "en-CA": "modelling", "en-AU": "modelling", "en-NZ": "modelling"},
    {"en-US": "enrollment", "en-GB": "enrolment", "en-CA": "enrolment", "en-AU": "enrolment", "en-NZ": "enrolment"},
    {"en-US": "fulfill", "en-GB": "fulfil", "en-CA": "fulfil", "en-AU": "fulfil", "en-NZ": "fulfil"},
    # -og / -ogue
    {"en-US": "catalog", "en-GB": "catalogue", "en-CA": "catalogue", "en-AU": "catalogue", "en-NZ": "catalogue"},
    {"en-US": "analog", "en-GB": "analogue", "en-CA": "analogue", "en-AU": "analogue", "en-NZ": "analogue"},
    # misc
    {"en-US": "gray", "en-GB": "grey", "en-CA": "grey", "en-AU": "grey", "en-NZ": "grey"},
    # vocabulary
    {"en-US": "zip code", "en-GB": "postcode", "en-CA": "postal code", "en-AU": "postcode", "en-NZ": "postcode"},
]

LOCALES = ["en-US", "en-GB", "en-CA", "en-AU", "en-NZ"]
NO_PERIOD_HONORIFIC = {"en-GB", "en-AU", "en-NZ"}
HONORIFICS = ["Mr.", "Mrs.", "Ms.", "Dr.", "Prof."]

PROSE_HINTS = ("description", "desc", "subtitle", "subtext", "helper", "hint",
               "placeholder", "error", "message", "msg", "warning", "status",
               "toast", "caption", "summary", "intro", "body", "paragraph",
               "empty", "explain", "detail", "note", "disclaimer", "banner")
CHECKBOX_HINTS = ("checkbox", "radio", "switch", "toggle", "consent", "optin",
                  "opt_in", "agree", "terms")
LABEL_HINTS = ("label", "field", "input", "form")
CHROME_HINTS = ("button", "btn", "cta", "action", "submit", "confirm", "cancel",
                "title", "heading", "header", "nav", "tab", "menu", "link",
                "column", "col", "toolbar", "breadcrumb", "step", "card")

PLACEHOLDER_RE = re.compile(r"%\d*\$?[sdf]|%\([^)]*\)s")
NON_ENGLISH_RE = re.compile(
    r"^(?!en([-_][a-z]{2,4})?$)([a-z]{2})([-_][a-z]{2,4})?$")
TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
US_DATE_RE = re.compile(r"\bMM/DD/(YY|YYYY)\b|\bM/D/(YY|YYYY)\b")
INTL_DATE_RE = re.compile(r"\bDD/MM/(YY|YYYY)\b|\bD/M/(YY|YYYY)\b")

SEVERITY_ORDER = {"error": 0, "warn": 1, "info": 2}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def strip_braces(text):
    """Drop balanced {...} groups, nesting included.

    ICU plural and select forms nest: `{n, plural, one {# file} other {# files}}`.
    A non-greedy regex stops at the first inner `}` and leaves `other }` behind,
    which then reads as real words. Match depth instead.
    """
    out = []
    depth = 0
    for ch in text:
        if ch == "{":
            depth += 1
        elif ch == "}":
            if depth:
                depth -= 1
                out.append(" ")
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def clean(text):
    """Strip placeholders, tags, and markdown link targets."""
    text = MD_LINK_RE.sub(r"\1", text)
    text = strip_braces(text)
    text = PLACEHOLDER_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def known_acronym(c, allow):
    """Listed acronym, not merely a word in capitals."""
    return c in ACRONYMS or c in allow or c.lower() in allow


def all_known_acronyms(text, allow):
    ws = [core(w) for w in words_of(text)]
    ws = [w for w in ws if w]
    return bool(ws) and all(known_acronym(w, allow) for w in ws)


def is_english_source(path):
    """False for locale files of other languages (fr.json, pt_BR.yml)."""
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    return not NON_ENGLISH_RE.match(stem)


def core(word):
    return word.strip("\"'“”‘’()[]{}.,;:!?…·|/\\-–—")


def words_of(text):
    return [w for w in clean(text).split() if core(w)]


def is_acronym(c, allow):
    return (c.isupper() and len(c) > 1) or c in ACRONYMS or c in allow


def has_inner_caps(c):
    """iPhone, eBay, GitHub, macOS: casing the brand owns."""
    return len(c) > 1 and any(ch.isupper() for ch in c[1:])


def minor_words(style):
    """Words that stay lowercase mid-title, per standard."""
    if style in ("apple", "chicago18"):
        return ARTICLES | COORD_CONJ | SHORT_PREPS | {"as"}
    if style == "chicago17":
        return ARTICLES | COORD_CONJ | SHORT_PREPS | LONG_PREPS | {"as"}
    if style in ("ap", "apa"):
        return {w for w in (ARTICLES | COORD_CONJ | SHORT_PREPS | {"as"}) if len(w) <= 3}
    raise ValueError("unknown title style: %s" % style)


def stems(word):
    """Candidate base forms, so Logging In reads as a phrasal verb like Log In."""
    w = word.lower()
    out = {w}
    for suf in ("s", "es", "ed", "ing", "d"):
        if w.endswith(suf) and len(w) > len(suf) + 1:
            base = w[:-len(suf)]
            out.add(base)
            out.add(base + "e")
            if len(base) > 2 and base[-1] == base[-2]:
                out.add(base[:-1])
    return out


def is_particle(words, i):
    if i == 0:
        return False
    return (bool(stems(core(words[i - 1])) & PARTICLE_VERBS)
            and core(words[i]).lower() in PARTICLES)


def title_case_errors(text, style, allow):
    """Return list of words capitalized wrongly for title case."""
    ws = words_of(text)
    minor = minor_words(style)
    bad = []
    for i, w in enumerate(ws):
        c = core(w)
        if not c or c[0].isdigit() or is_acronym(c, allow) or has_inner_caps(c):
            continue
        if c.lower() in allow:
            continue
        first_or_last = i == 0 or i == len(ws) - 1
        want_upper = first_or_last or c.lower() not in minor or is_particle(ws, i)
        if want_upper and not c[0].isupper():
            bad.append((c, "should be capitalized"))
        elif not want_upper and c[0].isupper():
            bad.append((c, "should be lowercase"))
    return bad


def sentence_case_errors(text, proper, allow):
    """Return list of words capitalized wrongly for sentence case.

    A word opening a new sentence may be capitalized, so multi-sentence
    prose passes.
    """
    ws = words_of(text)
    bad = []
    opens_sentence = True
    for i, w in enumerate(ws):
        c = core(w)
        starts = opens_sentence
        trimmed = w.rstrip("\"'”’)")
        opens_sentence = (trimmed.endswith((".", "!", "?", ":"))
                          and trimmed.lower() not in ABBREVIATIONS
                          and len(trimmed.rstrip(".")) > 1)
        if not c or c[0].isdigit() or is_acronym(c, allow) or has_inner_caps(c):
            continue
        low = c.lower()
        if low in proper or low in allow:
            continue
        if starts:
            if c[0].islower():
                bad.append((c, "should be capitalized" if i else
                            "first word should be capitalized"))
        elif c[0].isupper():
            bad.append((c, "should be lowercase"))
    return bad


def looks_title_case(text, style, allow):
    ws = words_of(text)
    if len(ws) < 2:
        return False
    return not title_case_errors(text, style, allow)


def looks_sentence_case(text, allow):
    ws = words_of(text)
    if not ws:
        return False
    caps = [core(w) for w in ws[1:]
            if core(w) and core(w)[0].isupper()
            and not is_acronym(core(w), allow) and not has_inner_caps(core(w))]
    return core(ws[0])[:1].isupper() and not caps


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------

def _hint_kind(key):
    for hint in CHECKBOX_HINTS:
        if hint in key:
            return "checkbox"
    for hint in PROSE_HINTS:
        if hint in key:
            return "prose"
    for hint in LABEL_HINTS:
        if hint in key:
            return "label"
    for hint in CHROME_HINTS:
        if hint in key:
            return "chrome"
    return "unknown"


def classify_key(keypath):
    """Element type from the message ID alone, ignoring the string's shape.

    The last segment wins: in `billing.banner.title` the element is a title
    that happens to sit in a banner, not banner prose.
    """
    segments = [s for s in re.split(r"[^a-zA-Z0-9]+", keypath.lower()) if s]
    if segments:
        kind = _hint_kind(segments[-1])
        if kind != "unknown":
            return kind
    return _hint_kind(keypath.lower())


def classify(keypath, text):
    """Return 'prose', 'checkbox', 'label', 'chrome', or 'unknown'.

    Shape wins over the key: a sentence is a sentence wherever it lives.
    """
    stripped = clean(text)
    if not stripped:
        return "unknown"
    if stripped[-1] in ".!?:" and not stripped.endswith("..."):
        return "prose"
    if len(stripped.split()) > 6:
        return "prose"
    return classify_key(keypath)


def expected_case(kind, mode, label_variant):
    if kind in ("prose", "checkbox"):
        return "sentence"
    if mode == "sentence":
        return "sentence"
    if kind == "label":
        if mode == "hybrid":
            return label_variant
        return "title"
    if kind == "chrome":
        return "title"
    return None  # unknown: reported, not judged


# --------------------------------------------------------------------------
# Input
# --------------------------------------------------------------------------

def walk_json(node, prefix, out):
    if isinstance(node, dict):
        for k, v in node.items():
            walk_json(v, "%s.%s" % (prefix, k) if prefix else str(k), out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk_json(v, "%s[%d]" % (prefix, i), out)
    elif isinstance(node, str):
        out.append((prefix, node))


def load(paths, use_stdin):
    """Return list of (source, keypath, text)."""
    items = []
    if use_stdin:
        for i, line in enumerate(sys.stdin.read().splitlines(), 1):
            if line.strip():
                items.append(("<stdin>", "line%d" % i, line.strip()))
        return items
    for pattern in paths:
        matches = glob.glob(pattern, recursive=True) or ([pattern] if os.path.exists(pattern) else [])
        if not matches:
            print("warning: no files matched %s" % pattern, file=sys.stderr)
        for path in matches:
            if os.path.isdir(path):
                continue
            with open(path, "r", encoding="utf-8") as fh:
                raw = fh.read()
            if not is_english_source(path):
                print("note: %s looks like a non-English locale file. Case rules "
                      "are English rules, so only the neutral checks run on it."
                      % path, file=sys.stderr)
            if path.endswith(".json"):
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError as exc:
                    print("warning: %s is not valid JSON (%s)" % (path, exc), file=sys.stderr)
                    continue
                found = []
                walk_json(data, "", found)
                items.extend((path, k, v) for k, v in found)
            elif path.endswith((".yml", ".yaml")):
                try:
                    import yaml  # optional, not stdlib
                except ImportError:
                    print("warning: %s needs PyYAML (pip install pyyaml). Skipped."
                          % path, file=sys.stderr)
                    continue
                try:
                    data = yaml.safe_load(raw)
                except yaml.YAMLError as exc:
                    print("warning: %s is not valid YAML (%s)" % (path, exc), file=sys.stderr)
                    continue
                found = []
                walk_json(data, "", found)
                items.extend((path, k, v) for k, v in found)
            else:
                for i, line in enumerate(raw.splitlines(), 1):
                    if line.strip():
                        items.append((path, "line%d" % i, line.strip()))
    return items


def learn_proper_nouns(items, allow):
    """Words capitalized mid-string across prose entries are probably names.

    A backstop, not a guarantee: a brand that only ever opens a string is
    invisible here. Pass --allow with the project's brand list.
    """
    seen = defaultdict(lambda: [0, 0])  # lower -> [capitalized, total]
    for _, key, text in items:
        if classify(key, text) != "prose":
            continue
        ws = words_of(text)
        for w in ws[1:]:
            c = core(w)
            if not c or c[0].isdigit() or is_acronym(c, allow) or has_inner_caps(c):
                continue
            rec = seen[c.lower()]
            rec[1] += 1
            if c[0].isupper():
                rec[0] += 1
    return {w for w, (cap, total) in seen.items() if total >= 2 and cap / total >= 0.8}


# --------------------------------------------------------------------------
# Locale checks
# --------------------------------------------------------------------------

def inflect(base):
    """Cheap inflection set for a base word or two-word phrase."""
    if " " in base:
        return {base, base + "s"}
    forms = {base, base + "s", base + "es", base + "ing", base + "ed",
             base + "d", base + "r", base + "rs"}
    if base.endswith("e"):
        stem = base[:-1]
        forms |= {stem + "ing", stem + "ed", stem + "es"}
    if base.endswith("y"):
        forms.add(base[:-1] + "ies")
    return forms


def spelling_map(locale):
    """Map wrong form -> preferred form for the target locale."""
    out = {}
    for row in SPELLING:
        want = row[locale]
        for loc in LOCALES:
            other = row[loc]
            if other == want:
                continue
            for form in inflect(other):
                if form not in inflect(want):
                    out.setdefault(form, want)
    return out


def locale_findings(text, locale, spell):
    found = []
    lowered = clean(text).lower()
    for wrong, right in spell.items():
        if " " in wrong:
            if wrong in lowered:
                found.append(("warn", "locale-spelling",
                              "%s is not %s, use %s" % (wrong, locale, right)))
            continue
        for w in words_of(text):
            if core(w).lower() == wrong:
                found.append(("warn", "locale-spelling",
                              "%s is not %s, use %s" % (core(w), locale, right)))
    if locale in NO_PERIOD_HONORIFIC:
        for h in HONORIFICS:
            if h in text:
                found.append(("info", "locale-punctuation",
                              "%s takes no period in %s" % (h, locale)))
    if locale == "en-US":
        if INTL_DATE_RE.search(text):
            found.append(("warn", "locale-date", "day-first date format in en-US"))
    elif US_DATE_RE.search(text):
        found.append(("warn", "locale-date", "month-first date format in %s" % locale))
    return found


# --------------------------------------------------------------------------
# Main checks
# --------------------------------------------------------------------------

def detect_mode(items, style, allow):
    counts = {"chrome_title": 0, "chrome_sentence": 0,
              "label_title": 0, "label_sentence": 0, "prose": 0, "unknown": 0}
    for _, key, text in items:
        kind = classify(key, text)
        if kind == "prose":
            counts["prose"] += 1
            continue
        if kind == "unknown":
            counts["unknown"] += 1
            continue
        bucket = "chrome" if kind == "chrome" else "label"
        if looks_title_case(text, style, allow):
            counts[bucket + "_title"] += 1
        elif looks_sentence_case(text, allow):
            counts[bucket + "_sentence"] += 1
    return counts


def check(items, mode, locale, style, label_variant, allow):
    findings = []
    proper = learn_proper_nouns(items, allow)
    spell = spelling_map(locale) if locale else {}

    # duplicate casings of the same string
    variants = defaultdict(set)
    for _, _, text in items:
        stripped = clean(text)
        if stripped:
            variants[stripped.lower()].add(stripped)
    for low, forms in sorted(variants.items()):
        if len(forms) > 1:
            findings.append({
                "severity": "error", "rule": "duplicate-casing",
                "source": "-", "key": "-", "text": " | ".join(sorted(forms)),
                "detail": "same string shipped in %d casings" % len(forms),
            })

    for source, key, text in items:
        stripped = clean(text)
        if not stripped:
            continue
        kind = classify(key, text)
        row = {"source": source, "key": key, "text": text}

        if stripped.isupper() and len(stripped) > 3 \
                and not all_known_acronyms(text, allow):
            findings.append(dict(row, severity="error", rule="all-caps",
                                 detail="use CSS text-transform, keep the source cased"))

        stray_period = (classify_key(key) in ("chrome", "label", "checkbox")
                        and stripped.endswith(".") and not stripped.endswith("..."))
        if stray_period:
            findings.append(dict(row, severity="error", rule="trailing-period",
                                 detail="controls and labels take no final period"))

        # A stray period demoted this string to prose, so its case verdict
        # would be wrong. Drop the period and re-run instead. Case rules are
        # English rules, so other languages get the neutral checks only.
        want = None if (stray_period or not is_english_source(source)) \
            else expected_case(kind, mode, label_variant)
        if want == "title":
            bad = title_case_errors(text, style, allow)
            if bad:
                findings.append(dict(row, severity="error", rule="title-case",
                                     detail="; ".join("%s %s" % (w, why) for w, why in bad)))
        elif want == "sentence":
            bad = sentence_case_errors(text, proper, allow)
            if bad:
                findings.append(dict(row, severity="error", rule="sentence-case",
                                     detail="; ".join("%s %s" % (w, why) for w, why in bad)))
        elif kind == "unknown" and is_english_source(source):
            findings.append(dict(row, severity="info", rule="unclassified",
                                 detail="key gives no element type, review by hand"))

        for sev, rule, detail in locale_findings(text, locale, spell) if locale else []:
            findings.append(dict(row, severity=sev, rule=rule, detail=detail))

    findings.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], f["rule"], f["source"], f["key"]))
    return findings


def report(findings, counts, total, as_json, quiet):
    if as_json:
        print(json.dumps({"scanned": total, "distribution": counts,
                          "findings": findings}, indent=2, ensure_ascii=False))
        return
    by_rule = defaultdict(int)
    for f in findings:
        by_rule[f["rule"]] += 1
    if counts:
        print("Distribution")
        for k, v in counts.items():
            print("  %-18s %d" % (k, v))
        print()
    if not quiet:
        for f in findings:
            print("[%s] %s  %s:%s" % (f["severity"], f["rule"], f["source"], f["key"]))
            print("    %s" % f["text"])
            print("    %s" % f["detail"])
    print("\nScanned %d strings, %d findings" % (total, len(findings)))
    for rule, n in sorted(by_rule.items(), key=lambda kv: -kv[1]):
        print("  %-18s %d" % (rule, n))


def main(argv=None):
    p = argparse.ArgumentParser(description="Audit UI strings for capitalization consistency.")
    p.add_argument("paths", nargs="*",
                   help="JSON or YAML i18n files, text files, or globs")
    p.add_argument("--stdin", action="store_true", help="read newline-delimited strings")
    p.add_argument("--mode", choices=["sentence", "hybrid", "title"], help="target mode")
    p.add_argument("--detect", action="store_true", help="report the current split, judge nothing")
    p.add_argument("--locale", choices=LOCALES, help="target regional English")
    p.add_argument("--title-style", default="apple",
                   choices=["apple", "chicago18", "chicago17", "ap", "apa"])
    p.add_argument("--label-variant", default="sentence", choices=["sentence", "title"],
                   help="mode hybrid: casing for form field labels")
    p.add_argument("--allow", help="file of terms to leave alone, one per line")
    p.add_argument("--json", action="store_true", dest="as_json")
    p.add_argument("--quiet", action="store_true", help="summary only")
    p.add_argument("--strict", action="store_true",
                   help="exit 1 on warnings too (locale spelling, punctuation)")
    args = p.parse_args(argv)

    if not args.paths and not args.stdin:
        p.error("give paths or --stdin")
    if not args.mode and not args.detect:
        p.error("give --mode or --detect")

    allow = set()
    if args.allow:
        with open(args.allow, "r", encoding="utf-8") as fh:
            allow = {ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")}
        allow |= {a.lower() for a in allow}

    items = load(args.paths, args.stdin)
    if not items:
        print("no strings found", file=sys.stderr)
        return 2

    if args.detect:
        counts = detect_mode(items, args.title_style, allow)
        chrome_total = counts["chrome_title"] + counts["chrome_sentence"]
        report([], counts, len(items), args.as_json, args.quiet)
        if chrome_total:
            share = counts["chrome_title"] / chrome_total
            verdict = ("title-first" if share > 0.7 else
                       "sentence-first" if share < 0.3 else "split, decide")
            print("\nChrome strings lean: %s (%.0f%% title case)" % (verdict, share * 100))
        return 0

    findings = check(items, args.mode, args.locale, args.title_style,
                     args.label_variant, allow)
    report(findings, None, len(items), args.as_json, args.quiet)
    fails = {"error", "warn"} if args.strict else {"error"}
    return 1 if any(f["severity"] in fails for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
