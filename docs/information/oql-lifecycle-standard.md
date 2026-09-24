---
{
  "schema": "wellmanifest.docs/document/v1",
  "id": "oql-lifecycle-standard",
  "kind": "information",
  "version": 1,
  "title": "OQL configuration and execution lifecycle",
  "status": "draft",
  "owner": "wellmanifest/oql",
  "created": "2026-09-24",
  "updated": "2026-09-24",
  "review_after": "2026-10-24",
  "source_revision": "b803d68ea7e5549d73117bf72b08d94f21761408",
  "affected_repositories": [
    "wellmanifest/oql"
  ],
  "evidence": [
    "repo://wellmanifest/oql/policy.json",
    "repo://wellmanifest/oql/schemas/rollout-review.schema.json",
    "https://github.com/subactor/docs/blob/main/architecture/analysis/maskservice-oql-adoption.md"
  ]
}
---

# OQL configuration and execution lifecycle — 0.1.0

<!-- docs:section purpose -->
## Purpose

Make OQL a verifiable configuration authority across authoring, runtime, hardware,
firmware and deployment. The canonical requirements are the numbered rules in
[`policy.json`](../../policy.json). MUST means required for the applicable profile;
MUST NOT is a prohibition. Projects adopt a pinned package explicitly. This draft
is not retroactive certification of existing Maskservice installations.

<!-- docs:section scope -->
## Scope

HOME is `wellmanifest`; SHAPE is `domain_pack`. Runtime compilers, device drivers,
secret resolution, deployment daemons and OQL execution remain in their owning
projects. This pack defines boundaries and a read-only review-record validator;
it does not introduce a replacement OQL parser or an execution service.

One source of truth means one authority for each declared namespace. It does not
mean one physical file, no replication, or one universal controller. A fleet can
compose a system baseline and device-specific overlays while retaining one owner
and conflict policy for each value. Desired configuration and observed device
state are different facts; neither silently overwrites the other.

<!-- docs:section evidence -->
## Evidence and related standards

