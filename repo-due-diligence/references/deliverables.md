# Repository Onboarding Due Diligence — Deliverables Contract

This file is the canonical output contract for the `repo-due-diligence` skill. Keep structure stable across repositories; vary depth according to evidence.

---

## Stability Rules

- Always create the core files. Create conditional chapters only when applicable; record every omission and its status in `README.md`.
- A core chapter with little evidence may be a single paragraph recording what was checked and why nothing more is reportable. Do not expand it to fill the file.
- Chapter numbers encode reading order, not identity. When a new chapter is inserted into this contract, renumber subsequent chapters in the same change and update every cross-reference across all skill files. Never use letter suffixes (`08a`) or append a chapter out of reading order.
- Use `不适用` only when repository type or explicit evidence establishes that a concept is outside scope. Otherwise use `证据不足` and list the paths or patterns checked.
- Define canonical items once and reference their identifiers elsewhere. Never duplicate full findings.
- Use `E-###` for evidence, `R-###` for risks, `S-###` for strengths, `REC-###` for recommendations, and `H-###` for human-confirmation items.
- Preserve companion code-hygiene IDs `DUP-###`, `DEAD-###`, and `CMT-###`. Convert returned evidence descriptors directly into this report's `E-###` register; do not create a second evidence namespace.
- Keep identifiers stable after first assignment. Do not renumber them when priority changes.
- Treat every numeric target as a maximum, not a quota. Never pad lists, diagrams, chapters, or slides.
- Use only existing coverage and CI artifacts. State explicitly that no repository code was executed.
- Create the optional single-file archive only when requested; assemble it from the canonical chapters and never edit it independently.
- When code-hygiene findings are produced using the local `references/code-hygiene-taxonomy.md`, integrate them into the canonical chapters. Do not create a standalone hygiene report unless the user explicitly requests one.

---

## Canonical Directory

```text
docs/repo-due-diligence/
  README.md
  00-executive-summary.md
  01-project-overview.md
  02-use-case-model.md                # conditional
  03-domain-model.md                  # conditional
  04-codebase-structure.md
  05-module-boundaries.md
  06-runtime-and-availability.md      # conditional
  07-data-and-storage.md              # conditional
  08-api-and-integrations.md          # conditional
  09-security.md
  10-engineering-quality.md
  11-refactoring-roadmap.md
  12-onboarding-guide.md
  appendix-evidence-index.md
  assets/
  slides-outline.md                   # optional; created only when user requests presentation material or PPT export is blocked
```

Chapters are ordered top-down: orientation (`01`), business semantics (`02`-`03`), static structure (`04`-`05`), runtime (`06`), persistence and interfaces (`07`-`08`), cross-cutting concerns (`09`-`10`), and action (`11`-`12`).

**Core files** (always created): `README.md`, `00-executive-summary.md`, `01-project-overview.md`, `04-codebase-structure.md`, `05-module-boundaries.md`, `09-security.md`, `10-engineering-quality.md`, `11-refactoring-roadmap.md`, `12-onboarding-guide.md`, `appendix-evidence-index.md`.

**Conditional chapters** (create when evidence exists): `02`, `03`, `06`, `07`, `08`.

For small or utility repositories, omitting most conditional chapters is normal. A complete report can consist of the core files plus only the conditional chapters with real evidence; depth follows evidence, not the chapter list.

---

## Canonical Registers

Maintain these summary indexes in `00-executive-summary.md`:

- **Risk register**: `R-###`, short label, severity, confidence, owning chapter, evidence IDs, and related recommendation IDs.
- **Strength register**: `S-###`, short label, confidence, owning chapter, evidence IDs, and related recommendation IDs when a recommendation builds on the strength.
- **Recommendation register**: `REC-###`, short label, priority, effort, evidence IDs, and related risk IDs. Full analysis lives in `11-refactoring-roadmap.md`.
- **Human-confirmation register**: `H-###`, question, why static evidence is insufficient, affected conclusions, and suggested owner.

Maintain the evidence register in `appendix-evidence-index.md`:

- Evidence ID `E-###`.
- Source path or read-only Git reference.
- Relevant symbol, line, section, or command.
- Short description without sensitive values.
- Confidence and limitations when needed.

The owning topical chapter contains full risk analysis. `11-refactoring-roadmap.md` owns full recommendation analysis; other chapters reference `REC-###` only. Executive registers index items without repeating attack paths, rationale, dependencies, or acceptance criteria. `README.md`, and `slides-outline.md` when produced, summarize or link to canonical IDs rather than redefining them.

Code-hygiene findings are evidence-backed maintenance findings, not automatically risks. Promote a finding to `R-###` only when it creates material delivery, correctness, security, data, or change-amplification risk. Create `REC-###` only when an item is prioritized in the roadmap.

