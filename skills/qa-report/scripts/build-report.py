#!/usr/bin/env python3
"""Render a QA report (Markdown, optional .docx) from a qa-results YAML file.

  build-report.py check  RESULTS.yaml                  validate the data; exit 1 on errors
  build-report.py render RESULTS.yaml [--out F.md] [--docx] [--full]

Metrics, the auth matrix and defect tables are computed from the data, never hand-counted.
Every string is passed through redact.py before it is written. The .docx writer has no
dependencies (pure OOXML). Requires PyYAML.
"""
import argparse
import re
import sys
import zipfile
from collections import Counter, OrderedDict
from pathlib import Path
from xml.sax.saxutils import escape

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from redact import redact  # noqa: E402

RESULTS = ("pass", "fail", "blocked", "skipped")
TYPES = ("success", "negative", "security")
SEVERITIES = ("critical", "high", "medium", "low", "info")
DEFECT_STATUS = ("open", "fixed", "wont_fix", "retest")
ENV_KINDS = ("local", "dev", "staging", "test", "production")
ID_RE = re.compile(r"^[A-Z]+-?\d+$")


# ───────────────────────── validation ─────────────────────────
def validate(d):
    errs, warns = [], []
    if not isinstance(d, dict):
        return ["top level must be a mapping"], []
    meta = d.get("meta") or {}
    for k in ("title", "project", "date", "tester"):
        if not meta.get(k):
            errs.append(f"meta.{k} is required")
    env = meta.get("environment") or {}
    for k in ("name", "kind", "target", "build"):
        if not env.get(k):
            errs.append(f"meta.environment.{k} is required")
    if env.get("kind") not in (None, *ENV_KINDS):
        errs.append(f"meta.environment.kind must be one of {ENV_KINDS}")
    if env.get("kind") == "production" and not env.get("authorization_note"):
        errs.append("production testing requires meta.environment.authorization_note (who authorized it, scope)")

    def ids(key, label):
        items = d.get(key) or []
        seen = []
        for i, it in enumerate(items):
            if not isinstance(it, dict) or not it.get("id"):
                errs.append(f"{label}[{i}] needs an id")
                continue
            if it["id"] in seen:
                errs.append(f"{label} duplicate id {it['id']}")
            seen.append(it["id"])
        return set(seen)

    actors, inv, scen, defs = ids("actors", "actors"), ids("inventory", "inventory"), ids("scenarios", "scenarios"), ids("defects", "defects")
    if not d.get("scenarios"):
        errs.append("no scenarios: a report needs executed evidence")

    for s in d.get("scenarios") or []:
        sid = s.get("id", "?")
        for k in ("module", "inventory", "type", "title", "actor", "expected", "actual", "result"):
            if not s.get(k):
                errs.append(f"{sid}: missing '{k}'")
        if s.get("type") not in TYPES:
            errs.append(f"{sid}: type must be one of {TYPES}")
        if s.get("result") not in RESULTS:
            errs.append(f"{sid}: result must be one of {RESULTS}")
        if s.get("inventory") and s["inventory"] not in inv:
            errs.append(f"{sid}: unknown inventory id {s['inventory']}")
        if s.get("actor") and s["actor"] not in actors:
            errs.append(f"{sid}: unknown actor {s['actor']}")
        if s.get("result") == "fail" and s.get("defect") not in defs:
            errs.append(f"{sid}: failing scenario must reference an existing defect")
        if s.get("defect") and s["defect"] not in defs:
            errs.append(f"{sid}: unknown defect {s['defect']}")
        if s.get("result") in ("pass", "fail") and not s.get("evidence"):
            errs.append(f"{sid}: executed scenarios need evidence (command/response excerpt)")
        az = s.get("authz")
        if az is not None and (az.get("expected") not in ("allow", "deny") or az.get("actual") not in ("allow", "deny")):
            errs.append(f"{sid}: authz.expected/actual must be allow|deny")

    by_def = Counter(s.get("defect") for s in d.get("scenarios") or [] if s.get("defect"))
    for x in d.get("defects") or []:
        did = x.get("id", "?")
        for k in ("title", "severity", "status", "description", "impact", "fix"):
            if not x.get(k):
                errs.append(f"{did}: missing '{k}'")
        if x.get("severity") not in SEVERITIES:
            errs.append(f"{did}: severity must be one of {SEVERITIES}")
        if x.get("status") not in DEFECT_STATUS:
            errs.append(f"{did}: status must be one of {DEFECT_STATUS}")
        if x.get("status") == "fixed" and not x.get("retest_evidence"):
            errs.append(f"{did}: fixed defects need retest_evidence")
        if not by_def.get(did):
            warns.append(f"{did}: no scenario references this defect")
    return errs, warns


