#!/usr/bin/env python3
"""Tests for capcheck. Run: python3 tests/test_capcheck.py (or with pytest)."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import capcheck as cc  # noqa: E402

ALLOW = set()


def title_ok(text, style="apple"):
    return cc.title_case_errors(text, style, ALLOW) == []


# -- title case, Apple Style Guide examples ---------------------------------

def test_apple_examples_pass():
    for text in ["Log In to the Server", "Start Up the Computer", "Turn On Apple Watch",
                 "What to Do If Your iPhone Is Lost", "Export a Document as a PDF",
                 "Skip This Backup", "Apple News Is Offline", "High-Level Events",
                 "Save As", "Go To", "Always on Top", "Paste Link"]:
        assert title_ok(text), "%s should be valid Apple title case" % text


def test_inflected_phrasal_verbs():
    # Apple's own examples use gerunds, not base forms.
    for text in ["Logging In to the Server", "Starting Up the Computer",
                 "Getting Started with Your MacBook Pro", "Signing Out of Your Account",
                 "Backing Up Your Data", "Shutting Down the Server"]:
        assert title_ok(text), "%s should be valid Apple title case" % text
    assert not title_ok("Logging in to the Server")
    assert not title_ok("Backing up Your Data")


def test_broken_title_case_is_caught():
    bad = cc.title_case_errors("A Great Tool With The Twist But Not Without Its Own Quirks",
                               "apple", ALLOW)
    flagged = {w.lower() for w, _ in bad}
    assert {"with", "the", "but"} <= flagged
    assert "without" not in flagged  # 7 letters, capitalized under Apple


def test_chicago17_lowercases_long_prepositions():
    text = "A Great Tool with the Twist but Not Without Its Own Quirks"
    assert title_ok(text, "apple")
    assert title_ok(text, "chicago18")
    bad = cc.title_case_errors(text, "chicago17", ALLOW)
    assert [w.lower() for w, _ in bad] == ["without"]


def test_phrasal_verb_particle_must_be_capitalized():
    assert not title_ok("Log in")
    assert title_ok("Log In")
    assert not title_ok("Sign up")
    assert title_ok("Sign Up")


def test_ap_capitalizes_four_letter_prepositions():
    assert title_ok("Share With Your Team", "ap")
    assert not title_ok("Share With Your Team", "apple")


# -- sentence case ----------------------------------------------------------

def test_sentence_case():
    assert cc.sentence_case_errors("Enter your email to reset password", set(), ALLOW) == []
    bad = cc.sentence_case_errors("Enter Your Email", set(), ALLOW)
    assert {w for w, _ in bad} == {"Your", "Email"}


def test_sentence_case_keeps_brands_and_acronyms():
    assert cc.sentence_case_errors("Upload a PDF to GitHub from your iPhone",
                                   set(), ALLOW) == []


def test_learned_proper_nouns_are_not_flagged():
    items = [("f", "a.description", "Ask Northwind for a summary."),
             ("f", "b.description", "Your Northwind report is ready."),
             ("f", "c.description", "Send it to Northwind when you finish.")]
    proper = cc.learn_proper_nouns(items, ALLOW)
    assert "northwind" in proper
    assert cc.sentence_case_errors("Open Northwind now", proper, ALLOW) == []


def test_brand_only_ever_first_needs_the_allowlist():
    items = [("f", "a.description", "Northwind reads your report.")]
    proper = cc.learn_proper_nouns(items, ALLOW)
    assert "northwind" not in proper  # one mid-string sighting is not evidence
    assert cc.sentence_case_errors("Open Northwind now", proper, {"northwind"}) == []


# -- placeholder and acronym handling ---------------------------------------

def test_icu_plural_and_select_are_stripped_whole():
    # Nested braces: a non-greedy regex leaves "other }" behind as real words.
    assert cc.clean("{count, plural, one {# document} other {# documents}} Ready") \
        == "Ready"
    assert cc.clean("{gender, select, male {He} female {She} other {They}} replied") \
        == "replied"
    assert cc.clean("You have {count, plural, one {1 item} other {# items}} left") \
        == "You have left"


def test_icu_string_gets_no_phantom_findings():
    items = [("f", "a.description", "You have {n, plural, one {1 file} other {# files}} left")]
    assert run(items, mode="hybrid") == []


def test_simple_placeholders_still_strip():
    assert cc.clean("Hello {name}, you have %d messages") == "Hello , you have messages"


def test_acronym_only_string_is_not_all_caps_noise():
    items = [("f", "a.label", "PDF, CSV"), ("f", "b.button", "SAVE CHANGES")]
    found = [f for f in run(items) if f["rule"] == "all-caps"]
    assert len(found) == 1 and found[0]["text"] == "SAVE CHANGES"


# -- non-English sources ----------------------------------------------------

def test_non_english_source_detection():
    assert cc.is_english_source("locales/en.json")
    assert cc.is_english_source("locales/en-GB.json")
    assert cc.is_english_source("src/messages.json")
    assert not cc.is_english_source("locales/fr.json")
    assert not cc.is_english_source("locales/pt_BR.yml")


def test_non_english_file_skips_case_rules_keeps_neutral_ones():
    items = [("locales/fr.json", "a.button", "Créer Un Compte"),
             ("locales/fr.json", "b.button", "ENVOYER MAINTENANT")]
    found = rules(run(items, mode="sentence"))
    assert "sentence-case" not in found  # English rules do not apply
    assert "all-caps" in found           # language neutral


# -- classification ---------------------------------------------------------

def test_classify():
    assert cc.classify("form.firstName.label", "First name") == "label"
    assert cc.classify("errors.network.message", "Could not connect") == "prose"
    assert cc.classify("actions.submit.button", "Save Changes") == "chrome"
    assert cc.classify("settings.notify.checkbox", "Email me updates") == "checkbox"
    assert cc.classify("random.key", "Save") == "unknown"
    assert cc.classify("actions.save.button", "Save your work before you go.") == "prose"
    assert cc.classify("nav.tab", "Reports and analytics for the whole team") == "prose"


def test_key_last_segment_wins():
    # A banner title is a title, not banner prose.
    assert cc.classify("billing.banner.title", "Payment Required") == "chrome"
    assert cc.classify("billing.banner.description", "Pick a plan") == "prose"
    assert cc.classify("card.header.button", "Add Item") == "chrome"


def test_multi_sentence_prose_passes():
    text = "Your documents and settings are saved. Pick a plan to continue."
    assert cc.sentence_case_errors(text, set(), ALLOW) == []


def test_abbreviation_does_not_open_a_sentence():
    text = "Use a CSV file, e.g. export.csv, to import your data"
    assert cc.sentence_case_errors(text, set(), ALLOW) == []


def test_trailing_period_suppresses_case_verdict():
    items = [("f", "a.button", "Cancel Subscription.")]
    found = rules(run(items, mode="hybrid"))
    assert found == {"trailing-period"}


def test_trailing_period_still_reports_locale():
    items = [("f", "a.button", "Customize Colors.")]
    found = rules(run(items, mode="hybrid", locale="en-GB"))
    assert "trailing-period" in found and "locale-spelling" in found


def test_expected_case_by_mode():
    assert cc.expected_case("chrome", "sentence", "sentence") == "sentence"
    assert cc.expected_case("chrome", "hybrid", "sentence") == "title"
    assert cc.expected_case("label", "hybrid", "sentence") == "sentence"
    assert cc.expected_case("label", "hybrid", "title") == "title"
    assert cc.expected_case("checkbox", "title", "title") == "sentence"


# -- corpus checks ----------------------------------------------------------

def run(items, mode="hybrid", locale=None, style="apple", variant="sentence"):
    return cc.check(items, mode, locale, style, variant, ALLOW)


def rules(findings):
    return {f["rule"] for f in findings}


def test_duplicate_casing():
    items = [("f", "a.button", "Log In"), ("f", "b.button", "Log in")]
    assert "duplicate-casing" in rules(run(items))


def test_all_caps_and_trailing_period():
    items = [("f", "a.button", "SAVE CHANGES"), ("f", "b.button", "Save Changes.")]
    found = rules(run(items))
    assert "all-caps" in found
    assert "trailing-period" in found


def test_mode_sentence_flags_title_case_button():
    items = [("f", "a.button", "Create New Case")]
    assert "sentence-case" in rules(run(items, mode="sentence"))


def test_mode_hybrid_accepts_split():
    items = [("f", "a.button", "Create New Case"),
             ("f", "b.description", "Upload a report to get started")]
    assert not [f for f in run(items) if f["severity"] == "error"]


# -- locale -----------------------------------------------------------------

def test_locale_spelling():
    items = [("f", "a.description", "Customize your colors")]
    detail = " ".join(f["detail"] for f in run(items, locale="en-GB"))
    assert "customise" in detail and "colour" in detail


def test_canadian_keeps_ize_and_takes_our():
    items = [("f", "a.description", "Organize your colors")]
    detail = " ".join(f["detail"] for f in run(items, locale="en-CA"))
    assert "colour" in detail
    assert "organise" not in detail


def test_australian_takes_ise():
    items = [("f", "a.description", "Organize your files")]
    detail = " ".join(f["detail"] for f in run(items, locale="en-AU"))
    assert "organise" in detail


def test_honorific_period():
    items = [("f", "a.description", "Contact Dr. Smith")]
    assert "locale-punctuation" in rules(run(items, locale="en-GB"))
    assert "locale-punctuation" not in rules(run(items, locale="en-US"))


def test_zip_code_vocabulary():
    items = [("f", "a.label", "Zip code")]
    detail = " ".join(f["detail"] for f in run(items, locale="en-AU"))
    assert "postcode" in detail


# -- end to end -------------------------------------------------------------

def test_strict_promotes_warnings_to_failure():
    data = {"settings": {"a": {"description": "Customize your colors"}}}
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "en.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        assert cc.main(["--mode", "sentence", "--locale", "en-GB", "--quiet", path]) == 0
        assert cc.main(["--mode", "sentence", "--locale", "en-GB", "--strict",
                        "--quiet", path]) == 1


def test_main_exit_codes():
    clean = {"actions": {"save": {"button": "Save Changes"}},
             "errors": {"network": {"message": "We could not reach the server"}}}
    dirty = {"actions": {"save": {"button": "Save changes"},
                         "other": {"button": "Save Changes"}}}
    with tempfile.TemporaryDirectory() as tmp:
        good = os.path.join(tmp, "good.json")
        bad = os.path.join(tmp, "bad.json")
        for path, data in ((good, clean), (bad, dirty)):
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
        assert cc.main(["--mode", "hybrid", "--quiet", good]) == 0
        assert cc.main(["--mode", "hybrid", "--quiet", bad]) == 1
        assert cc.main(["--detect", "--quiet", good]) == 0


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("pass  %s" % name)
            except AssertionError as exc:
                failures += 1
                print("FAIL  %s  %s" % (name, exc))
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print("ERROR %s  %s: %s" % (name, type(exc).__name__, exc))
    print("\n%d failure(s)" % failures)
    sys.exit(1 if failures else 0)
