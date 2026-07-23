---
name: repo-due-diligence
description: Static, read-only, language-adaptive repository onboarding and technical due diligence workflow. Use when analyzing an unfamiliar codebase without executing code, including architecture, domain model, module boundaries, security, data, code distribution, hygiene findings, diagrams, risks, and refactoring recommendations.
---

# Repository Onboarding Due Diligence

## Goal

Treat an unfamiliar repository as static evidence. Produce a concise, readable, evidence-backed onboarding report for technical leads, architects, incoming engineers, security reviewers, and managers.

This skill is **static and read-only** for every target repository it examines. It never executes, modifies, or installs anything from the target codebase.

**Default outputs:**

- Report entrypoint: `docs/repo-due-diligence/README.md`
- Report chapters: `docs/repo-due-diligence/*.md`
- Assets: `docs/repo-due-diligence/assets/`

Create `docs/repo-due-diligence.md` only when the user explicitly requests a single-file archive.

## Language Policy

- Honor any explicit language requested for the report or handoff.
- When the user does not specify a language, use the predominant language of the user's current request.
- Keep report-authored prose, headings, labels, statuses, severity levels, and confidence levels consistent in that language. Keep code, protocol names, file paths, and stable identifiers unchanged.
- Treat terms shown in this skill or its references as semantic concepts, not mandatory output literals. Localize concepts such as fact, inference, risk, recommendation, not applicable, and insufficient evidence into the report language.
- Do not produce a bilingual report unless the user explicitly requests one.

## External Fallback Boundaries

The following companion workflows are **not merged into this skill** and are **not mandatory**. Invoke them according to the rules below for each workflow.

- `humanizer-zh`: optional external editorial pass used only when the selected report language is Chinese. Availability check and fallback rules live in step 3.1; language-independent readability rules are defined once in `references/deliverables.md` (Readability Contract).
- `excalidraw-diagram-generator`: optional supplementary asset. Excalidraw output is never a substitute for a required report diagram. Mermaid is the default diagram format for all report chapters.

## Non-Negotiable Constraints

- **MUST NOT execute repository code.** Never run, import, compile, interpret, source, or start any file from the target repository.
- **MUST NOT run** tests, benchmarks, builds, linters, formatters, type checkers, coverage collectors, migrations, seeders, generators, package-manager scripts (`npm install`, `pip install`, `go mod download`, etc.), task runners, containers, deployment commands, or any repository-provided executable or script.
- Avoid tools that load repository-controlled hooks, plugins, lifecycle scripts, build files, or executable configuration. Inspect those definitions as plain text only.
- Do not modify source, production configuration, migrations, tests, dependencies, lock files, or any other file in the target repository.
- Do not install repository or global dependencies. When optional tooling is unavailable, report the limitation and use a non-executing fallback.
- Allow only read-only commands that treat files as data: `rg`, `find`, file metadata tools, safe text and statistics processing, and Git reads with repository-controlled helpers disabled. Use `git --no-pager -c core.fsmonitor=false`; add `--no-ext-diff --no-textconv` to diff commands.
- **Never print secrets, tokens, certificates, private connection strings, internal hostnames, or sensitive configuration values.** Cite the risk type and file path only.
- Separate facts, inferences, risks, and recommendations using labels localized according to the Language Policy. Mark runtime-dependent conclusions as static-analysis conclusions that were not runtime-verified, or as insufficient evidence.
- Cite every material conclusion with `E-###` identifiers. Define source paths, read-only commands, existing reports, and Git references only in the evidence register.
- Never claim that tests, builds, startup, migrations, or runtime behavior passed verification.

## Workflow

### 0. Inventory

Inspect repository instructions, README files, architecture and deployment docs, CI configuration, manifests, entrypoints, business directories, tests, existing reports, schemas, migrations, security code, observability configuration (alert rules, dashboard definitions, telemetry setup), and Git history.

Declare the analysis baseline and scope before deep inspection: date, branch and commit when available, dirty-worktree state, included systems, excluded generated/vendor/build directories, and known coverage gaps. For a monorepo or large multi-service system, record what was not examined and why.

