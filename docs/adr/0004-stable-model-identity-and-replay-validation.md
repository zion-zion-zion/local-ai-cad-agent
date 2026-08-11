# Use stable model identity and strict replay validation

Status: accepted

Every supported project is created under the new SimpleCADAPI project schema with an immutable Project Identity, stable Part identity, CAD Backend metadata, and model-contract version. Its canonical `model.py` exposes exactly one top-level `model_result` produced by one `@model` entry point; the captured value is a SimpleCADAPI Part containing exactly one Solid. Existing build123d projects, legacy detection, read-only compatibility, translation, and migration are outside the scope of this design.

## Consequences

- Project display names and directories may change without changing graph, Part, revision, or protection identities.
- The source validator rejects missing or multiple model entry points, missing explicit capture, non-variable tunable parameters, private SDK/kernel access, non-Part results, and non-public API calls.
- Every successful build performs strict Replay and compares result count, validity, volume, and bounding box within documented tolerances; Finalize additionally performs strict BRep/material comparison.
- Successful derived model JSON and session JSON are stored with their Model Source digest and cannot become current after the source changes.
- Quality records use a new generic schema containing CAD Backend name/version, model-contract version, documentation hash, and documentation pages consulted. The build123d-specific version field is removed.
