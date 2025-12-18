# TradePulse Thermodynamic Autonomic Control Layer (TACL) RFC

## 1. Executive Summary
- TACL governs system stability for TradePulse by enforcing monotonic free-energy descent (no self-degrading adaptation without explicit human approval).
- The RFC defines boundaries, invariants, and mechanisms to control autonomous reconfiguration, hot-swaps, and telemetry with auditable decision trails.
- Safety, auditability, resource governance, reproducibility, and event-based sparsity are treated as non-optional constraints with measurable thresholds.
- Free Energy **F** is explicitly modeled as a function of latency, coherency, and resource cost, with stress regimes and hysteresis-driven controls.
- Protocol hot-swaps (RDMA/CRDT/shared memory/gRPC/gossip) are admissible only under quantified triggers and rollback plans.
- CI safety gates, telemetry cadence, and 7-year immutable audit trails are specified to make adaptations falsifiable and reviewable.
- Assumptions are labeled and paired with verification plans to avoid undocumented claims.

## 2. System Boundary & Assumptions
- Boundary: TACL oversees TradePulse runtime decisions affecting transport selection, synchronization mode, and adaptation policies; it does **not** handle business logic or trade decision algorithms.
- Interfaces considered: control plane APIs for adaptation requests, telemetry ingestion, CI/CD deploy gates, and audit log sinks.
- Out of scope: pricing/ML models, UI, and human identity management (treated as trusted inputs).
- Assumptions (A):
  - A1: TradePulse exposes measurable latency and coherency probes per service bond. **Verification**: instrument p95/p99 latency and staleness metrics via telemetry (Section 12).
  - A2: Underlying infra supports immutable, signed logs with 7-year retention. **Verification**: provision WORM storage and verify retention policy via compliance scan.
  - A3: Human approval interface exists for non-monotonic actions. **Verification**: API endpoint or ticket workflow with signature capture and replay ID.

## 3. Problem Statement
- Autonomous adaptations risk self-degradation (latency spikes, coherency loss) if Free Energy is not monitored or bounded.
- Lack of auditability undermines compliance and postmortems when protocol swaps or policy changes occur without traceable provenance.
- Continuous compute without event gating violates resource budgets and can mask instability.

## 4. Constraints & Invariants
- Safety: No uncontrolled degradation; non-monotonic moves require explicit human approval. Violation ⇒ adaptation loops amplify outages.
- Auditability: Maintain 7-year audit trail (decisions, configs, model/policy versions, regime switches). Loss ⇒ unverifiable changes and compliance gaps.
- Resource Governance: Free Energy **F** = f(latency (ms), coherency (version skew), resource cost (CPU/GB/s/network)). Breach ⇒ runaway cost or inconsistency.
- Reproducibility: Deterministic replay with versioned configs and testable interfaces. Absence ⇒ inability to debug or certify releases.
- Event-Based Sparsity: Compute triggered by events/thresholds; avoid always-on overhead. Ignoring ⇒ wasted cycles and reduced stability margin.

## 5. Design Hypotheses
- If **F** increases beyond stress thresholds and coherency risk rises, then adaptive protocol/regime switches are necessary to restore monotonic descent.
- If audit and telemetry cadences are aligned with regime transitions, then rollback and forensics remain feasible within SLO budgets.
- If CI safety gates fail, deploy/auto-adaptation must halt because monotonicity cannot be guaranteed.

## 6. Mechanism Spec
For each mechanism: purpose → inputs → outputs → update rule → metrics → failure modes → safeguards.

### 6.1 Free Energy Measurement
- Purpose: Quantify system cost to enforce monotonic descent.
- Inputs: p95/p99 latency per bond (ms), coherency skew (versions or vector clocks), resource cost (CPU %, MB/s, network MB/s).
- Outputs: Scalar **F** per bond and aggregate.
- Update Rule: `F = w_l*Latency + w_c*CoherencySkew + w_r*ResourceCost`, weights versioned and stored in config repo.
- Metrics: F trend, derivative dF/dt, threshold bands (green < 0.7, amber 0.7–0.9, red > 0.9 normalized).
- Failure Modes: Missing telemetry; weight drift; mis-scaled units.
- Safeguards: Reject updates without unit tags; freeze adaptation if F is Unknown; alert on missing data beyond 2 sampling intervals.