Record the decision context when known (handover, rebuild-versus-refactor, acquisition, security review); when unknown, proceed as a general technical assessment. Determine whether full coverage of the in-scope code is feasible; when it is not, apply `references/sampling-strategy.md` and declare the sampling plan in the baseline.

Record declared build, test, coverage, and startup commands as text only. Do not run them. Produce a short analysis plan before drawing conclusions.

### 1. Analyze

Cover only evidence-backed aspects of these tracks:

1. Project purpose, actors, use cases, and core flows.
2. Runtime processes, deployment units, dependencies, availability, recovery, and observability.
3. Domain vocabulary, rules, lifecycle, data model, and storage.
4. Module structure, dependencies, boundaries, and domain-module friction.
5. APIs, jobs, integrations, permissions, and security boundaries.
6. Code distribution, complexity, churn, likely hotspots, duplicate code or rules, dead-code candidates, and comment smells.
7. Tests, existing coverage evidence, CI/CD, documentation, and developer experience.
8. Risks, strengths, human-confirmation needs, and staged recommendations.

For every track, return evidence, conclusions, uncertainty, and follow-up. Mark absent concepts as not applicable using the report language; do not invent content to fill a section.

When the scope supports cross-file review, apply the local code-hygiene taxonomy in `references/code-hygiene-taxonomy.md` to identify `DUP-###`, `DEAD-###`, and `CMT-###` findings with evidence descriptors. Assign findings directly into the onboarding `E-###` register and keep false-positive and confidence qualifications. If a standalone external hygiene audit is separately requested by the user, integrate its output as additional evidence without making it mandatory or blocking the report.

### 2. Cross-Validate

Check at least these relationships before writing:

- Use cases against APIs, jobs, permissions, data changes, and tests.
- Domain concepts against modules, DTOs, persistence models, and naming.
- Runtime topology against availability, recovery order, and observability.
- Security boundaries across API, service, persistence, configuration, and background work.
- Critical paths and churn or complexity hotspots against existing test evidence.
- Duplicate findings against domain boundaries and intentional variation; dead-code findings against public or dynamic roots; comment findings against rationale and authoritative documentation.
- Recommendations against risks, evidence, cost, dependencies, and acceptance criteria.

Before writing, record which required diagrams from `references/diagram-rules.md` are triggered for this repository. This is the diagram plan for steps 3 and 4.

### 3. Write the Report

Read `references/deliverables.md` before writing when it is present. When present, treat it as the single source of truth for filenames, chapter ownership, identifiers, and readability rules. Diagram requirements always follow `references/diagram-rules.md`. When `references/deliverables.md` is absent, apply the chapter list in the Reference Contracts section below and use conservative defaults.

Create the core chapters and only the applicable conditional chapters. Record every omitted canonical chapter and its localized not-applicable or insufficient-evidence reason in `README.md`. Define each risk, strength, recommendation, confirmation item, and evidence item once, then reference its stable identifier elsewhere.

Never pad ranked lists. "Top N" means up to N evidence-backed items.

Diagram obligations — the required diagram set, trigger gates, and the `## Diagram decision` ledger — follow `references/diagram-rules.md` only.

### 3.1 Readability Pass

After the first complete draft, review all report chapters for readability. When the selected report language is Chinese, check whether the `humanizer-zh` skill is available in the current environment. If it is available, invoke it now as an external workflow on the generated Markdown chapters. For other report languages, or when `humanizer-zh` is unavailable, perform the same full read-through using the language-independent Readability Contract; the absence of a language-specific editorial skill must not block delivery.

The pass is a full read-through of every chapter, not only a pattern scan. Grep-style scans for AI vocabulary are a pre-filter; they cannot catch over-compressed, fragmentary prose, which is the most common failure mode of this report's evidence-driven style. The pass is complete only when every chapter has been read end-to-end and cryptic fragments rewritten into complete sentences.

Readability rules are defined once: in `references/deliverables.md` (Readability Contract) when present. When it is absent, apply these conservative defaults:

