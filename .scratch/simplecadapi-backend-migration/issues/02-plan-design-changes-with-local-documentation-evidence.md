# 02 — Plan Design Changes with Local Documentation Evidence

**What to build:** A Ready DesignSpec automatically becomes an internal Model Plan, and the Agent can obtain the exact local SimpleCADAPI documentation it needs through a restricted, auditable read-only surface before writing Model Source.

**Blocked by:** 01 — Bootstrap SimpleCADAPI Project Contract.

**Status:** ready-for-agent

- [ ] Each Ready DesignSpec yields a persisted Model Plan containing Part intent, Design Parameters, ordered Design Features, Geometric Relations, candidate public APIs, documentation candidates, protection anchors, validation checks, and anticipated Preview evidence.
- [ ] Model Plan creation remains an internal execution gate and does not require user approval.
- [ ] Documentation search and read operations are read-only and restricted to approved local roots; traversal, symlink escape, and unrelated-file access are rejected.
- [ ] The Agent retrieves exact pages for unfamiliar public APIs or standard-library functions, and each page is retained with its content hash and Run provenance.
- [ ] The stable modeling policy replaces the build123d playbook while exact signatures are supplied dynamically from local documentation.
- [ ] The application seam proves that planning and documentation evidence are available before Model Source writes, and exposes concise phase events without private reasoning or full documentation payloads.