A strength is an evidence-backed asset that changes a decision: something worth preserving, extending, or reusing during remediation — for example a consistent error-handling pattern, disciplined migrations, a well-isolated module seam, or dependable test infrastructure. Every strength cites `E-###` evidence and carries the shared confidence scale; no compliments without code, configuration, or history evidence. The owning chapter holds the context; the register only indexes it. Do not balance risks against strengths mechanically — a strength earns its place only when it affects a preserve-versus-rebuild decision. Recommendations that extend a strength reference its `S-###`; recommendations that replace something registered as a strength state why the strength does not hold.

**Single analysis** (default): the stability rules above suffice — one ID per item, stable for the duration of the analysis. `###` means at least three digits, not a hard limit. `DUP-###`, `DEAD-###`, and `CMT-###` identifiers exist only when the code-hygiene taxonomy is applied.

**Incremental re-analysis** (apply only when re-analyzing a repository that already has registers): load existing registers before assigning IDs. Match by concern and affected scope, not wording. Preserve the original ID when an item moves or changes priority. When splitting an item, keep the original ID for the primary concern and assign new IDs to children. When merging, keep one ID and record the others as aliases. Never reuse retired IDs.

**Shared scales:**

- Severity: `严重`, `高`, `中`, `低` based on potential impact; describe likelihood separately only when evidence supports it.
- Confidence: `高`, `中`, `低` based on evidence completeness.
- Priority: `P0` immediate containment, `P1` next planned change, `P2` planned improvement, `P3` backlog.
- Effort: `S`, `M`, `L`, with repository-specific assumptions stated once.

Write material findings with a stable information model: classification (`事实` or `推断`), conclusion, evidence IDs, confidence, impact, and related `R`/`REC`/`H` IDs. Do not force all fields into one sentence. Put identifiers at paragraph ends or on a short `关联` line when that reads more naturally.

---

## README Contract

Keep `README.md` concise:

- Project one-line description.
- Three to five key conclusions with canonical IDs, written as direct answers rather than register rows.
- Global table of contents.
- Canonical chapters omitted as `不适用` or `证据不足`, with a brief reason for each.
- Role-based reading paths for managers, architects, incoming engineers, security reviewers, and operations/SRE.
- Up to five urgent risks or next actions, selected for orientation and linked to the complete registers in `00-executive-summary.md`. Do not reproduce the complete risk or recommendation register.
- Links to diagrams and the evidence index.

Do not repeat full risk descriptions, recommendation rationale, or chapter prose.

---

## Readability Contract

This contract is the single definition of readability rules for this skill; `SKILL.md` step 3.1 points here and does not restate them.

Apply this contract to `README.md` and chapters `00` through `12`. Keep the evidence appendix compact and factual.

- Start each chapter with one or two sentences that answer "本章说明什么" and, when material, "读完应做什么". Skip this opener when the chapter is shorter than a screen and the title is self-explanatory.
- Use one main conclusion per paragraph. Prefer two short paragraphs over one that combines cause, impact, remediation, acceptance criteria, and rollback.
- Write in complete sentences. Every bullet or list item needs a subject and a verb and must be understandable on its own. An identifier is not a sentence: never compress a point into a fragment such as "收益：R-007。" Place IDs at the end of the sentence or on a `关联` line.
- Guard against over-compression, not only against filler. The evidence-driven style of this report tends toward telegram prose (dropped subjects, stacked nouns, cryptic fragments). If a sentence only makes sense to the analyst who wrote it, rewrite it for the reader.
- Prefer concrete Chinese: name the component, action, failure, or owner. Avoid abstract consulting language when a direct statement is available (for example "态势", "版图", "深化", "闭环", "形成变更放大器").
- Explain uncommon English terms on first use, for example `默认拒绝（fail-closed）` or `本地事件表（outbox）`. Do not mix Chinese and English merely for tone.
- Use canonical Chinese names for the report's own artifacts: 登记册 for registers (风险/优势/建议/人工确认/证据登记册). Do not calque English contract terms into Chinese — 寄存器 means a CPU register. Code, protocol, and file names stay in English.
- Reserve tables for exact mappings, registers, and comparisons with repeated fields. Use prose or short lists for explanation. Do not present the same table or full register in two files.
- Keep canonical IDs, but group them at paragraph ends or in `关联` lines. Evidence-heavy prose should remain readable without mentally resolving every ID inline.
- Use `事实` and `推断` labels where they prevent ambiguity. Do not mechanically bold-label every paragraph.
- Avoid slogan-like titles, three-part rhetorical lists, repeated sentence templates, filler transitions, exaggerated significance, and vague attribution.
- The report voice is calm, specific, and technically opinionated. Do not add first-person reactions, humor, anecdotes, promotional language, or false certainty.