- Preserve every fact, uncertainty, severity, confidence, identifier, source relationship, and safety qualification.
- One main conclusion per paragraph; prefer concrete subjects and verbs over abstract filler.
- Tables only for exact mappings, registers, and comparisons.

After editing, cross-check all identifiers in use against their canonical registers. Every diagram block and every `## Diagram decision` section must survive the edit intact.

### 4. Create Diagrams

`references/diagram-rules.md` is the single source of truth for all diagram requirements: the required diagram set, trigger gates, the decision ledger, format selection (Mermaid default, C4, Excalidraw), and quality gates.

Create or verify the diagrams recorded in the step 2 diagram plan. Do not create diagrams whose trigger condition is unmet. Do not invent relationships not evidenced by the codebase.

### 5. Presentation Outline (Optional)

A `.pptx` presentation is **not produced by default**. When the user separately requests presentation material, produce `docs/repo-due-diligence/slides-outline.md` directly from the completed report. Preserve any analysis-authored slide sources under `assets/`. Do not use `ppt-master`, `python-pptx`, hand-written scripts, or any other custom PPT pipeline.

## Reference Contracts

This skill loads reference files from `references/` relative to its own skill directory when they are present. Loading order:

1. `references/deliverables.md` — chapter list, filenames, identifier schemes, readability contract, slide outline contract. When present, this overrides the defaults below.
2. `references/code-hygiene-taxonomy.md` — `DUP-###`, `DEAD-###`, `CMT-###` finding taxonomy, evidence descriptors, false-positive guidance.
3. `references/domain-and-adr.md` — domain vocabulary rules, ADR format, ubiquitous-language conventions.
4. `references/module-boundary-design.md` — module boundary criteria, dependency direction rules, friction scoring.
5. `references/diagram-rules.md` — single source of truth for diagram requirements: required diagram set, trigger gates, decision ledger, format selection, quality gates.
6. `references/code-distribution-and-hotspots.md` — complexity, churn, hotspot, and dead-code detection guidance.
7. `references/observability-evidence.md` — static observability signal categories, posture grading, and over-claiming cautions.
8. `references/sampling-strategy.md` — evidence selection order, coverage declaration, and false-confidence guards when full coverage is impractical.

When a reference file is absent, continue with the defaults documented in this skill body. Note each missing file in the final response under limitations.

**Default chapter list** (used when `references/deliverables.md` is absent):

- `README.md` — scope declaration, baseline, chapter index, omission register
- `00-executive-summary.md` — decision framing, top risks, strengths, recommendations, confirmation items
- `01-project-overview.md` — purpose, actors, use-case names, technology stack, declared entrypoints
- `02-use-case-model.md` (conditional) — actor-use-case matrix, core flows, edge cases
- `03-domain-model.md` (conditional) — vocabulary, rules, lifecycle, domain events
- `04-codebase-structure.md` — code distribution, complexity, churn, hotspots, `DUP-EXACT/STRUCTURAL/DATA` and `DEAD-###` findings
- `05-module-boundaries.md` — structure, dependency direction, boundary friction, `DUP-RULE/CROSS-LAYER` findings
- `06-runtime-and-availability.md` (conditional) — processes, deployment, dependencies, availability, recovery, observability
- `07-data-and-storage.md` (conditional) — data model, storage choices, migration state
- `08-api-and-integrations.md` (conditional) — APIs, jobs, integrations, permissions
- `09-security.md` — security boundaries, secret handling, known risks
- `10-engineering-quality.md` — hygiene summary, `CMT-###` findings, tests, CI/CD, developer experience
- `11-refactoring-roadmap.md` — risks, confirmation items, staged recommendations
- `12-onboarding-guide.md` — first-week guide, key contacts, open questions
- `appendix-evidence-index.md` — `E-###` register

## Final Response

Return a concise handoff in the report language containing:

- Skills used and any materially relevant skipped skills.
- Generated files and their paths.
- Explicit confirmation that no repository code was executed.
- Up to three most important risks and recommendations, referenced by identifier.
- Human-confirmation items and material limitations.
- Any deliverable that could not be produced and the closest useful fallback.
- Whether `references/deliverables.md` was present or absent, and which reference files were loaded.
