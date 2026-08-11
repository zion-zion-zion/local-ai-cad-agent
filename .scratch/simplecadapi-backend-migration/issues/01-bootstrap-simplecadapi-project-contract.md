# 01 — Bootstrap SimpleCADAPI Project Contract

**What to build:** New projects automatically run on the repository-local SimpleCADAPI backend with durable project/model metadata and startup diagnostics, so the application has one explicit CAD contract before a Run begins.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] A new project persists an immutable Project Identity, stable Part identity, project-schema version, CAD Backend name/version, and model-contract version; display names and storage locations do not act as identities.
- [ ] The application environment uses the vendored SimpleCADAPI package rather than an unrelated global installation.
- [ ] Startup diagnostics verify the declared runtime version, required public imports, rendering support, sandbox access, and a minimal CAD execution smoke test, with actionable failures.
- [ ] New-project behavior does not offer backend selection or require build123d compatibility.
- [ ] Dependency licensing and corresponding source-availability notices for SimpleCADAPI are present.
- [ ] Application-level tests cover project creation, metadata persistence, diagnostics, and the supported runtime contract.
