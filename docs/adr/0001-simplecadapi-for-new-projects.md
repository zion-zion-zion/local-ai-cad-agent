# Use SimpleCADAPI as the CAD backend for new projects

Status: accepted

The application keeps its existing conversation, DesignSpec, revision, quality, HTTP/SSE, and project-management framework, but new projects use SimpleCADAPI directly as their only CAD Backend. We do not preserve build123d execution or translate old build123d projects; the modeling contract follows SimpleCADAPI's replayable model/graph concepts and remains limited to a single Part. Preview and export formats stay behind the application boundary and may evolve as long as the user can inspect the result and finalization remains verifiable.

## Considered Options

- Keep build123d as the default and add SimpleCADAPI as an optional backend.
- Translate old build123d source into SimpleCADAPI source.
- Use SimpleCADAPI directly for new projects and reuse the surrounding application framework.

The third option was selected because compatibility with old projects is explicitly out of scope, while the surrounding agent and product workflow still provides reusable value.

## Consequences

- The runtime environment must install the local SimpleCADAPI package and its dependencies into the application's CAD execution environment.
- Prompt, source validation, model execution, geometry verification, rendering, and tests must be rewritten around SimpleCADAPI rather than mechanically renamed.
- The project must distribute the accepted AGPL-3.0 dependency and its corresponding source according to that license.