---

## Chapter Ownership

### `00-executive-summary.md`

- Executive summary and project posture.
- Decision framing: the top irreversible risk, the preserve-versus-rebuild posture, and the highest-value human confirmation. Frame them by referencing `R-###`, `S-###`, `REC-###`, and `H-###` items; never introduce new conclusions here.
- Summary indexes for risks, strengths, and recommendations, plus the human-confirmation register.
- Overall static-analysis limitations.

### `01-project-overview.md`

- Purpose, users or consuming systems, inputs, outputs, and system shape.
- Confirmed technology stack and major directories.
- Declared startup, build, test, and coverage entrypoints, clearly marked as not executed.
- Up to ten files that provide the highest onboarding value.
- Orientation level only: name primary use cases in one line each and link to `02-use-case-model.md` when it exists. Do not expand flows here, and do not repeat the distribution data owned by `04-codebase-structure.md`.

For a monorepo or multi-service repository, include a deployable-unit inventory with path, responsibility, external exposure, privileged or sensitive-data role, business criticality evidence, churn/complexity evidence, and deep-dive status. If more than five units exist and the user did not set scope, deep-dive at most five: order by external exposure or privilege/sensitive data first, then evidenced business criticality, then churn/complexity, and finally path name for deterministic ties. Record unselected units and selection limitations.

### `02-use-case-model.md` (conditional)

- Human actors, administrators, external systems, scheduled jobs, consumers, webhooks, and CLIs when applicable.
- Core goals, triggers, primary flows, failure or compensation flows, data changes, permissions, tests, and observability.
- Use-case-to-API/code/data/test mapping for critical paths.

### `03-domain-model.md` (conditional)

- Ubiquitous language and inconsistent terminology.
- Entities, value objects, aggregates, domain services, events, rules, state transitions, and lifecycle when evidenced.
- Domain-concept-to-code mapping and domain-model maturity.
- Mark non-domain utility repositories as `不适用` instead of manufacturing a domain model.

### `04-codebase-structure.md`

- Language and directory distribution, test-to-production distribution, and configuration distribution. Entrypoints and technology stack are owned by `01-project-overview.md`; do not repeat them here.
- Module size, complexity indicators, Git churn, and likely hotspots from static evidence.
- Own findings whose primary subtype is `DUP-EXACT`, `DUP-STRUCTURAL`, or `DUP-DATA`, plus `DEAD-###` candidates, including confidence, reachability limits, maintenance impact, and false-positive controls.
- Up to twenty evidence-backed hotspots; fewer is preferred when evidence is limited.

### `05-module-boundaries.md`

- Module responsibilities, dependencies, public surfaces, and boundary health.
- Layer leakage, circular or penetrating dependencies, duplicated rules, shallow modules, and deep-module opportunities.
- Own findings whose primary subtype is `DUP-RULE` or `DUP-CROSS-LAYER`, distinguishing harmful drift from intentional duplication across domain, deployment, trust, performance, or compatibility boundaries.
- Domain-module mapping, friction, impact, priority, and incremental restructuring direction.

### `06-runtime-and-availability.md` (conditional)

- Processes, deployment units, ports, lifecycle, background work, and external runtime dependencies.
- Availability and failure-impact matrix, recovery order, degradation, timeout, retry, backpressure, and idempotency evidence.
- Health checks, scaling, failover, RTO/RPO evidence, and runtime observability posture graded per signal category (logging, metrics, tracing, alerting, health) following `references/observability-evidence.md`; map gaps to critical paths.
- Distinguish OS processes, in-process tasks, and managed external services.

### `07-data-and-storage.md` (conditional)

- Databases, schemas, migrations, models, caches, queues, search, object storage, and third-party data services.
- Domain-to-model mapping, critical read/write paths, transactions, consistency, migration, and data-permission risks.

### `08-api-and-integrations.md` (conditional)

- User, management, internal, background, and external integration entrypoints.
- REST, RPC, GraphQL, WebSocket, queue, webhook, scheduler, and job surfaces when applicable.
- Authentication, versioning, errors, retries, rate limits, idempotency, endpoint discovery, and dependency configuration.

### `09-security.md`

- Authentication, authorization, tenant isolation, input/output handling, injection, SSRF, XSS/CSRF, upload/download, and callback risks as applicable.
- Secret, privacy, logging, configuration, token/session/cookie, key/certificate, dependency, database-permission, and CI/CD risks.
- Full analysis for security-owned risks: attack path, impact, likelihood when supported, evidence, urgency, and human-confirmation need.
- Never expose sensitive values.

### `10-engineering-quality.md`

