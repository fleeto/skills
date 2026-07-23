# Code Distribution and Hotspot Analysis

This file defines rules for measuring, classifying, and reporting code distribution, LOC counts, Domain LOC attribution, complexity, churn, and hotspot identification during repository onboarding analysis. All analysis is static and read-only. No repository-provided scripts, analyzers, or build tools may be run.

---

## Core Constraints

- Count lines and files using read-only text inspection only: `rg`, `find`, `wc -l` on individual files, file metadata tools, and Git log reads.
- Never run repository scripts, task runners, language analyzers, coverage tools, or build systems to collect distribution data. Prohibited examples: `npm run stats`, `cargo build`, `mvn test`, `gradle`, `cloc` (when installed via repository tooling), `tokei` (when invoked via a repository script).
- When a static approximation is the only option, state it explicitly and qualify the confidence.
- Always state what was excluded and why.

---

## Default Exclusions

Exclude these categories by default unless the user explicitly includes them or they contain a material hygiene risk:

- Generated code: `*.generated.*`, `*.pb.go`, `*.pb.ts`, files under `generated/`, `codegen/`, `__generated__/`.
- Vendored code: files under `vendor/`, `node_modules/`, `.cache/`, `third_party/`.
- Build output: files under `dist/`, `build/`, `out/`, `target/`, `.next/`, `.nuxt/`.
- Snapshots and fixtures: `__snapshots__/`, `testdata/`, `fixtures/` when not part of business logic.
- Lock files: `package-lock.json`, `yarn.lock`, `Cargo.lock`, `go.sum`, `poetry.lock`.

State the exclusion list in `appendix-evidence-index.md` as part of the analysis baseline.

---

## LOC Distribution Buckets

Measure and report distribution across these buckets. Not all buckets apply to every repository; mark inapplicable ones as `不适用`.

1. **Language / file type**: lines per language (TypeScript, Python, Go, SQL, etc.) and per significant file extension.
2. **Top-level directory**: lines per first-level directory, excluding the default exclusions above.
3. **Deployable unit**: for monorepos, lines per service, app, or package boundary.
4. **Package or module**: lines per Go package, Python module, npm package, Java package, or equivalent.
5. **Production vs test**: lines in production code paths vs lines in test files. Use path conventions (`__tests__/`, `_test.go`, `spec/`, `test/`) and file name patterns to classify. When the boundary is ambiguous, state the rule used and its limitations.
6. **Configuration, schema, and migration**: lines in config files, schema definitions (JSON Schema, Protobuf, OpenAPI), and database migrations.
7. **Documentation**: lines in Markdown, RST, AsciiDoc, and inline doc comments when material.

Report totals as approximate when exact counting is not feasible with read-only tools. Never claim precision that is not supported by the method used.

---

## Domain LOC

Domain LOC measures the share of the codebase that implements business logic as opposed to infrastructure, framework plumbing, configuration, tests, or tooling. It is a qualitative orientation aid, not a precise metric.

### Attribution Rules

Attribute a file or directory to the domain bucket only when ownership is supported by at least one of:

- Directory or package name that matches a domain concept identified in the ubiquitous language analysis (`domain-and-adr.md`).
- Module or class name that directly maps to a named domain entity, aggregate, or service.
- Explicit architectural declaration in `CONTEXT.md`, `CONTEXT-MAP.md`, README, or architecture docs.
- ADR or architecture doc that defines the domain layer boundary.

### Confidence Classification

- `事实`: ownership is structurally clear from directory or package name matching the domain vocabulary, or from an explicit architectural declaration. State the evidence.
- `推断`: inferred from naming conventions, documentation proximity, or code patterns without a direct structural declaration. State the inference rule and its limitations.
- `证据不足`: stable domain-to-path attribution is not possible from static evidence. Do not estimate; mark as `证据不足` and list what was checked.

Do not blend `事实` and `推断` items into a single aggregate number without labeling which items carry which confidence.

### Domain LOC Report Format

