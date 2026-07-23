# Module Boundary Design Reference

This file provides vocabulary and evaluation criteria for analyzing module boundaries during repository onboarding. It is a read-only analysis guide. Do not propose or execute refactors as part of analysis; surface observations and recommendations only.

Source: distilled from `codebase-design/SKILL.md`, `codebase-design/DEEPENING.md`, and `improve-codebase-architecture/SKILL.md`.

---

## Vocabulary

Use these terms exactly when writing findings. Do not substitute "component," "service," "API," or "boundary."

**Module**: anything with an interface and an implementation. Deliberately scale-agnostic — a function, class, package, or tier-spanning slice.

**Interface**: everything a caller must know to use the module correctly: the type signature, but also invariants, ordering constraints, error modes, required configuration, and performance characteristics. Not just the public methods.

**Implementation**: what is inside a module, its body of code. Distinct from Adapter.

**Depth**: leverage at the interface — the amount of behavior a caller can exercise per unit of interface they must learn. A module is **deep** when a large amount of behavior sits behind a small interface; **shallow** when the interface is nearly as complex as the implementation.

**Seam**: a place where behavior can be altered without editing at that place — the location at which a module's interface lives. Where to put the seam is its own design decision, distinct from what goes behind it.

**Adapter**: a concrete thing that satisfies an interface at a seam. Describes role, not substance.

**Leverage**: what callers gain from depth — more capability per unit of interface learned.

**Locality**: what maintainers gain from depth — change, bugs, knowledge, and verification concentrate in one place rather than spreading across callers.

---

## Deep vs Shallow Module Assessment

When analyzing a module, ask:

- How many methods or entry points does the public interface expose?
- How complex are the parameters and return types?
- How much behavior is hidden behind that interface?
- Would a caller need to know internal details to use it correctly?

A **deep module** earns its keep: the interface is small relative to what it does. A **shallow module** adds interface complexity without hiding proportional implementation complexity — it is often a pass-through.

### The Deletion Test

To identify a shallow module: imagine deleting it. If complexity vanishes, it was earning its keep. If complexity reappears spread across N callers, it was a pass-through that added indirection without hiding behavior.

### The Interface is the Test Surface

Callers and tests cross the same seam. If understanding tests requires knowledge of internal implementation, the module shape is probably wrong. Record this as a testability friction finding.

### One Adapter vs Two Adapters

One adapter at a seam means the seam is hypothetical — indirection without genuine variation. Two adapters (typically production and test) means the seam is real. Flag single-adapter seams as shallow-module candidates.

---

## Dependency Categories

When assessing a module's dependencies, classify them. The category determines the depth opportunity and testing approach.

**In-process**: pure computation, in-memory state, no I/O. Always deepenable — no adapter needed. Test through the deepened module's interface directly.

**Local-substitutable**: dependencies that have local test stand-ins (e.g., in-memory database, in-memory filesystem). Deepenable if the stand-in exists. Test with the stand-in; the seam is internal to the deepened module.

**Remote but owned** (Ports and Adapters): services across a network boundary that the team owns. Define a port (interface) at the seam. The deep module owns the logic; transport is injected as an adapter. Tests use an in-memory adapter; production uses an HTTP/gRPC/queue adapter.

**True external**: third-party services the team does not control (Stripe, Twilio, etc.). The deepened module takes the external dependency as an injected port; tests provide a mock adapter.

---

## Architecture Friction Checklist

When reviewing modules, check for these friction signals:

- A caller must coordinate multiple modules to accomplish one domain operation — suggests those modules could be deepened into one.
- A module's public interface exposes internal steps that callers must sequence correctly — suggests the sequence belongs inside the module.
- A business rule appears in two or more modules — classify as `DUP-RULE` per `code-hygiene-taxonomy.md`.
- A module calls into another module's internals (e.g., via package-private access or reflection) — layer leakage; record as a boundary health finding.
- Circular dependencies between modules — record with the specific cycle, impact, and affected layers.
- A module imports from a higher-level layer (domain imports from persistence) — layer inversion; record as a boundary health finding.
- Test code imports production-internal packages — the module's external seam is not the test surface; record as a testability friction finding.

---

## Deepening Opportunity Fields

When a candidate for deepening is identified, record it with these fields:

- **Files**: which files or modules are involved.
- **Problem**: why the current structure is causing friction (shallow interface, layer leakage, circular dependency, missing locality).
- **Solution**: what would change — in plain language, not executable steps.
- **Benefits**: explained in terms of locality and leverage, and how tests would improve.
- **Dependency category**: in-process, local-substitutable, remote-owned, or true external.
- **Recommendation strength**: `Strong`, `Worth exploring`, or `Speculative`.
- **ADR conflict**: if the candidate contradicts an existing ADR, note it explicitly.

Record candidates in `05-module-boundaries.md`. Propose the deepening as a `REC-###` item in `11-refactoring-roadmap.md` only when the friction creates material delivery, correctness, security, or data risk.

**Non-goal**: do not propose, plan, or execute the refactor steps. Report the opportunity and let the team decide.

---

## Domain-Module Mapping

After completing both the domain vocabulary analysis (`domain-and-adr.md`) and the module boundary analysis, produce a domain-to-module mapping in `05-module-boundaries.md`:

- For each domain concept identified, which module owns it?
- Are any domain concepts split across module boundaries without a clear reason?
- Are any modules responsible for multiple unrelated domain concepts?

Record mismatches with evidence IDs and classify their impact. Use `DUP-RULE` or `DUP-CROSS-LAYER` findings when the mismatch results in duplicated business rules.
