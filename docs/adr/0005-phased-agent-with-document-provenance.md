# Use a phased AgentRunner with documented local repair

Status: accepted

One AgentRunner owns each Run and advances through DesignSpec, ModelPlan, documentation preparation, Model Source editing, build/replay verification, visual review, and completion. ModelPlan is an internal gate rather than a user approval step. The Agent may use a read-only local SimpleCADAPI documentation tool and a restricted terminal check, but generated Model Source is limited to public SimpleCADAPI APIs. A failed build or replay must trigger documented, localized repair before a full source rewrite is considered; verified fixes may enter experience memory with backend and documentation provenance.

## Consequences

- Tool orchestration remains compatible with the existing SSE and Run state model while adding explicit modeling phases and documentation evidence.
- The tool layer needs a whitelisted documentation search/read surface, provenance tracking, and phase-aware guards around model writes and CAD builds.
- Each ModelPlan is persisted with its Run and summarized through a status event without requiring user approval.
- Context is layered so the stable prompt prefix can remain cached while DesignSpec, ModelPlan, documentation excerpts, source, and verification results are appended dynamically.
- The default budget is eight documentation/plan calls, twenty-four edit/build/repair calls, and forty total calls per Run, with configuration overrides.
- A new Design Change invalidates the active ModelPlan, documentation candidates, pending replay/Preview, and any derived result not bound to the new source digest.
- Protected Definitions remain user-controlled through the application; the Agent may read and preserve them but cannot create, remove, or change them.
- One repeated failure permits up to three localized repairs and then one protected full rewrite; a further failure ends automatic repair and produces a targeted Clarification or blocked result.
- Documentation reads may run concurrently, but source writes and CAD builds are serialized and each source digest may be built only once.
- Phase events expose concise progress without exposing system prompts, private reasoning, or complete documentation payloads.
- Run and Attempt records retain plan, documentation, source, repair, build, replay, Preview, and final result hashes.
- Final `summary.md` records the Part, stable identities, public APIs, Design Parameters, verification evidence, backend/documentation versions, and known limitations.
- Experience memory is searched for matching failures and may be updated only after both build and Replay succeed; current SDK documentation always overrides remembered guidance.
- The completion event remains gated on successful geometry/replay verification and browser preview delivery confirmation.
- Experience records become version- and condition-aware so a fix learned from one SimpleCADAPI release is not silently reused under another.
