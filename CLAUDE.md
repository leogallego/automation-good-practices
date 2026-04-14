# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is the **Red Hat Communities of Practice (CoP) Automation Good Practices** guide -- a documentation-only repository of opinionated Ansible automation guidelines written in AsciiDoc. It is published to https://redhat-cop.github.io/automation-good-practices/. There is no application code, no tests, and no Ansible playbooks meant to be executed (example playbooks exist only as documentation illustrations).

## Build Commands

Requires Fedora Linux with `asciidoctor`, `asciidoctor-pdf`, `rubygem-rouge`, `plantuml`, `graphviz`, and `hunspell` installed.

```bash
make                # Build PDF (Good_Practices_for_Ansible.pdf + Contributing-to-GPA.pdf)
make release        # Build HTML site into docs/ (used by CI for publishing)
make preview        # Build both PDF and HTML previews into docs/preview/
make view           # Build PDFs and open in okular
make spell          # Run hunspell spellcheck on all .adoc files
make plantuml       # Regenerate SVG diagrams from images/*.plantuml
make clean          # Remove generated PDFs
```

## Document Architecture

The top-level `README.adoc` is the master document. It includes all section files via `include::` directives with `leveloffset=1`. Each section lives in its own directory with a `README.adoc`:

- `structures/` -- Landscape/Type/Function/Component hierarchy
- `roles/` -- Role design, naming, variables, check mode, idempotency, platform support
- `collections/` -- Collection structure, implicit variables, licensing
- `playbooks/` -- Keeping playbooks simple, tags, debug verbosity
- `inventories/` -- SSOT, As-Is vs To-Be, structured directories, host looping
- `plugins/` -- Python guidelines, testing with pytest, documentation
- `coding_style/` -- YAML/Jinja2 syntax, naming conventions, module usage

Shared rendering configuration is in `_style/render.adoc` (included by all section files). Diagrams live in `images/` as PlantUML sources; SVGs are generated via `make plantuml`.

## Writing Guidelines

Each guideline follows this AsciiDoc template (from `CONTRIBUTE.adoc`):

```asciidoc
== Guideline sentence here
[%collapsible]
====
Explanations:: ...
Rationale:: ...
Examples:: ...
====
```

- Write in present tense; avoid "should", "must"
- Use singular "they" for neutrality
- Follow [AsciiDoc recommended practices](https://asciidoctor.org/docs/asciidoc-recommended-practices/)
- Each section file must have a single `=` title and be renderable standalone
- Limit each PR to a single recommendation for easier review

## CI/CD

Three GitHub Actions workflows in `.github/workflows/`:

- `make_docs.yml` -- On push to `main`: builds HTML with `make release`, force-pushes `docs/` to the `docs` branch (used by GitHub Pages)
- `test_docs.yml` -- On pull requests: runs `make release` to verify the document renders without errors
- `make_preview_docs.yml` -- On push to non-main branches: builds preview PDFs/HTML and uploads as artifacts
