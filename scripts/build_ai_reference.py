#!/usr/bin/env python3
"""Build condensed AI-reference markdown from AsciiDoc good-practice sections.

Processes each {section}/README.adoc from the automation-good-practices repo:
- Keeps: guideline headings, explanations, short code examples, admonitions, bullets
- Strips: rationale, verbose examples, includes, images, AsciiDoc-only markup

Outputs compact markdown files suitable for selective AI context loading.

Usage:
    python3 scripts/build_ai_reference.py [--output docs/ai-reference]
"""

import argparse
import re
import sys
from pathlib import Path

SECTIONS = [
    "structures",
    "roles",
    "collections",
    "playbooks",
    "inventories",
    "plugins",
    "coding_style",
]

MAX_CODE_LINES = 15

# --- Regex patterns ---
RE_HEADING = re.compile(r"^(={1,4})\s+(.+)$")
RE_SOURCE_TAG = re.compile(r"^\[source,(\w+)\]$")
RE_COLLAPSIBLE = re.compile(r"^\[%collapsible\]$")
RE_BLOCK_DELIM = re.compile(r"^={4}\s*$")
RE_CODE_DELIM = re.compile(r"^-{4}\s*$")
RE_INCLUDE = re.compile(r"^include::")
RE_IMAGE = re.compile(r"^image::")
RE_ANCHOR = re.compile(r"^\[\[.+\]\]$")
RE_ADMONITION = re.compile(r"^(NOTE|TIP|CAUTION|WARNING|IMPORTANT):\s+(.+)")
RE_DEF_KEEP = re.compile(
    r"^(Explanations?|Use Cases?|Explanation)::\s*(.*)", re.IGNORECASE
)
RE_DEF_RATIONALE = re.compile(r"^Rationale::", re.IGNORECASE)
RE_DEF_EXAMPLES = re.compile(r"^Examples?::", re.IGNORECASE)
RE_LINK = re.compile(r"(https?://\S+?)\[([^\]]*)\]")
RE_XREF = re.compile(r"<<[^,>]*,?([^>]*)>>")
RE_CALLOUT = re.compile(r"\s+<\d+>\s*$")
RE_CALLOUT_LINE = re.compile(r"^<\d+>\s+")
RE_BLOCK_TITLE = re.compile(r"^\.[A-Z]")
RE_PLUS_CONT = re.compile(r"^\+\s*$")
RE_ORDERED_LIST = re.compile(r"^\.\s+(.+)$")


def clean_line(text):
    """Convert AsciiDoc inline markup to markdown."""
    text = RE_LINK.sub(r"[\2](\1)", text)
    text = RE_XREF.sub(r"\1", text)
    text = RE_CALLOUT.sub("", text)
    return text