### 6.2 Stress Detection & Regime Control
- Purpose: Detect threat contours and manage hysteresis between regimes (normal, constrained, fail-safe).
- Inputs: F bands, error rates, queue depth, coherency skew.
- Outputs: Regime state with timestamp and signature.
- Update Rule: Hysteresis thresholds (e.g., enter constrained at F>0.85 for 3 intervals; exit when F<0.65 for 5 intervals).
- Metrics: Regime dwell time, oscillation count.
- Failure Modes: Oscillation without hysteresis; delayed detection.
- Safeguards: Minimum dwell timer; backoff; human approval before re-entering normal after fail-safe.

### 6.3 Evolutionary Reconfiguration of Service Bonds
- Purpose: Adjust topology/policy (GA/RL/LinkActivator) only when it lowers F.
- Inputs: Candidate bond configurations, historical F, reward = -ΔF.
- Outputs: Selected configuration with provenance ID.
- Update Rule: Accept candidate if projected F decrease > epsilon and CI gates pass; otherwise reject or queue for human review.
- Metrics: ΔF per change, acceptance rate, rollback count.
- Failure Modes: Overfitting to noisy telemetry; hidden coherency cost.
- Safeguards: Shadow evaluation; canary with rollback; explicit human approval for non-monotonic projections.

### 6.4 Protocol Hot-Swap Engine
- Purpose: Swap between RDMA, CRDT, shared memory, gRPC, gossip to optimize F.
- Inputs: Current regime, F decomposition, transport availability, coherency requirements.
- Outputs: Protocol selection, rollback pointer.
- Update Rule: Only permit swap if projected F decreases and coherency constraints satisfied; log decision with signature.
- Metrics: Swap success rate, rollback latency, coherency error post-swap.
- Failure Modes: Swap increases F; incompatible semantics (e.g., CRDT vs strong consistency).
- Safeguards: Pre-swap simulation; rollback snapshot; human approval if coherency risk > threshold.

### 6.5 Telemetry + API Layer
- Purpose: Expose measured F, regimes, swap events to operators and automation.
- Inputs: Metrics/trace events; adaptation requests.
- Outputs: Signed telemetry streams; API responses with versioned schemas.
- Update Rule: Event-based emission; default cadence 1s for critical bonds, 10s for non-critical, with burst detection.
- Metrics: Telemetry freshness, drop rate, API latency.
- Failure Modes: Telemetry gaps; API overload; schema drift.
- Safeguards: Backpressure; schema version negotiation; circuit breakers; emit Unknown flags when data absent.

### 6.6 CI Safety Gates
- Purpose: Block deploy/auto-adaptation unless tests and invariants pass.
- Inputs: Test suites (latency regression, coherency checks, resource budget tests), policy linters, signature verification.
- Outputs: Pass/fail with artifacts.
- Update Rule: All gates must pass for monotonic actions; non-monotonic requires pass + human sign-off token.
- Metrics: Gate pass rate, false-positive rate, time-to-decision.
- Failure Modes: Flaky tests; bypassed gates.
- Safeguards: Mandatory signing; quarantine on gate failure; immutable logs of decisions.

## 7. Interfaces & Contracts
- Control API: `POST /tacl/adapt` with desired action, projected ΔF, evidence hash; responds with decision ID, status, required approvals. Versioned via semantic schema (vMAJOR.MINOR).
- Telemetry Stream: Signed events `{timestamp, bond_id, F, regime, transport, coherency_skew, resource_cost}`; retention policy 7 years.
- Config Repo: Versioned weights, thresholds, hysteresis settings; changes require CI gates + signature.
- SLA: Adaptation decision latency ≤ 500 ms in normal regime; telemetry freshness ≤ 2s for critical bonds.

