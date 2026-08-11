# 05 — Run Safety, Preview, and Finalize

**What to build:** One phased AgentRunner safely carries a Run from DesignSpec through Preview and Finalize, while cancellation, stale intent, concurrency, and artifact publication remain deterministic for the user.

**Blocked by:** 03 — Build, Validate, Replay, and Retain a CAD Revision; 04 — Protect Definitions and Bound Repairs.

**Status:** ready-for-agent

- [ ] One AgentRunner owns the Run phases for planning, documentation, Model Source editing, build, Replay, visual review, Preview publication, and completion.
- [ ] Model Source writes and CAD builds are serialized, each Model Source digest is built at most once per Run, and a new Design Change invalidates obsolete plans, documentation, Replay evidence, Preview identities, and completion waits.
- [ ] Documentation/plan, edit/build/repair, and total-call budgets are enforced with explicit configuration overrides.
- [ ] Stop remains available throughout an active Run, prevents deliberate later work, and preserves the latest successful CAD Revision; terminal events restore idle controls.
- [ ] SimpleCADAPI rendering supplies the Agent's visual-review image while the browser continues to receive the current STL Preview.
- [ ] Only the current Preview identity can satisfy display confirmation; display confirmation is not design approval, and delivery failure blocks completion.
- [ ] Finalize reruns build/Replay and strict BRep/material checks, then atomically publishes validated STEP, STL, render, and summary artifacts tied to the current source digest.