def convert_section(name, base_dir):
    """Convert one AsciiDoc section file to condensed markdown."""
    path = base_dir / name / "README.adoc"
    lines = path.read_text().splitlines()
    out = []

    skip = False
    in_collapsible = 0
    in_code = False
    code_lang = ""
    code_buf = []
    pending_lang = ""

    for line in lines:
        # --- Code block delimiters ---
        if RE_CODE_DELIM.match(line):
            if in_code:
                in_code = False
                # Skip blocks that are only include:: directives
                has_real_content = any(
                    cl.strip() and not RE_INCLUDE.match(cl.strip())
                    for cl in code_buf
                )
                if has_real_content and len(code_buf) <= MAX_CODE_LINES:
                    out.append("```{}".format(code_lang))
                    for cl in code_buf:
                        out.append(RE_CALLOUT.sub("", cl))
                    out.append("```")
                    out.append("")
                code_buf = []
                code_lang = ""
            else:
                in_code = True
                code_lang = pending_lang
                pending_lang = ""
                code_buf = []
            continue

        if in_code:
            code_buf.append(line)
            continue

        # --- [source,X] tags ---
        m = RE_SOURCE_TAG.match(line)
        if m:
            pending_lang = m.group(1)
            continue

        # --- Collapsible / block delimiters ---
        if RE_COLLAPSIBLE.match(line):
            continue

        if RE_BLOCK_DELIM.match(line):
            if in_collapsible > 0:
                in_collapsible -= 1
                if in_collapsible == 0:
                    skip = False
            else:
                in_collapsible += 1
            continue

        # --- Headings (always keep, reset skip) ---
        m = RE_HEADING.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            skip = False
            out.append("{} {}".format("#" * level, text))
            out.append("")
            continue

        # --- Definition list keys ---
        m = RE_DEF_KEEP.match(line)
        if m:
            skip = False
            rest = m.group(2).strip()
            if rest:
                out.append(clean_line(rest))
                out.append("")
            continue

        if RE_DEF_RATIONALE.match(line):
            skip = True
            continue

        if RE_DEF_EXAMPLES.match(line):
            skip = True
            continue

        # --- Always-skip patterns ---
        if RE_INCLUDE.match(line):
            continue
        if RE_IMAGE.match(line):
            continue
        if RE_ANCHOR.match(line):
            continue
        if RE_BLOCK_TITLE.match(line):
            continue
        if RE_PLUS_CONT.match(line):
            continue

        # --- Content lines ---
        if skip:
            continue

        stripped = line.strip()
        if not stripped:
            if out and out[-1] != "":
                out.append("")
            continue

        # Callout explanation lines (<1> text)
        if RE_CALLOUT_LINE.match(stripped):
            continue

        # Admonitions
        m = RE_ADMONITION.match(stripped)
        if m:
            out.append(
                "> **{}:** {}".format(m.group(1).capitalize(), clean_line(m.group(2)))
            )
            out.append("")
            continue

        # Bullet points
        if stripped.startswith("* "):
            out.append("- {}".format(clean_line(stripped[2:])))
            continue

        # Ordered list items (AsciiDoc ". text" -> markdown "1. text")
        m = RE_ORDERED_LIST.match(stripped)
        if m:
            out.append("1. {}".format(clean_line(m.group(1))))
            continue

        # Normal text
        out.append(clean_line(stripped))

    # Clean trailing blanks
    while out and out[-1] == "":
        out.pop()

    return "\n".join(out) + "\n"


def build_summary(section_names, base_dir):
    """Build rules-summary.md from heading structure of all sections."""
    out = [
        "# Ansible Good Practices - Rules Summary",
        "",
        "Auto-generated from the "
        "[Red Hat CoP Automation Good Practices]"
        "(https://redhat-cop.github.io/automation-good-practices/).",
        "",
        "Section references with full explanations are available "
        "in the same directory.",
        "",
    ]

    for name in section_names:
        path = base_dir / name / "README.adoc"
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            m = RE_HEADING.match(line)
            if not m:
                continue
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 1:
                out.append("## {}".format(text))
                out.append("")
            elif level == 2:
                out.append("- {}".format(text))
            elif level == 3:
                out.append("  - {}".format(text))
        out.append("")

    while out and out[-1] == "":
        out.pop()

    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Build condensed AI-reference markdown from AsciiDoc sources."
    )
    parser.add_argument(
        "--output",
        "-o",
        default="docs/ai-reference",
        help="Output directory (default: docs/ai-reference)",
    )
    parser.add_argument(
        "--sections",
        nargs="+",
        default=SECTIONS,
        help="Sections to process (default: all)",
    )
    args = parser.parse_args()

    base_dir = Path(".")
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    processed = []
    for name in args.sections:
        path = base_dir / name / "README.adoc"
        if not path.exists():
            print(
                "  WARNING: {} not found, skipping".format(path),
                file=sys.stderr,
            )
            continue
        md = convert_section(name, base_dir)
        out_path = output_dir / "{}.md".format(name)
        out_path.write_text(md)
        line_count = md.count("\n")
        processed.append(name)
        print("  {}.md ({} lines)".format(name, line_count))

    summary = build_summary(processed, base_dir)
    summary_path = output_dir / "rules-summary.md"
    summary_path.write_text(summary)
    print(
        "  rules-summary.md ({} total)".format(
            sum(
                1
                for n in processed
                for l in (base_dir / n / "README.adoc").read_text().splitlines()
                if RE_HEADING.match(l) and len(RE_HEADING.match(l).group(1)) >= 2
            )
        )
    )


if __name__ == "__main__":
    main()