# ───────────────────────── model → blocks ─────────────────────────
class Ctx:
    def __init__(self):
        self.redactions = 0

    def r(self, v):
        if v is None:
            return ""
        s = str(v).strip("\n")
        s, n = redact(s)
        self.redactions += n
        return s


def pct(n, d):
    return f"{(100.0 * n / d):.0f}%" if d else "n/a"


def build_blocks(d, full, ctx):
    r = ctx.r
    meta, env = d["meta"], d["meta"]["environment"]
    scen, defs = d["scenarios"], d.get("defects") or []
    inv = {i["id"]: i for i in d.get("inventory") or []}
    actors = d.get("actors") or []
    amap = {a["id"]: a for a in actors}
    dmap = {x["id"]: x for x in defs}
    B = []

    def H(n, t): B.append(("h", n, r(t)))
    def P(t): B.append(("p", r(t)))
    def UL(items): B.append(("ul", [r(i) for i in items]))
    def T(head, rows): B.append(("table", [r(h) for h in head], [[r(c) for c in row] for row in rows]))
    def C(t): B.append(("code", r(t)))

    B.append(("title", r(meta["title"])))
    P(f"**Project:** {meta['project']}  |  **Date:** {meta['date']}  |  **Tester:** {meta['tester']}  |  **Build:** {env['build']}")

    # 1. Executive summary + metrics
    H(1, "1. Executive Summary")
    if d.get("summary"):
        P(d["summary"])
    cnt = Counter(s["result"] for s in scen)
    executed = cnt["pass"] + cnt["fail"]
    open_defs = [x for x in defs if x["status"] in ("open", "retest")]
    verdict = "FAIL: open defects remain" if any(x["severity"] in ("critical", "high") for x in open_defs) else \
              ("PASS WITH ISSUES" if open_defs or cnt["fail"] or cnt["blocked"] else "PASS")
    P(f"**Overall verdict: {verdict}**")
    T(["Metric", "Value"], [
        ["Scenarios total", len(scen)], ["Passed", cnt["pass"]], ["Failed", cnt["fail"]],
        ["Blocked", cnt["blocked"]], ["Skipped", cnt["skipped"]],
        ["Pass rate (executed)", pct(cnt["pass"], executed)], ["Execution coverage", pct(executed, len(scen))],
        ["Endpoints/components in inventory", len(inv)],
        ["Defects open / fixed", f"{sum(x['status'] in ('open','retest') for x in defs)} / {sum(x['status']=='fixed' for x in defs)}"],
    ])
    by_type = OrderedDict((t, Counter(s["result"] for s in scen if s["type"] == t)) for t in TYPES)
    T(["Scenario type", "Total", "Pass", "Fail", "Blocked/Skipped", "Pass rate"],
      [[t, sum(c.values()), c["pass"], c["fail"], c["blocked"] + c["skipped"], pct(c["pass"], c["pass"] + c["fail"])] for t, c in by_type.items() if c])
    mods = OrderedDict()
    for s in scen:
        mods.setdefault(s["module"], Counter())[s["result"]] += 1
    T(["Module", "Total", "Pass", "Fail", "Blocked/Skipped", "Pass rate"],
      [[m, sum(c.values()), c["pass"], c["fail"], c["blocked"] + c["skipped"], pct(c["pass"], c["pass"] + c["fail"])] for m, c in mods.items()])
    sev = [[sv.title(), sum(1 for x in defs if x["severity"] == sv and x["status"] in ("open", "retest")),
            sum(1 for x in defs if x["severity"] == sv and x["status"] == "fixed"),
            sum(1 for x in defs if x["severity"] == sv and x["status"] == "wont_fix")] for sv in SEVERITIES]
    T(["Severity", "Open", "Fixed", "Won't fix"], [row for row in sev if any(row[1:])] or [["none", 0, 0, 0]])

    # 2. Scope
    H(1, "2. Scope")
    meta_scope = d.get("scope") or {}
    P("**In scope**")
    UL(meta_scope.get("in") or ["(not stated)"])
    P("**Out of scope**")
    UL(meta_scope.get("out") or ["(not stated)"])

    # 3. Environment, actors, fixtures
    H(1, "3. Environment & Test Actors/Fixtures")
    T(["Item", "Value"], [["Environment", env["name"]], ["Kind", env["kind"]], ["Target", env["target"]], ["Build / commit", env["build"]]]
      + [[k.replace("_", " ").title(), v] for k, v in env.items() if k not in ("name", "kind", "target", "build")])
    P("**Test actors** (credentials are never recorded in this report)")
    T(["ID", "Role", "Description", "Fixture/account (placeholder)"],
      [[a["id"], a.get("role", ""), a.get("description", ""), a.get("fixture", "")] for a in actors])
    if d.get("fixtures"):
        P("**Fixtures / seed data**")
        T(["ID", "Description"], [[f["id"], f.get("description", "")] for f in d["fixtures"]])

    # 4. Methodology
    H(1, "4. Methodology")
    P(d.get("methodology") or "Execution-based verification: each scenario was run against the target and the observed response recorded as evidence.")

    # 5. Inventory
    H(1, "5. Endpoint / Component Inventory")
    T(["ID", "Module", "Kind", "Name", "Method", "Path/Location", "Auth", "Scenarios"],
      [[i["id"], i.get("module", ""), i.get("kind", "endpoint"), i.get("name", ""), i.get("method", ""), i.get("path", ""),
        i.get("auth", ""), sum(1 for s in scen if s["inventory"] == i["id"])] for i in inv.values()])
    untested = [i["id"] for i in inv.values() if not any(s["inventory"] == i["id"] and s["result"] in ("pass", "fail") for s in scen)]
    if untested:
        P("**Not executed:** " + ", ".join(untested))

    # 6. Auth matrix
    H(1, "6. Authentication & Authorization Matrix")
    cells = {}
    for s in scen:
        az = s.get("authz")
        if not az:
            continue
        key = (s["inventory"], s["actor"])
        ok = az["expected"] == az["actual"] and s["result"] == "pass"
        txt = f"{az['actual']} {'(ok)' if ok else '(expected ' + az['expected'] + ': FAIL)'}"
        if key not in cells or "FAIL" in txt:
            cells[key] = txt
    used_actors = [a["id"] for a in actors if any(k[1] == a["id"] for k in cells)]
    rows = []
    for iid in inv:
        if any(k[0] == iid for k in cells):
            rows.append([f"{iid} {inv[iid].get('method', '')} {inv[iid].get('path', inv[iid].get('name', ''))}".strip()] +
                        [cells.get((iid, a), "-") for a in used_actors])
    if rows:
        T(["Endpoint"] + [f"{a} ({amap[a].get('role', '')})" for a in used_actors], rows)
        P("Cell = observed outcome for that actor; '(ok)' means it matched the expected policy.")
    else:
        P("No authorization scenarios were recorded (add `authz` to scenarios).")

    # 7. Scenarios by module
    H(1, "7. Module-by-Module Scenarios")
    for m in mods:
        H(2, f"7.{list(mods).index(m) + 1} {m}")
        ms = [s for s in scen if s["module"] == m]
        T(["ID", "Type", "Scenario", "Actor", "Expected", "Actual", "Result"],
          [[s["id"], s["type"], s["title"], s["actor"], s["expected"], s["actual"], s["result"].upper() + (f" → {s['defect']}" if s.get("defect") else "")] for s in ms])
        for s in ms:
            if not (full or s["type"] != "success" or s["result"] != "pass"):
                continue
            if not (s.get("request") or s.get("evidence")):
                continue
            H(3, f"{s['id']} — {s['title']} [{s['result'].upper()}]")
            if s.get("request"):
                P("Request / steps:")
                C(s["request"])
            if s.get("evidence"):
                P("Evidence (redacted):")
                C(s["evidence"])

    # 8. Defects
    H(1, "8. Security / Access-Control & Defect Findings")
    order = {sv: i for i, sv in enumerate(SEVERITIES)}

    def defect_section(title, items):
        H(2, title)
        if not items:
            P("None.")
            return
        for x in sorted(items, key=lambda z: (order[z["severity"]], z["id"])):
            linked = ", ".join(s["id"] for s in scen if s.get("defect") == x["id"]) or "-"
            H(3, f"{x['id']} — {x['title']} [{x['severity'].upper()} / {x['status'].upper()}]")
            UL([f"Location: {x.get('location', 'n/a')}", f"Found by: {linked}", f"Description: {x['description']}",
                f"Impact: {x['impact']}", f"Fix: {x['fix']}"] + ([f"Retest evidence: {x['retest_evidence']}"] if x.get("retest_evidence") else []))

    defect_section("8.1 Open defects", [x for x in defs if x["status"] in ("open", "retest")])
    defect_section("8.2 Fixed and retested", [x for x in defs if x["status"] == "fixed"])
    wf = [x for x in defs if x["status"] == "wont_fix"]
    if wf:
        defect_section("8.3 Accepted / won't fix", wf)

    # 9. Remediation
    H(1, "9. User Remediation Guidance")
    rem = d.get("remediation") or []
    if not rem:
        P("No remediation items recorded.")
    for item in rem:
        H(2, item.get("audience", "General"))
        UL(item.get("steps") or [])
    P(f"_Report generated by claude-harness qa-report. Redactions applied: {{REDACTIONS}}._")
    return B


