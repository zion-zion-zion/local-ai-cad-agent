# 02 — Generate and display the first Ready DesignSpec

**What to build:** For a new text-only project with the structured-spec Demo enabled, turn the first clear Design Change into one current Ready DesignSpec before the Agent can write or execute CAD, then automatically continue into the existing modeling flow and show the specification in a read-only interface.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

- [x] The existing structured-spec feature flag is loaded by application settings and remains disabled by default.
- [x] With the flag disabled, a chat request follows the existing direct Agent flow without requiring or inventing a DesignSpec.
- [x] With the flag enabled, a clear text Design Change passes through a lightweight structured stage before any CAD-writing or CAD-execution capability is available.
- [x] The stage produces one Ready DesignSpec for one Part containing a schema version, request summary, Design Parameters, Body, Design Features, Geometric Relations, Design Requirements, and Assumptions.
- [x] Each Design Parameter records its quantity type, original value and unit, normalized value and unit, and whether it came from a user statement or Assumption.
- [x] Length values are normalized to millimetres and angular values to degrees before the existing CAD Agent receives the Ready DesignSpec.
- [x] The Ready DesignSpec is atomically stored as the project's one current specification and no DesignSpec history is created.
- [x] The existing CAD Agent receives the Ready DesignSpec as context and can begin its normal code-generation and verification loop only after the specification is stored.
- [x] A project-scoped read-only HTTP response returns the current Ready DesignSpec and reports that none is available before the first specification exists.
- [x] A project-scoped update event causes a read-only, collapsible DesignSpec view to display or refresh the current specification without requiring user approval.
- [x] An application-level test with a temporary new project and deterministic Fake LLM proves the order: Design Change, Ready DesignSpec persistence, read-only API visibility, then entry into the existing CAD loop.
- [x] A Demo-stage failure produces a readable error without adding migration, retry orchestration, rollback, or recovery behavior.
