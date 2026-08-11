# 04 — Protect Definitions and Bound Repairs

**What to build:** Protected Parameters and Features survive SimpleCADAPI edits and Replay, while repeated failures receive bounded, evidence-backed repair instead of uncontrolled retries or protection weakening.

**Blocked by:** 03 — Build, Validate, Replay, and Retain a CAD Revision.

**Status:** ready-for-agent

- [ ] Protected Design Parameters are tied to stable SimpleCADAPI variable identities, with value, unit, and tolerance checked after every edit.
- [ ] Protected Design Features retain stable semantic names through source boundaries, semantic tags, and traceable Model Graph operations; transient topology identifiers are evidence only.
- [ ] Only the user-facing protection workflow can add, remove, or change a Protected Definition; the Agent can read, preserve, and validate it but cannot weaken it.
- [ ] A repeated failure permits at most three documented localized repairs followed by at most one protected full rewrite, with every attempt passing source and protection validation.
- [ ] Further failure ends automatic repair with a targeted Clarification when missing user information can resolve it, or a terminal blocked result otherwise.
- [ ] Experience records are written only after build and Replay succeed and are scoped by SimpleCADAPI version, relevant APIs, documentation evidence, and operating conditions; current local documentation takes precedence.
