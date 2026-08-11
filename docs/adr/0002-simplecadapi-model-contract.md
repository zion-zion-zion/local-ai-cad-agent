# Adopt the SimpleCADAPI model contract for new projects

Status: accepted

Each new project's canonical Model Source is one editable `model.py` using SimpleCADAPI's replayable model entry point and explicit result capture. User-adjustable Design Parameters use SimpleCADAPI variables; the evaluated Model Result, model JSON, and session JSON are derived artifacts for replay, inspection, and audit, not competing sources of truth. A successful Part follows SimpleCADAPI's documented contract and contains exactly one valid Solid.

## Considered Options

- Make model JSON the only editable source.
- Keep a plain top-level geometry result and ignore SimpleCADAPI's graph/model contract.
- Use a SimpleCADAPI model source as canonical and persist its evaluated result as a derived artifact.

The third option was selected because the agent must edit readable source while the graph/model result provides replay and audit value. Enforcing the one-Solid Part contract keeps the application vocabulary aligned with SimpleCADAPI and avoids silently treating a Compound as a Part.

## Consequences

- The prompt, source validator, runner, and revision metadata must understand `@model`, `capture_result`, `Var`, tags, and ModelResult unwrapping.
- Generated Model Source may use only public SimpleCADAPI APIs; trusted runner code may use internal kernel access when required for verification.
- Protected Design Parameters use variables, while protected Design Features keep source markers and also use semantic tags or Model Graph nodes.
- Derived model JSON and session JSON must be tied to the source digest so stale replay artifacts cannot be mistaken for the current CAD Revision.
- Rendering uses SimpleCADAPI's public screenshot renderer with its VTK dependency, while STL remains the first browser Preview format.
- Completion requires the full application, sandbox, replay, geometry, protection, export, and end-to-end acceptance suite rather than a single geometry smoke test.
