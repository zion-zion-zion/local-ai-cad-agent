# 06 — Audit, Legacy Cutover, and Full Acceptance

**What to build:** The migrated workflow is auditable and shippable as the only new-project CAD path, with generic quality records, a useful final summary, legacy build123d assumptions removed, and one application-level acceptance flow proving the migration.

**Blocked by:** 01 — Bootstrap SimpleCADAPI Project Contract; 02 — Plan Design Changes with Local Documentation Evidence; 03 — Build, Validate, Replay, and Retain a CAD Revision; 04 — Protect Definitions and Bound Repairs; 05 — Run Safety, Preview, and Finalize.

**Status:** ready-for-agent

- [ ] Run and Attempt records retain Model Plan, documentation, Model Source, repair, build, Replay, Preview, and final Model Result digests plus structured phase/error codes and retry counts.
- [ ] Quality metadata uses generic CAD Backend name/version, model-contract version, documentation hashes, and consulted pages; build123d-specific fields and compatibility semantics are removed.
- [ ] The final summary identifies the Part, DesignSpec, stable identities, Design Parameters, public APIs, validation and Replay evidence, backend/documentation versions, limitations, and skipped operations.
- [ ] Build123d-specific prompt content, dependency checks, execution paths, fixtures, and dormant compatibility behavior are removed; existing legacy projects are explicitly unsupported.
- [ ] Tests cover installation/diagnostics, source and sandbox safety, documentation provenance, persistence and protection invariants, Preview/Finalize gating, and the full application path from Design Change through Finalize.
- [ ] The repository documents and distributes the SimpleCADAPI AGPL-3.0 obligations and corresponding source availability.
