# Diagram Rules

This file defines diagram requirements, format selection, and quality gates for report diagrams produced during repository onboarding analysis. It is the single source of truth for which diagrams to create, in what format, and what constitutes a complete diagram.

Source: consolidates the diagram requirements formerly duplicated across `SKILL.md` and `deliverables.md`, plus usage rules from `c4-architecture/SKILL.md` and `excalidraw-diagram-generator/SKILL.md`. All other files point here; do not restate diagram rules elsewhere.

---

## Default Format

**Mermaid is the default format for all report diagrams.** Use it unless there is a specific reason to use C4 or Excalidraw.

Embed all Mermaid diagrams inline in their owning chapter file. Store exported assets (PNGs, `.excalidraw` files) under `assets/`.

---

## C4 Notation

Use C4 notation only when the diagram's subject maps precisely to one of the four C4 levels:

| Level | Type | Use when |
| --- | --- | --- |
| 1 | C4Context | Showing the system and its external actors, users, and dependencies |
| 2 | C4Container | Showing applications, databases, services, and their runtime relationships |
| 3 | C4Component | Showing internal components of a single container — only when it adds value beyond the container diagram |
| 4 | C4Deployment | Showing infrastructure nodes — only when deployment evidence is available |
| - | C4Dynamic | Showing a numbered request flow — only for complex multi-step workflows |

Context and Container diagrams are the default architecture pair when evidence supports both. Component diagrams are optional. Deployment diagrams require deployment evidence.

### C4 Quality Rules

- Every element must have a label, a short description, and a technology tag when evidenced.
- Relationships must have unidirectional arrows with a verb label and a protocol or transport label when evidenced.
- Never model a shared library as a container. Containers are separately deployable; libraries are not.
- External systems are black boxes — show the interface, not the internals.
- Message brokers: show topics, queues, or clear directional labels rather than one opaque hub node connecting everything.
- Prefer under 20 elements per diagram. When a diagram exceeds 20 elements, split it or raise the abstraction level.

### C4 Anti-Patterns to Avoid

- Bidirectional arrows (use two separate unidirectional arrows if the relationship is genuinely bidirectional and both directions matter).
- Technology implementation detail in element labels (e.g., method names, variable names).
- Mixing abstraction levels within one diagram.
- Container diagrams that model every class or module — that is a Component diagram.
- Relationships that have no label or direction.

---

## Excalidraw

Excalidraw is **optional and supplementary**. It is never a substitute for a required Mermaid chapter diagram.

Use Excalidraw only when:

- A freehand sketch would communicate something that a structured Mermaid diagram would not.
- The user explicitly requests an Excalidraw file.

Store `.excalidraw` files and any exported PNGs under `assets/`. Reference them from the owning chapter as supplementary material only.

---

## Required Diagrams and Trigger Gates

Four diagram types are required when their trigger condition is met. The owning chapter must contain either the diagram or a recorded `## Diagram decision` omission entry. A chapter whose trigger condition is satisfied but has neither a diagram nor an omission entry fails QA.

| Diagram type | Owning chapter | Required when |
| --- | --- | --- |
| System context / actor-dependency relationship | `01-project-overview.md` | One or more external actors, systems, or dependencies are evidenced |
| Runtime topology | `06-runtime-and-availability.md` | Any deployment or runtime unit is evidenced (applies when the chapter is created) |
| Module dependency / boundary graph | `05-module-boundaries.md` | Two or more modules or packages are evidenced |
| Trust / security boundary graph | `09-security.md` | Trust boundaries, privileged flows, or auth surfaces are evidenced |

---

## Optional Diagrams

The following diagram types may be added when they materially improve the chapter. They require no ledger entry and are never QA-blocking, but still follow the quality checklist and evidence constraint below:

- Availability / failure propagation (`06-runtime-and-availability.md`)
- Use-case / primary flow (`02-use-case-model.md`)
- Domain model relationship graph (`03-domain-model.md`)
- Data model / state relationship (`07-data-and-storage.md`)
- API / external dependency graph (`08-api-and-integrations.md`)
- Risk / recommendation priority or roadmap relationship (`11-refactoring-roadmap.md`)

Do not create empty diagrams.

---

## Diagram Decision Ledger

Every chapter that owns a required diagram must append a `## Diagram decision` section recording exactly one outcome per applicable required diagram type:

- **Created** — diagram type, format (Mermaid / C4 / Excalidraw), and a one-line description of what it shows.
- **Not applicable** — localize this status to the report language; use it when the trigger condition is outside scope for this repository, and state the specific reason.
- **Insufficient evidence** — localize this status to the report language; use it when evidence was sought but not found, and list the files, patterns, or paths checked.

A missing or blank `## Diagram decision` section in a chapter owning a required diagram is a QA failure. Recording a localized not-applicable or insufficient-evidence status is valid only when the trigger is genuinely unmet or evidence is absent. Chapters with only optional diagrams do not need this section.

---

## Diagram Quality Checklist

Before marking a diagram as complete:

- Title is present and describes the subject, not just the diagram type.
- All arrows are unidirectional and labeled.
- Technology or protocol labels are present when evidenced (absent when not evidenced — do not invent them).
- Element count is under 20; if over 20, justify or split.
- No relationships are included that are not evidenced by the codebase.
- No internal implementation details appear that belong at a lower abstraction level.

---

## Evidence Constraint

Do not invent relationships. Every element and every relationship in a report diagram must be backed by an `E-###` evidence entry or by a directly observed file, symbol, or configuration value cited in the owning chapter. When evidence is absent, record the localized insufficient-evidence status in the `## Diagram decision` section for required diagrams, and omit optional diagrams rather than speculating.
