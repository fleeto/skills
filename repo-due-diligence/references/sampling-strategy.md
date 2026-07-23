# Sampling Strategy

This file defines how to select and declare evidence when a full read of the in-scope codebase is not feasible. Sampling is a declared compromise, not a shortcut: every conclusion drawn from sampled scope carries a coverage qualifier.

---

## When Sampling Applies

Default to full coverage of the in-scope directories. Apply sampling only when the in-scope file count or volume makes a complete read impractical, and declare the sampling plan in the analysis baseline (`appendix-evidence-index.md`) before drawing conclusions from it.

---

## Selection Order

Read in this order. Stop only when the effort budget is reached, and record where you stopped:

1. **Always read fully** (regardless of repository size): repository instructions and README files, dependency manifests, CI/CD configuration, declared entrypoints, top-level directory layout, existing architecture and deployment docs, security-critical paths (authentication, authorization, cryptography, tenant isolation), and the most recent migration files.
2. **Churn-prioritized**: the highest-churn files from the Git signals defined in `code-distribution-and-hotspots.md` (last 90 days or last 500 commits). Read the top of this list fully — churn predicts where defects and knowledge concentrate.
3. **Critical-path following**: code reachable from the entrypoints and use cases identified for `01-project-overview.md` and `02-use-case-model.md`. Follow the primary flows and read what they touch.
4. **Directory-stratified sampling** for the remaining long tail: per top-level directory not yet covered, read the largest files plus any file referenced by two or more already-read files. Record the per-directory sample ratio.

Default exclusions from `code-distribution-and-hotspots.md` (generated, vendored, build output, snapshots, lock files) remain excluded; do not sample them.

---

## Coverage Declaration

- In `appendix-evidence-index.md`, record: the selection rules applied, the thresholds used (churn window, largest-file cutoff), per-directory sample ratios, and an overall coverage estimate (files read / files in scope).
- In each chapter whose conclusions rest on sampled scope, state the coverage basis in one line (for example, `基于约 35% 抽样，选择规则见附录`).
- Confidence for sampled-scope conclusions is capped at `中` unless corroborated by an independent signal (documentation, tests, or CI configuration).

---

## Guards Against False Confidence

- Never claim absence from sampled evidence. Write `在抽样范围内未发现` with the coverage figure, not `不存在`.
- Do not use `DEAD-UNREACHABLE` under sampling; it requires a closed, fully inspected scope (see `code-hygiene-taxonomy.md`). Use `DEAD-UNRESOLVED` instead.
- Do not produce repository-wide LOC or distribution totals from sampled scope; report the measured subset and name it as such.
- Security conclusions (chapter `09-security.md`) must not rest on sampling alone: every security-relevant sink class (authentication, injection, secret handling, tenant isolation) requires either full coverage of its known locations or an explicit `H-###` covering the unexamined remainder.
