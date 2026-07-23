# Observability Evidence

This file defines how to assess a repository's observability posture from static, read-only evidence: what signals to look for, how to grade them, and how to avoid over-claiming. Qualify all conclusions in the report language as static-analysis conclusions that were not runtime-verified: the presence of an SDK, rule file, or endpoint does not prove that dashboards exist, alerts fire, or anyone reviews them.

---

## Signal Categories

Inspect each category as text evidence and record findings with `E-###` entries. Never infer runtime behavior from file presence.

### Logging

- Framework and configuration: logger initialization, config files (`logback.xml`, `log4j2.xml`, `zap`/`slog` setup, `winston`/`pino` config, `logging.config`), per-environment level defaults.
- Structure: structured (JSON/key-value) versus free-text logging; field naming conventions; correlation, request, or trace ID propagation in log context.
- Coverage pattern: where log calls concentrate (entry points, error handlers) versus where they are absent (library code, hot paths). Treat call counts from `rg` as coarse volume signals, never as quality proof.
- Hygiene: sensitive-data scrubbing, log-injection handling, level appropriateness.

### Metrics

- Client libraries: Prometheus clients, Micrometer, StatsD, OpenTelemetry metrics.
- Definition points: Counter/Gauge/Histogram/Summary declarations; project-specific business metrics versus only library or framework defaults.
- Exposure: `/metrics` or equivalent endpoints, push gateways, exporters.

### Tracing

- SDK or agent presence: OpenTelemetry, Jaeger, Zipkin, vendor tracing libraries.
- Instrumentation: middleware, interceptors, decorators, or manual span creation on critical paths; context propagation across process and service boundaries (headers, queue message metadata).
- Auto-instrumentation caveat: Java agents, eBPF, and service meshes can produce traces with little visible code. When the stack suggests agent-based tracing, record an inference using the localized label, state its basis, and consider an `H-###` to confirm.

### Alerting

- Rule files: Prometheus alerting rules, Alertmanager config, Grafana alert provisioning, PagerDuty/Opsgenie/Datadog monitor definitions (including Terraform).
- Quality signals when readable: alerts named for user-visible symptoms versus component noise, severity routing, runbook links, SLO/SLI definitions.

### Health and Readiness

- Health and readiness endpoints; `livenessProbe`/`readinessProbe` in Kubernetes manifests; dependency health aggregation (does the endpoint actually check downstreams, or always return success?).

### Dashboards

- Dashboards-as-code: Grafana JSON or provisioning, Datadog/CloudWatch definitions in Terraform or config files.
- Absence of dashboard code does not prove absence of dashboards — they may live entirely in a SaaS UI. Record insufficient evidence using the localized label and raise an `H-###` rather than concluding "no dashboards".

---

## Posture Grading

Grade each category in the owning chapter:

- **Evidence present** — concrete project-specific definitions exist in the repository (config, rules, call sites).
- **Framework defaults only** — only library or framework defaults are visible; no project-specific definitions.
- **No evidence found** — nothing was found; list what was searched.
- **Not applicable** — the category does not apply to this repository type (for example, a CLI with no metrics endpoint).

Localize these four grade labels to the report language and use them consistently throughout the report.

Map grades against the critical paths identified in `02-use-case-model.md`: observability gaps matter most on externally-facing and business-critical paths. A gap on a critical path is a materially stronger finding than a gap in aggregate.

---

## False-Positive and Over-Claiming Cautions

- An imported library is not evidence of use; confirm call sites or initialization before assigning a grade above no evidence found.
- Configuration presence is not evidence of functioning pipelines; qualify every posture statement as unverified at runtime.
- Stale alert rules and dead dashboards are common; when Git history shows no maintenance of these files, note it.
- Never claim that alerts will fire, dashboards are reviewed, or on-call is staffed from static evidence. Route these questions to `H-###`.

---

## Chapter Landing

| Analysis | Primary chapter | Secondary chapter |
| --- | --- | --- |
| Runtime observability posture (health, readiness, alert rules, runtime metrics and tracing) | `06-runtime-and-availability.md` | `09-security.md` when telemetry exposes sensitive data |
| Logging conventions and developer-facing diagnostics | `10-engineering-quality.md` | — |
| Observability gaps on critical paths | `06-runtime-and-availability.md` (finding) | `R-###` when material, `H-###` when runtime confirmation is required |
