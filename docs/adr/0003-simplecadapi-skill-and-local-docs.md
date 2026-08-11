# Use the SimpleCADAPI skill with local API retrieval

Status: accepted

The CAD agent replaces its embedded build123d playbook with a curated SimpleCADAPI modeling policy derived from the repository-local skill. Exact API and standard-library pages are supplied through a read-only local documentation tool and DesignSpec-driven preloading rather than injecting the entire documentation tree into every request. Each Run records the SimpleCADAPI version, documentation hashes, and pages consulted so generated Model Source can be audited against the API information available at the time.

## Considered Options

- Inject only the raw SimpleCADAPI `SKILL.md`.
- Inject the complete SDK documentation into every system prompt.
- Combine stable skill rules and indexes with exact local documentation retrieval.

The third option was selected because the raw skill requires exact API reading but does not contain every signature, while the full documentation set would make the static prompt unnecessarily large and harder to cache.

## Consequences

- The model receives a restricted documentation search/read tool that cannot escape the local SimpleCADAPI documentation roots.
- Likely API pages are preloaded from the Ready DesignSpec, and the model can retrieve additional exact pages before writing unfamiliar calls.
- Source validation enforces the skill's stable rules, including public APIs, keyword arguments, one model entry point, explicit result capture, variables for tunable parameters, and consistent tags.
- Build123d identity text, playbook injection, dependency checks, API-specific preflight rules, and prompt tests are removed rather than retained as dormant compatibility behavior.