Requirements are grounded in the separately owned [Maskservice audit](https://github.com/subactor/docs/blob/main/architecture/analysis/maskservice-oql-adoption.md).
The audit records exact revisions, source hashes, positive controls, reproduced
gaps and unobserved production behavior. Package examples are synthetic twins.

Reuse `wellmanifest/dsl` for manifest/AST classification, `poa` for process
boundaries, `uriprocess` for packaging/provenance, `deployment` for release
lifecycle, `auth-lifecycle` for authorization and `logs` for receipts.
This pack specializes their boundaries for OQL; it does not grant their runtime
authorities. Adoption must pin each dependency actually used; links are navigation.

<!-- docs:section content -->
## Context profiles

| Context | Source or projection | Permitted effect | Required evidence |
| --- | --- | --- | --- |
| Authoring/store | Versioned OQL documents; one declared write authority | Save with validated expected revision | Actor, source graph, resulting digest, conflict result |
| Scenario/HUI | Compiled CONFIG/HARDWARE/EVENT process subset | Explicit query/command through registered URI | Compiler identity, session context, effect classification |
| Hardware configuration | Typed effective parameters derived from OQL | Supported apply mode only | Target identity, lease, source revision, effective readback |
| Firmware update | Immutable firmware artifact plus compatible OQL profile | Authorized installation and boot trial | Image/build/provisioning identity, current-image precondition, recovery |
| Application deployment | Pinned service images and compatible source bundle | Staged release activation | Per-service digest, readiness, source/config revision, rollback |
| Fleet management | Baseline plus owned device overlays and exact target plan | Ordered per-target rollout | Compatibility matrix, waves, per-target state and compensation |
| Simulation/testing | Explicit twin schema/capability contract | Isolated simulation | Simulator revision, differences from hardware, negative tests |
| UI/diagnostics | Read-only projection of desired and observed state | No implicit hardware mutation | Freshness, origin, missing/invalid states, correlation |

### Normative rules

#### OQL-001 — dialect

Declare dialect, grammar version, supported subset, compiler revision and transport contract separately. OQL source, hardware JSON commands, DOQL, SQL and TestQL are not interchangeable. Reject unsupported declarations before effects.

#### OQL-002 — authority

For each configuration namespace declare exactly one writable authority, owner and mutation API. Git seeds, store rows, filesystem replicas, firmware NVS and UI projections have explicit roles; copying does not transfer authority.

#### OQL-003 — composition

Resolve a bounded acyclic include graph with deterministic declared precedence, source digests and authenticated context. Reject duplicate declarations within a layer; cross-layer overrides require an explicit allowlist and provenance. Unknown target selectors must fail closed.

#### OQL-004 — compilation

Compile the complete supported grammar, including comments, escaping, types, units, ranges and cross-field constraints. Regex header recognition alone is not syntax validation. Unknown fields, duplicate JSON keys, non-finite numbers and unsupported versions are rejected.

#### OQL-005 — catalog

Every writable setting has a type, unit, owning source, consumer, apply mode, write operation and verification method. Distinguish supported-writable, read-only, compile-time-only and documentary settings. A SET declaration alone proves no support.

#### OQL-006 — revision

Keep raw source-byte SHA256, effective configuration digest and compiler identity distinct. Bind execution to the complete source graph and context. Compare expected revisions atomically at the authority; never silently perform last-writer-wins updates or omit conflict checks on alternate write routes.

#### OQL-007 — auth

Resolve principal and role from a trusted authenticated boundary. Device execution revalidates capability, audience, resource and expiry. Payload/URL roles, source comments, natural-language plans and this conformance result grant no authority.

#### OQL-008 — secrets

Store only references to provisioned secrets in OQL, manifests and public evidence. Exclude secret values from logs, projections and hashes published as guessing oracles. Secret resolution is scoped, audited and outside compilation.

#### OQL-009 — addressing

Processes use stable logical identities; transport resolution follows authorization. Discovery is an observation, not configuration authority. Confirm device identity and freshness; reject ambiguous, mismatched and unknown destinations.

#### OQL-010 — effects

Classify query, compile, simulate, configure, actuate, deploy and firmware-update separately. Dry-run performs no device writes. Read or UI success cannot imply actuation. Physical command retries require reconciliation, never automatic mutation failover.

#### OQL-011 — leases

Serialize conflicting physical effects with device-validated bounded leases/fencing. Loss of lease triggers documented local safe behavior. A STOP targets the device/channel captured at START, even if configuration changes meanwhile.

#### OQL-012 — idempotency

Bind a mutation identifier to target, payload digest and expected revision. Define deduplication retention and restart behavior; reject same key with different payload. If persistent deduplication is unavailable, declare reconcile-only/no-blind-retry. A header is not proof of deduplication.

#### OQL-013 — state

Expose desired, validated, staged, applying, trial, confirmed, rolled_back, failed, partial and outcome_unknown distinctly. HTTP acceptance, file save, source commit and a healthy unrelated endpoint do not establish applied configuration.

#### OQL-014 — readback

Confirmation binds target identity, requested and observed configuration digests, firmware identity, observer and timestamp. Verify both revision and effective values/capabilities. Failed or ambiguous verification must not be labelled confirmed.

#### OQL-015 — transactions

Journal config-store and device effects as separate steps with preconditions, recovery and compensation. No cross-device atomicity claim without a supporting protocol. Failed compensation remains partial/unknown and blocks dependent actions.

#### OQL-016 — network

Network/pin changes use staged activation, bounded reconnection, identity-checked readback and a device-local rollback deadline. Persist activation receipts only after confirmation. DNS/LAN readiness alone is not target proof.

#### OQL-017 — firmware

Bind each update to source revision, exact image digest, board/variant, compiler/build inputs, provisioning contract, supported OQL/API schemas and current-image precondition. Verify provenance through the deployment trust policy; a supplied SHA256 proves integrity, not publisher authenticity.

#### OQL-018 — firmware-activation

Before update verify safe idle outputs and exclusive maintenance. Use a recoverable inactive image or an explicit alternative recovery method. Preserve identities, keys and calibration; confirm running image plus hardware readiness after boot, otherwise roll back. Never flash a compile-test image as a provisioned production release.

#### OQL-019 — fleet

An immutable fleet plan binds the exact target set, per-device desired revisions, compatibility matrix, dependency waves and failure policy. Preserve device-specific overlays, calibration and secrets. Stop progression on failure; record per-device partial success and recovery. A global boolean cannot erase partial rollout.

#### OQL-020 — delivery

Keep built, tested, committed, published, installed, running and verified release states separate. Pin image/bundle digests and source graph; mutable tags and repository fast-forward alone are insufficient deployed-version evidence.

#### OQL-021 — telemetry

Return channel identity, physical/virtual origin, presence, validity, freshness, saturation, raw unit and calibration revision. Missing configured hardware must not become a valid virtual zero. Support arbitrary declared channels independently of logical NC/SC/WC labels.

#### OQL-022 — polling

Declare deadlines, freshness limits, single-flight/coalescing and bounded load. Query caching preserves timestamp/origin; expired data is not fresh success. Give safety STOP/control priority over diagnostic polling.

#### OQL-023 — errors

Preserve correlation across process, adapter and device; report source, stage, target, code, retry disposition and reconciliation action. Generic hardware-unavailable errors must not prescribe repairs for an unrelated transport.

#### OQL-024 — tests

Pin simulator capability/schema versions and declare deviations from real hardware. Require negative auth, conflict, duplicate/replay, lost-response, partial failure, reboot rollback and missing-channel tests for applicable effects. Simulation success does not establish physical conformance.

#### OQL-025 — migration

Version the contract and provide explicit migrations for renamed keys, units, layer authority and capability changes. Seed deployment must not overwrite newer active device configuration; downgrade compatibility and rollback state are explicit.

#### OQL-026 — adoption

Adoption records pin this standard and map rules to owned implementations, tests and exceptions. Separate implemented, partial, absent, unobserved and not_applicable. Publish scope/revisions/coverage; a source-only audit cannot attest production enforcement.

### Lifecycle and failure semantics

```text
authored → validated → staged → applying → trial → confirmed
                               ↘ failed / outcome_unknown / partial
                                             ↓ reconciliation
                                      rolled_back or confirmed
```

`trial` is mandatory when the chosen apply mode requires it. A saved profile can
remain desired while the device still runs a previous confirmed revision. The
operator must see both. A lost response is `outcome_unknown`; first observe the
same target and operation before any retry. Firmware and network changes need
recovery that survives loss of the orchestrator. Cross-device progress is a saga
with explicit compensation, not an implied distributed transaction.

A complete firmware/application release binds at least: source Git revision and
cleanliness, build inputs/toolchain, artifact digest, hardware variant, provisioning
contract, compatible OQL/compiler/API versions, expected current state, exact
target identity, backup/recovery, rollout ordering and post-activation readback.
OQL may refer to that release contract; it MUST NOT turn an arbitrary URL or shell
string into unrestricted firmware execution. Artifact authenticity requires an
operator-trusted provenance verifier; a caller-supplied digest alone is insufficient.

### Parameter ownership and migrations

A settings catalog is an executable contract shared by compiler, UI and consumer.
For example `NC → CH0, SC → CH1, WC → CH2` is a default logical mapping; discovering
an ADC on CH4 does not authorize automatic remapping or calibration changes.
A displayed setting with no implemented writer is labelled documentary/read-only.
Compile-time ADC gain or sample-rate changes need a firmware capability/migration
contract; inventing a SET key does not implement the change.

Device overlays own identity, calibration and provisioning references. An upgrade
imports a seed only when there is no active owned value, or through an explicit
versioned migration with conflict checks. Fleet synchronization never replaces an
entire mutable table from a stale read without authority-side CAS and a transaction
or recoverable journal. Compatibility routes obey the same requirements as new APIs.

### Conformance and adoption

[`rollout-review.schema.json`](../../schemas/rollout-review.schema.json) is a
closed review-record format, not executable OQL. Version 1 declares one operation
per device; sequential operations on one device require separate plans with fresh
preconditions. It covers source ownership, parameter support, exact target sets,
revision preconditions, firmware metadata, recovery and readback consistency.

The checker reports only structural and cross-field consistency. It never opens
evidence URLs, contacts devices, verifies signatures or executes source. References
to evidence and successful verification are declarations, not trusted attestations.
Adopters must test their actual grammar, authority and transport boundaries and
obtain independent evidence for enforcement. Rule `verification` in policy.json
separates review requirements from directly checked invariants. A PASS is not full
OQL compliance or permission to deploy.

Adoption records must include package commit/digest, applicable rule IDs, owning
implementation/test paths, observed revisions, exceptions with owner/expiry, and
separate implementation/test/deployment status. An unobserved rule is never PASS;
not_applicable requires a concrete reason. Rollout requires the application's
normal protected authorization. This package supplies no exception mechanism
that can disable runtime safety or authorize bypass.

<!-- docs:section limitations -->
## Limitations

This is an experimental 0.1.0 specification. It does not prove a particular OQL
program correct, define electrical limits, establish physical pressure calibration,
or attest firmware deployed on a device. The validator does not parse OQL, validate
all runtime rule semantics, authenticate receipt issuers, or prove event chronology.
Complete conformance needs adopter adapters and negative integration tests.

<!-- docs:section next_actions -->
## Next actions

Adopters first inventory namespace authority and unsupported SET fields, then
implement parser/CAS/readback gaps, pin the standard, and add contract tests to a
protected build. Qualify firmware rollback and fleet partial failures on a twin
before an authorized hardware canary. Refine profiles for crash-safe journal
recovery, distributed deduplication, telemetry units and calibration lineage,
firmware/OQL migration matrices, and simulator parity using observed failures.
These are follow-up contracts, not claims that existing runtimes implement them.