## 8. Protocol Hot-Swap Policy
- Admissibility: Swap allowed only if projected F decrease ≥ 5% and coherency constraints satisfied; CI simulations pass; no unresolved alerts.
- Guardrails: Hysteresis timer (no swap more than once per bond per 10 minutes); smoke test before activation.
- Rollback: Pre-swap snapshot; automatic rollback if F not improved within 3 intervals or coherency errors > threshold.
- Human Approval: Required for any swap that risks coherency downgrade or fails monotonic criteria.

## 9. Safety Model (Monotonic Free Energy Descent)
- Formalization: Actions must satisfy `F_after <= F_before - epsilon` unless explicit human approval token present.
- Gating Logic: If telemetry incomplete ⇒ freeze adaptations; if CI gates fail ⇒ block; if human token absent for non-monotonic moves ⇒ reject.
- Enforcement: Decisions signed and logged; runtime asserts F deltas within 2 intervals post-action.

## 10. Rejected Alternatives
- Unbounded autonomous swaps without hysteresis: Rejected—breaks safety and causes oscillations.
- Always-on telemetry and compute: Rejected—violates event-based sparsity and resource governance.
- Heuristic-only decisions without F formalization: Rejected—non-falsifiable and unauditable.

## 11. Verification & Falsifiability
- Tests: Regression tests for latency/coherency; simulation of swap scenarios; replay tests ensuring deterministic decisions given identical inputs/configs.
- Metrics: ΔF distribution, rollback counts, alert MTTR, telemetry gap rate.
- Experiments: Canary swaps with controlled load; chaos tests inducing latency spikes to validate regime control.

## 12. Observability
- Telemetry: Event-driven; cadences in Section 6.5; redlines on freshness (critical >2s gap triggers alert).
- Logs: Immutable, signed; include decision ID, inputs, outputs, signatures; retained 7 years.
- Traces: Propagate decision ID across services; sample at 1% baseline, 10% during red regime.

## 13. Audit Trail & Governance
- Provenance: Every config/policy/model version signed and logged with hash and author.
- Retention: 7-year WORM storage for logs, telemetry summaries, decision records.
- Change Control: All adaptations recorded with diff, ΔF, regime, approvals; reproducible replay supported via versioned inputs.

## 14. Rollout Plan
- Phase 1: Instrument F metrics and telemetry; validate cadences and unit tagging.
- Phase 2: Enable stress detection with hysteresis; dry-run swaps (no activation).
- Phase 3: Canary protocol hot-swaps with automatic rollback; require human approval for non-monotonic cases.
- Kill-Switch: Immediate revert to last known good protocol and freeze adaptations if F unknown or red for >5 intervals.

## 15. Open Questions
- OQ1: Precise weight calibration for F. **Owner**: Systems Eng. **Next**: Collect baseline under load and fit weights.
- OQ2: Coherency skew measurement units across transports. **Owner**: Platform. **Next**: Define normalized vector clock or version skew metric.
- OQ3: Human approval UX for non-monotonic actions. **Owner**: Ops. **Next**: Implement signed token workflow and test replayability.

## Decision Record
- Decision: Adopt TACL with monotonic Free Energy descent and controlled protocol hot-swaps.
- Alternatives: Unbounded swaps; heuristic-only decisions; always-on compute (rejected in Section 10).
- Invariants: Safety, auditability, resource governance, reproducibility, event-based sparsity (Section 4).
- Evidence: Defined F model, hysteresis rules, CI gates, audit/telemetry contracts in this RFC.
- Risk: Misconfigured weights or missing telemetry could block safe adaptations; mitigated via freeze + alerts.
- Rollback: Revert to prior config version; disable adaptation engine; restore last signed regime snapshot.
