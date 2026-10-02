#!/usr/bin/env python3
"""Repo lint: every SKILL.md must have parseable frontmatter and the house keys."""
import glob, os, sys, yaml

REQUIRED = ["name", "version", "description", "author", "license", "triggers", "mutating"]
fails = []
for f in sorted(glob.glob("*/SKILL.md")):
    skill = os.path.dirname(f)
    try:
        fm = yaml.safe_load(open(f).read().split("---")[1])
    except Exception as e:
        fails.append(f"{skill}: frontmatter does not parse ({str(e).splitlines()[0]})")
        continue
    if not isinstance(fm, dict):
        fails.append(f"{skill}: frontmatter must be a mapping")
        continue
    metadata = fm.get("metadata", {})
    if not isinstance(metadata, dict):
        fails.append(f"{skill}: metadata must be a mapping")
        metadata = {}
    nested_house_keys = all(k in metadata for k in ("version", "author", "mutating"))
    for k in REQUIRED:
        if k == "triggers" and nested_house_keys:
            continue
        if k not in fm and not (k in ("version", "author", "mutating") and k in metadata):
            fails.append(f"{skill}: missing required key '{k}'")
    if fm.get("name") != skill:
        fails.append(f"{skill}: name '{fm.get('name')}' does not match directory")
    d = str(fm.get("description", ""))
    if not d.lower().startswith("use when"):
        fails.append(f"{skill}: description should start with 'Use when'")
    if ("triggers" in fm or not nested_house_keys) and (not isinstance(fm.get("triggers"), list) or not fm["triggers"]):
        fails.append(f"{skill}: triggers must be a non-empty list")

print(f"checked {len(glob.glob('*/SKILL.md'))} skills")
for x in fails:
    print("FAIL:", x)
sys.exit(1 if fails else 0)
