#!/usr/bin/env python3
"""Validate architecture specs in registry/architectures/ against the spec schema.

Checks: frontmatter keys/types, unique ids matching filenames, layer graph
(references exist, acyclic), required body sections, no private-data hints.
Requires PyYAML (pip install pyyaml). Exit 1 on any error.
"""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry" / "architectures"
REQUIRED_KEYS = {"id", "name", "version", "status", "summary", "tags", "layers"}
STATUSES = {"draft", "stable"}
REQUIRED_SECTIONS = [
    "Intent",
    "Layers & Responsibilities",
    "Dependency Rules",
    "Conventions",
    "Request / Data Flow",
    "Anti-patterns",
    "Detection Hints",
    "Planning Checklist",
    "Refactoring Playbook",
]
LAYER_KEYS = {"id", "responsibility", "may_depend_on"}
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# Registry specs are public; flag things that look like private project data.
PRIVATE_HINTS = re.compile(r"(/home/\w+|C:\\Users\\|[\w.+-]+@(?!example\.)[\w-]+\.\w+)")


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    return (m.group(1), m.group(2)) if m else (None, text)


def find_cycle(graph):
    state = {}

    def visit(n, path):
        state[n] = 1
        for m in graph.get(n, []):
            if state.get(m) == 1:
                return path + [n, m]
            if m not in state:
                c = visit(m, path + [n])
                if c:
                    return c
        state[n] = 2
        return None

    for n in graph:
        if n not in state:
            c = visit(n, [])
            if c:
                return c
    return None


def validate(path, seen_ids):
    errs = []
    fm_text, body = split_frontmatter(path.read_text(encoding="utf-8"))
    if fm_text is None:
        return [f"{path.name}: missing YAML frontmatter"]
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        return [f"{path.name}: invalid YAML: {e}"]
    if not isinstance(fm, dict):
        return [f"{path.name}: frontmatter must be a mapping"]

    missing = REQUIRED_KEYS - fm.keys()
    if missing:
        errs.append(f"{path.name}: missing keys {sorted(missing)}")
        return errs

    sid = fm["id"]
    if not isinstance(sid, str) or not SLUG.match(sid):
        errs.append(f"{path.name}: id must be a lowercase slug")
    elif sid != path.stem:
        errs.append(f"{path.name}: id '{sid}' must equal filename stem '{path.stem}'")
    if sid in seen_ids:
        errs.append(f"{path.name}: duplicate id '{sid}'")
    seen_ids.add(sid)
    if not SEMVER.match(str(fm["version"])):
        errs.append(f"{path.name}: version must be semver (x.y.z)")
    if fm["status"] not in STATUSES:
        errs.append(f"{path.name}: status must be one of {sorted(STATUSES)}")
    if not isinstance(fm["tags"], list) or not all(isinstance(t, str) for t in fm["tags"]):
        errs.append(f"{path.name}: tags must be a list of strings")

    layers = fm["layers"]
    if not isinstance(layers, list) or not layers:
        errs.append(f"{path.name}: layers must be a non-empty list")
        return errs
    ids = []
    for i, layer in enumerate(layers):
        if not isinstance(layer, dict) or not LAYER_KEYS <= layer.keys():
            errs.append(f"{path.name}: layers[{i}] needs keys {sorted(LAYER_KEYS)}")
            continue
        ids.append(layer["id"])
    if len(ids) != len(set(ids)):
        errs.append(f"{path.name}: duplicate layer ids")
    graph = {}
    for layer in layers:
        if not isinstance(layer, dict) or "id" not in layer:
            continue
        deps = layer.get("may_depend_on") or []
        graph[layer["id"]] = deps
        for d in deps:
            if d not in ids:
                errs.append(f"{path.name}: layer '{layer['id']}' depends on unknown layer '{d}'")
            if d == layer["id"]:
                errs.append(f"{path.name}: layer '{d}' depends on itself")
    cyc = find_cycle(graph)
    if cyc:
        errs.append(f"{path.name}: dependency cycle {' -> '.join(cyc)}")

    headings = {h.strip() for h in re.findall(r"^##\s+(.+)$", body, re.M)}
    for sec in REQUIRED_SECTIONS:
        if sec not in headings:
            errs.append(f"{path.name}: missing section '## {sec}'")

    m = PRIVATE_HINTS.search(path.read_text(encoding="utf-8"))
    if m:
        errs.append(f"{path.name}: looks like private data: '{m.group(0)}' (use example.* / placeholders)")
    return errs


def main():
    specs = sorted(p for p in REGISTRY.glob("*.md") if p.name.lower() != "readme.md")
    if not specs:
        sys.exit("validate-registry: no specs found")
    seen, errors = set(), []
    for p in specs:
        errors += validate(p, seen)
    if errors:
        print("\n".join(f"✗ {e}" for e in errors))
        sys.exit(1)
    print(f"✓ validate-registry: {len(specs)} specs OK ({', '.join(sorted(seen))})")


if __name__ == "__main__":
    main()
