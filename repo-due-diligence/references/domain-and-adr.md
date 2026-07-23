# Domain Vocabulary and ADR Reference

This file provides rules for identifying and analyzing domain vocabulary and architectural decisions during repository onboarding. It is a read-only analysis guide, not an active modeling workflow.

Source: distilled from `domain-modeling/SKILL.md`, `domain-modeling/CONTEXT-FORMAT.md`, and `domain-modeling/ADR-FORMAT.md`. This skill does **not** maintain `CONTEXT.md` or ADR files during analysis. Those are separate authoring tasks requiring explicit user authorization.

---

## Purpose During Onboarding

When analyzing a repository, the goal is to:

1. Identify the domain vocabulary the codebase actually uses.
2. Detect overloaded, inconsistent, or missing terms.
3. Map domain concepts to code paths with evidence.
4. Surface ADR suggestions worth raising — not write the ADRs.

Do not manufacture a domain model for utility, infrastructure-only, or tooling repositories. Mark `03-domain-model.md` as `不适用` when no domain concepts are evidenced.

---

## Ubiquitous Language Analysis

### Finding the Vocabulary

Look for domain terms in:

- `CONTEXT.md` or `CONTEXT-MAP.md` at the repository root or within service directories.
- `docs/adr/` for architectural decisions that name domain concepts.
- Entity, aggregate, and value-object class names; function and method names; route names; event names; database table and column names; job and scheduler names; DTO and schema names.
- README, architecture docs, API specs, and inline comments that explain business concepts.

### Overloaded and Inconsistent Terms

Flag when the same word is used for different concepts, or different words are used for the same concept. Examples of patterns to catch:

- `User` in auth context vs. `User` in billing context when they represent distinct objects.
- `Account`, `Profile`, `Customer`, `Client` used interchangeably without evidence they are the same concept.
- A concept named `Order` in the domain layer but `Transaction` in the persistence layer.

Record inconsistencies as evidence items with the locations and the suspected divergence. Do not resolve them — surface them for human confirmation (`H-###`).

### Mapping Domain Concepts to Code

For each confirmed domain concept, record:

- Canonical term as used in the codebase.
- Module, package, or file path where it is primarily defined.
- Whether the same concept appears under different names elsewhere.
- Confidence: `事实` when a direct structural mapping exists (class name, directory name); `推断` when inferred from naming conventions or documentation.

---

## Domain Concept Classification

Classify concepts only when static evidence supports the classification. Do not invent domain structure to fill a template.

- **Entity**: has identity that persists across state changes. Evidence: an identifier field (`id`, `uuid`, etc.) and mutation operations on a named type.
- **Value Object**: defined by its attributes, no independent identity. Evidence: immutable data structures, equality by value, no identifier field.
- **Aggregate**: a cluster of entities and value objects treated as a unit for consistency. Evidence: a root entity that controls access to the cluster, transaction boundaries around the cluster.
- **Domain Service**: stateless operation involving multiple aggregates or external systems. Evidence: a service class or function that coordinates between aggregates without owning state.
- **Domain Event**: a record of something that happened in the domain. Evidence: event classes, event bus, or event-sourcing infrastructure.
- **State Transition**: documented lifecycle of an entity or aggregate. Evidence: status fields with a known set of values, transition guards, state machine code.

Mark all classifications as `推断` unless the codebase explicitly uses DDD terminology or the structure is unambiguous. When evidence is insufficient to classify, say `证据不足` and list what was checked.

---

## ADR Suggestions

Suggest an ADR only when all three conditions are evidenced:

1. **Hard to reverse**: the decision's cost of change is materially high (storage format, public API shape, cross-service coupling, security architecture).
2. **Surprising without context**: a future reader encountering the code would likely question why this approach was chosen.
3. **Real trade-off**: evidence suggests alternatives existed and one was chosen for specific reasons.

If any condition is absent, do not suggest an ADR. Record the observation as a recommendation item (`REC-###`) in `11-refactoring-roadmap.md` instead.

### ADR Suggestion Format

When suggesting an ADR in the report, provide:

- Decision area (one sentence).
- Why it meets all three conditions, with evidence IDs.
- Suggested owner and suggested location (`docs/adr/` or context-specific `docs/adr/`).

Do not write the ADR content. The suggestion belongs in `12-onboarding-guide.md` under "Missing documentation and suggested ADRs."

---

## CONTEXT.md as Evidence Source

If a `CONTEXT.md` exists, read it as a domain glossary. Compare its definitions against actual code names and flag divergences. Do not edit `CONTEXT.md` during analysis. If the file is absent and domain analysis reveals meaningful vocabulary, note its absence as a documentation gap in `12-onboarding-guide.md`.

---

## Domain-Module Friction

When reporting in `05-module-boundaries.md`, compare the domain concept map against the module structure:

- Does a single domain concept span multiple modules without a clear reason?
- Does a single module own multiple domain concepts that should be separated?
- Are domain rules (validation, state transitions, invariants) duplicated across module boundaries? If so, create `DUP-RULE` or `DUP-CROSS-LAYER` findings per `code-hygiene-taxonomy.md`.

Report friction as observations with evidence IDs and confidence. Propose restructuring directions as `REC-###` items only when the friction creates material delivery, correctness, or security risk.