- Naming, layering, errors, logging, configuration, documentation, developer experience, performance, and extensibility.
- Assess logging and diagnostics conventions per `references/observability-evidence.md` without repeating the runtime observability posture owned by `06-runtime-and-availability.md`.
- Own `CMT-###` findings and summarize the overall code-hygiene posture, inspected scope, exclusions, and false-positive limitations without repeating findings owned by chapters `04` or `05`.
- Test framework, types, distribution, and declared entrypoints from static inspection.
- The production-vs-test ratio is measured once in `04-codebase-structure.md`; this chapter interprets its DX impact without repeating the table.
- Existing coverage reports and trends, CI test and coverage gates, critical-path gaps, and up to ten highest-value test additions.
- State `未发现现有覆盖度报告/声明命令` when appropriate. Never infer coverage percentages.
- Confirm explicitly that applications, tests, builds, lint, type checks, coverage, migrations, and startup were not run.

### `11-refactoring-roadmap.md`

- Full analysis for recommendations: risk reduction, benefit, effort, dependencies, confidence, and acceptance criteria.
- Map prioritized hygiene work to `REC-###` items that reference the relevant `DUP-###`, `DEAD-###`, or `CMT-###` findings. Do not recommend deletion or consolidation without the companion audit's confidence and human-confirmation constraints.
- Short-, medium-, and long-horizon sequencing without invented calendar commitments.
- State what each stage preserves versus replaces; preserve-and-extend strategies reference the relevant `S-###` strengths.
- Acceptance criteria and rollback or migration concerns for each recommended stage.

### `12-onboarding-guide.md`

- Role-based reading sequence and practical first tasks.
- Highest-value files, concepts, workflows, and operational knowledge for incoming engineers.
- Missing documentation and suggested ADRs.
- Suggest new or improved skills only when a repeated, project-specific workflow justifies one.

### `appendix-evidence-index.md`

- Analysis date, branch, commit when available, dirty-worktree state, scope, exclusions, sampling plan and coverage estimate per `references/sampling-strategy.md`, and limitations.
- Canonical evidence register.
- Mapping from each integrated `DUP-###`, `DEAD-###`, and `CMT-###` finding to onboarding `E-###` evidence IDs.
- Existing reports and Git references used; record exact read-only command arguments and a short output summary when command evidence matters.
- Explicit statement that no repository code was executed.

---

## Diagram Contract

Diagram requirements are defined in `references/diagram-rules.md`, the single source of truth for the required diagram set, trigger gates, the `## Diagram decision` ledger, format selection (Mermaid default, C4, Excalidraw), and quality gates. Do not duplicate diagram rules in this file or elsewhere.

Stable summary: embed Mermaid diagrams inline in their owning chapter; store external assets under `assets/`; never invent relationships not evidenced by the codebase. Optional diagrams may be added when they materially improve a chapter and need no ledger entry.

---

## Slide Outline Contract

`slides-outline.md` is an optional artifact created only when the user explicitly requests presentation material, or when PPT export is blocked and a slide outline is the closest useful fallback.

**Purpose**: provide a presentation-ready narrative derived from the completed report, usable standalone or as input to a PPT tool.

**Content**:

- Derive all slides from the completed report chapters and their canonical identifiers. Do not create a second set of conclusions.
- Default structure (adjust to evidence; prefer no more than 16 slides):
  1. Title — project name, analysis date, scope.
  2. Project posture — one-line summary and top three findings.
  3. System shape — key actors, entry points, and deployment units.
  4. Critical flows — primary use cases or integration paths with mapped evidence.
  5. Architecture and domain findings — module boundaries, domain health, key `DUP-###` or `DEAD-###` promoted findings.
  6. Security posture — trust boundaries, top security risks with `R-###` IDs.
  7. Engineering quality — test coverage state, top `CMT-###` or quality findings.
  8. Risk summary — ranked `R-###` list with severity and owning chapter.
  9. Roadmap — staged `REC-###` items with priority and effort.
  10. Human-confirmation items — `H-###` list with suggested owners.
  11. Onboarding quick-start — role-based entry points.
- Each slide entry: one heading, one core point, one takeaway, and compact canonical IDs. Reference IDs; do not redefine risk or recommendation content.
- Where a report chapter contains a Mermaid diagram, note the diagram reference for that slide rather than converting relationships into prose bullets.

**Format**: Markdown with `## Slide N: Title` headings, bullet-form content, and a `---` separator between slides.

**PPT generation**: If the user explicitly requests a `.pptx`, suggest using the `ppt-master` skill with `slides-outline.md` and the `assets/` directory as source material. Do not generate a `.pptx` through any other pipeline. If `ppt-master` is unavailable or export is blocked, `slides-outline.md` is the complete fallback; state the limitation explicitly.
