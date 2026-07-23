# Code Hygiene Taxonomy

This file is the canonical classification reference for `DUP-###`, `DEAD-###`, and `CMT-###` findings produced during repository onboarding analysis. A finding is a maintenance hypothesis backed by static evidence, not permission to change code.

Source: distilled from `static-code-hygiene-audit/references/taxonomy.md`. The classification rules and confidence scale are reproduced here so this skill is self-contained. Do not run the `static-code-hygiene-audit` skill as a dependency; apply this taxonomy directly.

---

## Shared Decision Rules

### Confidence Scale

- **High**: Evidence covers the relevant scope and closes the main alternative explanations.
- **Medium**: Evidence is strong, but dynamic loading, external consumers, intentional variation, or incomplete scope remains possible.
- **Low**: The finding is based on a limited heuristic or incomplete search; useful only as a review lead.

### Maintenance Impact Scale

- **High**: Likely to cause inconsistent business behavior, security or data defects, broad change amplification, or unsafe removal decisions.
- **Medium**: Creates recurring maintenance cost, misleading understanding, or localized divergence risk.
- **Low**: Mostly readability or cleanup value with limited change risk.

Localize both scales to the report language and use their labels consistently.

### Minimum Evidence Rule

Each finding needs evidence for every cited location and evidence addressing the main false-positive explanation. In companion mode, return evidence descriptors for the parent onboarding report to assign `E-###` IDs. A name search alone is never sufficient proof.

---

## Duplicate Code and Rules (`DUP-###`)

### Subtypes

- `DUP-EXACT`: Meaningful exact or near-exact code repeated in multiple locations.
- `DUP-STRUCTURAL`: The same control flow or transformation with superficial naming or type differences.
- `DUP-RULE`: The same business invariant, permission rule, validation, state transition, or calculation expressed separately.
- `DUP-DATA`: Repeated constants, mappings, schemas, or configuration facts that can drift.
- `DUP-CROSS-LAYER`: A rule duplicated across API, service, domain, persistence, job, or client boundaries.

Assign one primary subtype using this precedence: `DUP-RULE`, `DUP-CROSS-LAYER`, `DUP-DATA`, `DUP-STRUCTURAL`, then `DUP-EXACT`. Add other applicable forms only as secondary tags. Choose the primary subtype by maintenance risk, not textual appearance.

### Required Checks

1. Compare inputs, outputs, side effects, error handling, and dependencies.
2. Identify intentional differences and the reason they exist.
3. Determine whether the locations must change together.
4. Check whether extraction would increase coupling or erase useful domain distinctions.
5. Prefer `DUP-RULE` over structural similarity when the maintenance risk is semantic divergence.

### Common False Positives

- Small idioms and language syntax.
- Framework-required boilerplate.
- Generated or vendored code.
- Test setup duplicated for readability or isolation.
- Similar algorithms serving different domain concepts.
- Deliberate duplication across deployment, trust, performance, or compatibility boundaries.

### Chapter Landing

Own `DUP-EXACT`, `DUP-STRUCTURAL`, and `DUP-DATA` findings in `04-codebase-structure.md`. Own `DUP-RULE` and `DUP-CROSS-LAYER` findings in `05-module-boundaries.md`. Prioritized remediation in `11-refactoring-roadmap.md`.

---

## Dead or Unused Code (`DEAD-###`)

### Subtypes

- `DEAD-UNREACHABLE`: No path from any known production root inside a closed scope.
- `DEAD-UNUSED-INTERNAL`: Internal symbol with no supported production use.
- `DEAD-ORPHAN`: File, module, configuration branch, asset, or registration disconnected from known roots.
- `DEAD-BRANCH`: Condition or state branch contradicted by static constants, types, or state transitions.
- `DEAD-TEST-ONLY`: Reachable only from tests or fixtures.
- `DEAD-COMPAT`: Retained only for compatibility, migration, or external consumers.
- `DEAD-UNRESOLVED`: Suspicious reachability that cannot be settled statically.

### Root Checklist

Check all evidenced roots before classifying any symbol as dead:

- Executables, CLI commands, server entrypoints, and exported library APIs.
- Routes, controllers, handlers, jobs, schedulers, consumers, subscribers, and webhooks.
- Framework annotations, registries, dependency injection, service loaders, and plugin manifests.
- Reflection, serialization, templates, naming conventions, callback strings, and configuration-driven loading.
- Migrations, seed paths, operational scripts, admin tools, feature flags, and environment-specific entrypoints.
- Tests, examples, documentation snippets, and external/public compatibility contracts.

### Classification Rules

- Use `DEAD-UNREACHABLE` only when the inspected scope is closed and every applicable root class was checked. Under sampled coverage (`sampling-strategy.md`), use `DEAD-UNRESOLVED` instead.
- Use `DEAD-UNUSED-INTERNAL` only for non-public symbols with no dynamic or framework-visible path.
- Do not treat test-only code as automatically removable; report its role.
- Do not treat deprecated or compatibility code as dead without checking support commitments.
- Use `DEAD-UNRESOLVED` or lower confidence whenever external consumers or dynamic behavior may exist.

### Chapter Landing

Own `DEAD-###` findings in `04-codebase-structure.md`. Promote to `R-###` only when a dead-code candidate creates a material correctness, security, data, or change-amplification risk. Prioritized remediation in `11-refactoring-roadmap.md`.

---

## Comment Smells (`CMT-###`)

### Subtypes

- `CMT-RESTATE`: Restates names, syntax, or an obvious next operation.
- `CMT-STALE`: Contradicts current behavior, names, types, or configuration.
- `CMT-CODE`: Contains disabled or obsolete code instead of history in version control.
- `CMT-NARRATION`: Excessively narrates implementation steps or repeats each statement.
- `CMT-DUPLICATE`: Repeats nearby documentation without adding local rationale.
- `CMT-TODO`: TODO/FIXME/HACK lacks an owner, condition, rationale, or actionable next step.
- `CMT-MASKING`: Explains confusing code whose naming or structure carries the real maintenance problem.

### Comments to Preserve

- Rationale and rejected alternatives.
- Business invariants and non-obvious edge cases.
- Security, privacy, consistency, concurrency, or performance constraints.
- External protocol, hardware, vendor, or regulatory behavior.
- Compatibility and migration workarounds with removal conditions.
- Legal, license, copyright, generated-file, or tooling directives.
- Required public API documentation.

### Required Checks

1. Compare the comment with the current code and authoritative docs.
2. Decide whether removal would lose information not expressible by names or structure.
3. For commented-out code, check whether version control preserves the history and whether a restoration condition is documented.
4. For TODOs, distinguish a useful tracked constraint from an unowned vague reminder.
5. Classify unclear code separately when a comment is only a symptom of a naming or structure problem.

### Chapter Landing

Own `CMT-###` findings in `10-engineering-quality.md`. Prioritized remediation in `11-refactoring-roadmap.md`.

---

## Cross-Category Rules

- Classify commented-out code as `CMT-CODE`, not dead code, unless active declarations are also unreachable.
- Classify repeated comments as `CMT-DUPLICATE`; classify repeated behavior or rules as `DUP-*`.
- A duplicate region can contain dead code; create separate findings only when each changes the recommended action.
- Do not recommend a shared abstraction solely because text is similar. The proposed action may be documentation, naming alignment, ownership consolidation, generation, or intentional retention.

---

## Safe Suggested Actions

Use non-mutating recommendations only. No deletion or consolidation is authorized by a finding alone.

- Confirm consumers or owners before recommending removal.
- Consolidate a business rule behind an existing boundary.
- Record intentional duplication and its synchronization requirement.
- Remove only after explicit authorization and targeted verification outside this analysis.
- Replace a redundant comment with clearer naming or structure in a separate change.
- Update a stale comment from an authoritative source.
- Convert a valid TODO into a tracked item with a removal or completion condition.

---

## Evidence Integration with the Onboarding Report

When this taxonomy is applied during onboarding analysis, do not create a standalone `docs/static-code-hygiene-audit.md` unless the user explicitly requests it. Instead:

1. Assign findings directly into the onboarding `E-###` register in `appendix-evidence-index.md`.
2. Map each `DUP-###`, `DEAD-###`, and `CMT-###` finding ID to its onboarding `E-###` evidence IDs in the appendix.
3. Preserve confidence ratings, false-positive controls, and human-confirmation needs as stated.
4. Promote to `R-###` only when the finding meets the risk threshold defined in `deliverables.md`.