Domain LOC reports the line count attributed to each domain or bounded context when a domain-to-path mapping is supported by static evidence. It is not a single business-vs-infrastructure aggregate; it is a per-domain breakdown that makes concentration, ownership, and boundary health visible.

When the domain-to-path mapping is sufficiently evidenced, report using this table schema. The rows below are schema examples only; reports must replace every placeholder with an evidence-backed count from the corresponding `E-###` entry, or omit the row entirely if evidence is absent. Never fill in concrete numbers without a matching evidence entry.

| 领域 / Bounded Context | 路径 | LOC | 分类 | 置信度 | 证据 |
| --- | --- | --- | --- | --- | --- |
| `<domain name>` | `<path>` | `<LOC from E-###>` | 事实 | 高 | `<E-###: explicit architectural declaration or directory matches domain vocabulary>` |
| `<domain name>` | `<path>` | `<LOC from E-###>` | 推断 | 中 | `<E-###: naming convention corroborated by partial docs>` |
| `<domain name>` | `<path>` | `<LOC from E-###>` | 推断 | 低 | `<E-###: naming convention only, no corroborating documentation>` |
| 跨域 / 基础设施 | `<path>` | `<LOC from E-###>` | 不适用 | — | `<E-###: shared utilities or framework plumbing, no single domain owner>` |

Follow the table with one or two sentences stating what the distribution implies for change risk, ownership clarity, or boundary health. Do not write a narrative per row.

When a domain-to-path mapping cannot be established from static evidence, skip the table and record `证据不足` with a note listing what was checked (directory names, package declarations, CONTEXT.md, architecture docs).

In addition to the table, include:

- Method used (directory name matching, explicit declaration, naming inference).
- Approximate share of total non-excluded LOC per domain, with the caveat that this is a static approximation.
- What was explicitly excluded and why.

---

## Complexity and Churn Indicators

These are signal sources for identifying hotspots. Use them as orientation, not as definitive metrics.

### Static Complexity Signals

Read-only signals that suggest high complexity without running analyzers:

- File line count: files over 500 lines of handwritten code are worth noting; files over 1000 lines are likely hotspot candidates.
- Function or method count per file: high counts suggest missing abstraction.
- Nesting depth: visible from indentation in source files; deep nesting suggests complex conditional logic.
- Import fan-in: files imported by many other files are central to the dependency graph. Use `rg` to count references.
- Import fan-out: files that import from many other packages are tightly coupled to the rest of the codebase.

### Git Churn Signals

Use `git --no-pager -c core.fsmonitor=false log --no-ext-diff --no-textconv` to read Git history without executing repository hooks.

- **High-frequency change**: files with the most commits over the last 90 days or last 500 commits.
- **Recent large diffs**: files with large diff sizes in recent commits.
- **Blame concentration**: files where a small number of authors own nearly all lines (bus-factor risk).

Record the exact Git command used as evidence. State the date range and commit range inspected.

### Hotspot Identification

A hotspot is a file or module that combines high complexity signals with high churn signals. Report up to 20 evidence-backed hotspots in `04-codebase-structure.md`; prefer fewer when evidence is limited. For each hotspot, record:

- File path.
- Complexity signals observed (size, nesting, fan-in/out).
- Churn signals observed (commit frequency, diff size).
- Relevance to domain or critical path when evidenced.
- Confidence (`高` / `中` / `低`).

---

## Chapter Landing

| Analysis | Primary chapter | Secondary chapter |
| --- | --- | --- |
| LOC distribution by language and directory | `04-codebase-structure.md` | — |
| Production vs test ratio | `04-codebase-structure.md` | `10-engineering-quality.md` |
| Domain LOC attribution | `04-codebase-structure.md` (summary) | `03-domain-model.md` (domain mapping) |
| Module-level distribution and boundary mismatch | `05-module-boundaries.md` | — |
| Test/production ratio and DX impact | `10-engineering-quality.md` | — |
| Hotspot concentration and remediation priority | `11-refactoring-roadmap.md` | Only when concentration creates material risk |

Do not repeat the full LOC table in multiple chapters. Define it once in `04-codebase-structure.md` and reference it by chapter link elsewhere.