# ───────────────────────── emitters ─────────────────────────
def cell(c):
    return str(c).replace("|", "\\|").replace("\n", "<br>")


def to_markdown(blocks):
    out = []
    for b in blocks:
        k = b[0]
        if k == "title":
            out.append(f"# {b[1]}\n")
        elif k == "h":
            out.append(f"{'#' * (b[1] + 1)} {b[2]}\n")
        elif k == "p":
            out.append(b[1] + "\n")
        elif k == "ul":
            out.append("\n".join(f"- {i}" for i in b[1]) + "\n")
        elif k == "table":
            head, rows = b[1], b[2]
            out.append("| " + " | ".join(cell(h) for h in head) + " |\n|" + "---|" * len(head) + "\n" +
                       "\n".join("| " + " | ".join(cell(c) for c in row) + " |" for row in rows) + "\n")
        elif k == "code":
            out.append("```\n" + b[1] + "\n```\n")
    return "\n".join(out)


_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="21"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="100"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="200"/></w:pPr><w:rPr><w:b/><w:sz w:val="44"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="320" w:after="120"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="80"/></w:pPr><w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="160" w:after="60"/></w:pPr><w:rPr><w:b/><w:sz w:val="22"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:basedOn w:val="Normal"/><w:pPr><w:pBdr><w:left w:val="single" w:sz="12" w:space="6" w:color="999999"/></w:pBdr><w:spacing w:after="0"/></w:pPr><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:sz w:val="18"/></w:rPr></w:style>
<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:tblPr><w:tblBorders>
<w:top w:val="single" w:sz="4" w:color="999999"/><w:left w:val="single" w:sz="4" w:color="999999"/><w:bottom w:val="single" w:sz="4" w:color="999999"/>
<w:right w:val="single" w:sz="4" w:color="999999"/><w:insideH w:val="single" w:sz="4" w:color="999999"/><w:insideV w:val="single" w:sz="4" w:color="999999"/></w:tblBorders></w:tblPr></w:style>
</w:styles>"""


def _runs(text, base_rpr=""):
    """Split on **bold** and _italic-free_ text into runs."""
    parts = re.split(r"(\*\*[^*]+\*\*)", text)
    xml = []
    for p in parts:
        if not p:
            continue
        bold = p.startswith("**") and p.endswith("**") and len(p) > 4
        t = p[2:-2] if bold else p
        rpr = base_rpr + ("<w:b/>" if bold else "")
        xml.append(f'<w:r>{"<w:rPr>" + rpr + "</w:rPr>" if rpr else ""}<w:t xml:space="preserve">{escape(t)}</w:t></w:r>')
    return "".join(xml)


def _para(text, style=None):
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{ppr}{_runs(text)}</w:p>"


def to_docx(blocks, path):
    body = []
    for b in blocks:
        k = b[0]
        if k == "title":
            body.append(_para(b[1], "Title"))
        elif k == "h":
            body.append(_para(b[2], f"Heading{min(b[1], 3)}"))
        elif k == "p":
            body.append(_para(b[1].replace("_", "") if b[1].startswith("_") else b[1]))
        elif k == "ul":
            body.extend(_para("• " + i) for i in b[1])
        elif k == "code":
            body.extend(_para(line if line else " ", "Code") for line in b[1].split("\n"))
            body.append(_para(""))
        elif k == "table":
            head, rows = b[1], b[2]
            ncol = len(head)
            width = int(9000 / ncol)
            grid = "".join(f'<w:gridCol w:w="{width}"/>' for _ in head)

            def tc(txt, hdr=False):
                shade = '<w:shd w:val="clear" w:color="auto" w:fill="E7E6E6"/>' if hdr else ""
                paras = "".join(f"<w:p>{_runs(line, '<w:b/>' if hdr else '')}</w:p>" for line in (str(txt).split("\n") or [""]))
                return f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}</w:tcPr>{paras}</w:tc>'

            trs = ["<w:tr><w:trPr><w:tblHeader/></w:trPr>" + "".join(tc(h, True) for h in head) + "</w:tr>"]
            trs += ["<w:tr>" + "".join(tc(c) for c in row) + "</w:tr>" for row in rows]
            body.append(f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{"".join(trs)}</w:tbl>')
            body.append(_para(""))
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
           + "".join(body) + '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080"/></w:sectPr></w:body></w:document>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                   '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/_rels/document.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("word/styles.xml", _STYLES)
        z.writestr("word/document.xml", doc)


# ───────────────────────── CLI ─────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("check", "render"))
    ap.add_argument("results")
    ap.add_argument("--out")
    ap.add_argument("--docx", action="store_true", help="also write a .docx next to the Markdown")
    ap.add_argument("--full", action="store_true", help="include request/evidence for passing success scenarios too")
    a = ap.parse_args()

    try:
        data = yaml.safe_load(Path(a.results).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        sys.exit(f"✗ cannot read {a.results}: {e} (tip: quote values that contain ': ' or start with special characters)")
    errs, warns = validate(data)
    for w in warns:
        print(f"! {w}")
    if errs:
        print("\n".join(f"✗ {e}" for e in errs))
        sys.exit(1)
    if a.cmd == "check":
        print(f"✓ qa results OK: {len(data['scenarios'])} scenarios, {len(data.get('defects') or [])} defects")
        return

    ctx = Ctx()
    blocks = build_blocks(data, a.full, ctx)
    md = to_markdown(blocks).replace("{REDACTIONS}", str(ctx.redactions))
    blocks = [(b[0], b[1].replace("{REDACTIONS}", str(ctx.redactions))) if b[0] == "p" else b for b in blocks]
    out = Path(a.out) if a.out else Path(a.results).with_name("QA-REPORT.md")
    out.write_text(md, encoding="utf-8")
    print(f"✓ wrote {out} ({ctx.redactions} redaction(s) applied)")
    if a.docx:
        dp = out.with_suffix(".docx")
        to_docx(blocks, dp)
        print(f"✓ wrote {dp}")


if __name__ == "__main__":
    main()
