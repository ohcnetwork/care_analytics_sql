#!/usr/bin/env python3
"""Deterministic linter for CARE analytics query docs.

Given one or more query markdown files (the TEMPLATE.md format used across
this repo), it:

  1. extracts every ```sql fenced block,
  2. substitutes Metabase templating so the SQL becomes parseable:
       {{param}}        -> the dummy literal `1`
       [[ ... ]]        -> two variants are produced and BOTH are parsed:
                           "kept"    = brackets stripped, inner clause kept
                           "removed" = the whole optional clause dropped
     (Metabase drops or keeps `[[...]]` at runtime depending on whether the
      parameter is bound, so a query must parse both ways),
  3. parses each variant with sqlglot's Postgres dialect and reports syntax
     errors,
  4. checks TEMPLATE.md conformance: `## Purpose`, `## Query`, `## Notes`
     sections, a `*Last updated: YYYY-MM-DD*` line, and a Parameters table
     whenever `{{` appears in the SQL.

It is a *reporter*, not a gate: it always exits 0 (unless invoked wrongly)
and writes a markdown report for the review agent to consume. Malformed
files (stray/unclosed fences, no SQL at all) are reported as findings, never
crashes -- several existing files in this repo are imperfect and the linter
must degrade gracefully on them.

Usage:
    python3 lint_queries.py [--out report.md] file1.md [file2.md ...]

Requires: sqlglot (pip install sqlglot).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field

try:
    import sqlglot
    from sqlglot.errors import ParseError
except ImportError:  # pragma: no cover
    print("error: sqlglot is not installed (pip install sqlglot)", file=sys.stderr)
    sys.exit(2)

FENCE_RE = re.compile(r"^\s*(`{3,})\s*(\S*)\s*$")
PARAM_RE = re.compile(r"\{\{\s*[\w.]+\s*\}\}")
OPTIONAL_RE = re.compile(r"\[\[(.*?)\]\]", re.DOTALL)
LAST_UPDATED_RE = re.compile(r"^\*Last updated: \d{4}-\d{2}-\d{2}\*\s*$", re.MULTILINE)
TABLE_ROW_RE = re.compile(r"^\s*\|.+\|\s*$")
TOKEN_REPR_RE = re.compile(r"<Token[^>]*?text: (\S+?),[^>]*>")


@dataclass
class SqlBlock:
    start_line: int  # 1-based line of the opening fence
    text: str
    closed: bool


@dataclass
class FileReport:
    path: str
    findings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.findings


def extract_sql_blocks(lines: list[str]) -> tuple[list[SqlBlock], list[str]]:
    """Walk fence lines; return sql blocks + structural warnings.

    Tolerates the imperfections found in real files: 4-backtick fences,
    stray trailing fences that open an empty block, and blocks that are
    never closed before EOF.
    """
    blocks: list[SqlBlock] = []
    warnings: list[str] = []
    in_block = False
    is_sql = False
    start = 0
    buf: list[str] = []

    for i, line in enumerate(lines, start=1):
        m = FENCE_RE.match(line)
        if not m:
            if in_block and is_sql:
                buf.append(line)
            continue
        if not in_block:
            in_block = True
            is_sql = m.group(2).lower() == "sql"
            start = i
            buf = []
        else:
            # Any fence line closes the open block, regardless of length.
            if is_sql:
                blocks.append(SqlBlock(start, "\n".join(buf), closed=True))
            in_block = False
            is_sql = False

    if in_block:
        if is_sql:
            blocks.append(SqlBlock(start, "\n".join(buf), closed=False))
            warnings.append(
                f"unclosed ```sql fence opened at line {start} (parsed to end of file)"
            )
        else:
            content = "\n".join(buf).strip()
            if content:
                warnings.append(
                    f"unclosed code fence opened at line {start} swallows trailing content"
                )
            else:
                warnings.append(
                    f"stray trailing code fence at line {start} (harmless, but should be removed)"
                )
    return blocks, warnings


def metabase_variants(sql: str) -> dict[str, str]:
    """Return the two parseable renderings of a Metabase-templated query."""
    kept = OPTIONAL_RE.sub(lambda m: m.group(1), sql)
    removed = OPTIONAL_RE.sub("", sql)
    kept = PARAM_RE.sub("1", kept)
    removed = PARAM_RE.sub("1", removed)
    if kept == removed:
        return {"as written": kept}
    return {"optional clauses kept": kept, "optional clauses removed": removed}


def parse_errors(sql: str) -> list[str]:
    """Parse with sqlglot (postgres); return human-readable error strings."""
    if not sql.strip():
        return ["block is empty"]
    try:
        sqlglot.parse(sql, read="postgres")
        return []
    except ParseError as e:
        errs = []
        for err in (e.errors or [])[:3]:
            desc = TOKEN_REPR_RE.sub(r"'\1'", str(err.get("description", "parse error")))
            line = err.get("line")
            col = err.get("col")
            loc = f" (block line {line}, col {col})" if line else ""
            errs.append(f"{desc}{loc}")
        return errs or [str(e).splitlines()[0]]
    except Exception as e:  # sqlglot can raise TokenError etc. on garbage
        return [f"{type(e).__name__}: {e}"]


def check_template(content: str, sql_texts: list[str], report: FileReport) -> None:
    """TEMPLATE.md conformance checks (structure only -- accuracy is the
    review agent's job)."""
    for section in ("## Purpose", "## Query", "## Notes"):
        if not re.search(rf"^{re.escape(section)}\s*$", content, re.MULTILINE):
            report.findings.append(f"missing `{section}` section (see TEMPLATE.md)")

    if not LAST_UPDATED_RE.search(content):
        report.findings.append(
            "missing `*Last updated: YYYY-MM-DD*` line (see TEMPLATE.md)"
        )

    # A Parameters table is required whenever the SQL references {{params}},
    # even when the templated lines are commented out -- the doc still has to
    # tell the Metabase user what the parameter means.
    uses_params = any("{{" in s for s in sql_texts)
    if uses_params:
        m = re.search(r"^## Parameters\s*$", content, re.MULTILINE)
        if not m:
            report.findings.append(
                "SQL references `{{parameters}}` but there is no `## Parameters` section"
            )
        else:
            rest = content[m.end():]
            next_heading = re.search(r"^#{1,6}\s", rest, re.MULTILINE)
            section_body = rest[: next_heading.start()] if next_heading else rest
            if not any(TABLE_ROW_RE.match(l) for l in section_body.splitlines()):
                report.findings.append(
                    "`## Parameters` section has no markdown table describing the `{{parameters}}`"
                )


def lint_file(path: str) -> FileReport:
    report = FileReport(path=path)
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError as e:
        report.findings.append(f"could not read file: {e}")
        return report

    blocks, fence_warnings = extract_sql_blocks(content.splitlines())
    report.findings.extend(fence_warnings)

    if not blocks:
        report.findings.append("no ```sql blocks found -- is this a query doc?")
    for idx, block in enumerate(blocks, start=1):
        label = f"SQL block {idx} (line {block.start_line})"
        for variant, sql in metabase_variants(block.text).items():
            errs = parse_errors(sql)
            for err in errs:
                report.findings.append(
                    f"{label}, {variant}: does not parse as Postgres -- {err}"
                )
    if blocks:
        report.notes.append(
            f"{len(blocks)} SQL block(s) parsed with sqlglot dialect=postgres"
        )

    check_template(content, [b.text for b in blocks], report)
    return report


def render_report(reports: list[FileReport]) -> str:
    lines = ["# SQL lint report", ""]
    lines.append(
        "Deterministic findings from `.github/scripts/lint_queries.py` "
        "(sqlglot Postgres parse + TEMPLATE.md structure). "
        "These are inputs for review, not verdicts."
    )
    lines.append("")
    if not reports:
        lines.append("No changed query docs to lint.")
        return "\n".join(lines) + "\n"
    for r in reports:
        lines.append(f"## `{r.path}`")
        lines.append("")
        if r.clean:
            lines.append("No lint findings. " + "; ".join(r.notes))
        else:
            for f_ in r.findings:
                lines.append(f"- {f_}")
        lines.append("")
    total = sum(len(r.findings) for r in reports)
    lines.append(f"---\n**{total} finding(s) across {len(reports)} file(s).**")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="*", help="query markdown files to lint")
    ap.add_argument("--out", help="write the markdown report here (default: stdout)")
    args = ap.parse_args(argv)

    reports = [lint_file(p) for p in args.files]
    text = render_report(reports)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {args.out} ({sum(len(r.findings) for r in reports)} findings)")
    else:
        print(text)
    # Always succeed: findings are agent input, not a CI gate.
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
