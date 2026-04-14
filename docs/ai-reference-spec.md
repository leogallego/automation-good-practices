# Spec: Consuming AsciiDoc Sources for AI Review Skills

## Problem

The `ansible-cop-review` skill currently loads a monolithic scraped markdown
file (`redhat-cop-automation-good-practices-scrap-2026-03.md`, 115KB, 2549
lines, ~35K tokens). This file is:

- **Stale** — manually scraped, not auto-generated from source
- **Monolithic** — loaded entirely even when reviewing a single role or playbook
- **Redundant** — the same rules already exist as structured AsciiDoc in the
  source repo, and as a condensed version in CLAUDE.md

## Proposal

Replace the monolithic file with selective loading of individual section files
directly from the
[automation-good-practices](https://github.com/redhat-cop/automation-good-practices)
source repo. No build script, no generated artifacts — the source `.adoc` files
are the endpoints.

## Source Files (Endpoints)

All files live in the `main` branch of
`redhat-cop/automation-good-practices`. Each section is a single
`README.adoc` in its own directory:

| File | Lines | ~Tokens | Content |
|---|---:|---:|---|
| `structures/README.adoc` | 54 | 300 | Landscape/Type/Function/Component hierarchy |
| `roles/README.adoc` | 476 | 1,850 | Role design, naming, variables, idempotency, check mode, argument validation, file refs, templates, platform support, fact gathering, providers |
| `collections/README.adoc` | 77 | 230 | Collection structure, implicit variables, versioning, licensing |
| `playbooks/README.adoc` | 165 | 330 | Keeping playbooks simple, tags, debug verbosity |
| `inventories/README.adoc` | 316 | 1,230 | SSOT, As-Is vs To-Be, structured directories, host looping, variable precedence |
| `plugins/README.adoc` | 197 | 480 | Python plugin guidelines, testing with pytest, documentation |
| `coding_style/README.adoc` | 386 | 1,280 | YAML/Jinja2 syntax, naming conventions, FQCN, module usage |
| **All sections** | **1,671** | **~5,700** | |

Additionally:

| File | Purpose |
|---|---|
| `README.adoc` (root) | Master document with introduction and section index |
| `CONTRIBUTE.adoc` | Guideline template (useful for understanding the AsciiDoc structure) |

### Raw GitHub URLs

```
https://raw.githubusercontent.com/redhat-cop/automation-good-practices/main/{section}/README.adoc
```

For example:
```
https://raw.githubusercontent.com/redhat-cop/automation-good-practices/main/roles/README.adoc
```

## AsciiDoc Structure per Section

Every section file follows the same pattern (defined in `CONTRIBUTE.adoc`):

```asciidoc
= Section Title

== Guideline sentence here
[%collapsible]
====
Explanations:: The rule explanation (KEEP — this is the actionable content)
Rationale:: Why the rule exists (OPTIONAL for review — context, not action)
Examples:: Code examples showing correct/incorrect usage (USEFUL for review)
====

== Next guideline...
```

Key structural elements:

- `=` Level-1 heading: section title (one per file)
- `==` Level-2 headings: individual guidelines (the rule statements)
- `===` Level-3 headings: sub-guidelines
- `Explanations::` — the actionable rule content
- `Rationale::` — background context (can be skipped for token savings)
- `Examples::` — code samples (useful but verbose)
- `[%collapsible]` / `====` — wraps the detail block (AsciiDoc-specific, ignore)
- `[source,yaml]` / `----` — code blocks
- `NOTE:`, `TIP:`, `CAUTION:`, `WARNING:`, `IMPORTANT:` — admonitions

## Category-to-Section Mapping

The skill's 17 review categories map to source sections as follows:

| Review Category | Source Section | Notes |
|---|---|---|
| Architecture | `structures/` | Entire file is relevant |
| Role naming | `roles/` | "Naming parameters" heading |
| Variable placement | `roles/` | "Naming variables" and defaults/vars headings |
| Idempotency & check mode | `roles/` | Dedicated heading |
| Argument validation | `roles/` | "Validate with argument specs" heading |
| File references | `roles/` | "Reference files from within" heading |
| Templates | `roles/` | "Use templates wisely" heading |
| Platform support | `roles/` | "Support multiple platforms" heading |
| Fact gathering | `roles/` | "Handle facts gracefully" heading |
| Providers | `roles/` | "Providers" heading |
| Playbook structure | `playbooks/` | Entire file is relevant |
| Inventory | `inventories/` | Entire file is relevant |
| YAML style | `coding_style/` | YAML/Jinja2 headings |
| Naming | `coding_style/` | Naming headings |
| Module usage | `coding_style/` | FQCN and module headings |
| Collections | `collections/` | Entire file is relevant |
| Documentation | `roles/` | README heading + `collections/` |

### Practical loading groups

Most reviews will need only 2-3 sections. Recommended groupings:

| Reviewing... | Load sections | ~Tokens |
|---|---|---|
| A single role | `roles/`, `coding_style/` | ~3,100 |
| A playbook | `playbooks/`, `coding_style/` | ~1,600 |
| Inventory | `inventories/` | ~1,230 |
| A collection | `collections/`, `roles/`, `coding_style/` | ~3,350 |
| Full project | All 7 sections | ~5,700 |

## Loading Strategy

### Current behavior (to replace)

```
1. Glob for redhat-cop-automation-good-practices-*.md in project root
2. If found → read entire 115KB file (~35K tokens)
3. If not found → fetch from GitHub (entire repo? unclear)
4. Also reads CLAUDE.md for condensed rules
```

### Proposed behavior

```
1. Determine which sections are relevant based on the files being reviewed:
   - roles/ tasks/ defaults/ vars/ meta/ handlers/ templates/ → load roles/, coding_style/
   - playbooks (*.yml with hosts:) → load playbooks/, coding_style/
   - inventory/ group_vars/ host_vars/ → load inventories/
   - collection (galaxy.yml present) → load collections/, roles/, coding_style/
   - plugins/ modules/ → load plugins/, coding_style/
   - unclear or full review → load all sections

2. For each needed section, fetch via raw GitHub URL:
   https://raw.githubusercontent.com/redhat-cop/automation-good-practices/main/{section}/README.adoc

3. CLAUDE.md rules (if present in the project) still take precedence —
   they are the condensed, imperative version of the same rules.
   The AsciiDoc sections provide the full explanations and examples
   for edge cases.
```

### Token budget comparison

| Approach | Tokens | Notes |
|---|---|---|
| Current monolithic file | ~35,000 | Always loaded in full |
| All 7 AsciiDoc sections | ~5,700 | Raw source, no processing |
| Selective (role review) | ~3,100 | Only roles/ + coding_style/ |
| Selective (playbook review) | ~1,600 | Only playbooks/ + coding_style/ |
| CLAUDE.md alone | ~2,500 | Condensed rules, no examples |

## AsciiDoc Parsing Notes

The skill consumer (Claude) does not need a parser. AsciiDoc is readable as
plain text. However, these patterns should be understood:

| Pattern | Meaning | Handling |
|---|---|---|
| `= Title` | Level-1 heading | Section title |
| `== Title` | Level-2 heading | Individual guideline |
| `=== Title` | Level-3 heading | Sub-guideline |
| `[%collapsible]` | Collapsible block marker | Ignore |
| `====` | Block delimiter | Ignore |
| `----` | Code block delimiter | Treat as code fence |
| `[source,yaml]` | Code language tag | Next code block is YAML |
| `Explanations::` | Definition list key | Rule content follows |
| `Rationale::` | Definition list key | Background follows |
| `Examples::` | Definition list key | Code examples follow |
| `include::path[]` | File inclusion | Ignore (content is inline in rendered form) |
| `image::path[]` | Image reference | Ignore |
| `NOTE: text` | Admonition | Important note |
| `https://url[label]` | Link | URL with display text |
| `<<anchor,text>>` | Cross-reference | Internal link |

## Migration Path

1. **Drop** the bundled `redhat-cop-automation-good-practices-scrap-*.md` file
   from the skill repo
2. **Update** SKILL.md to fetch sections via raw GitHub URLs instead of
   globbing for a local markdown file
3. **Add** section-selection logic based on the files being reviewed
4. **Keep** CLAUDE.md as the primary rule source — the AsciiDoc sections
   become the "detailed reference" fallback, not the primary source
5. **Remove** the "if not available locally" fallback — fetching from GitHub
   becomes the standard path, not a fallback

## Open Questions

- **Caching**: Should the skill cache fetched `.adoc` files locally? Fetching
  7 small files per review is fast, but repeated reviews in the same session
  would re-fetch. Consider caching in a temp directory for the session.
- **Version pinning**: Should the skill fetch from `main` (always latest) or
  pin to a tag/release? `main` means rules update automatically but could
  break if the repo structure changes.
- **CLAUDE.md overlap**: When both CLAUDE.md rules and AsciiDoc sections are
  available, CLAUDE.md should take precedence for rule *application*, with
  AsciiDoc providing additional context and examples. Define clearly which
  wins on conflicts.
