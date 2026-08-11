# 03 — Build, Validate, Replay, and Retain a CAD Revision

**What to build:** A planned Design Change produces one canonical SimpleCADAPI Model Source that the trusted runner can safely build and Replay into a validated one-Part/one-Solid CAD Revision.

**Blocked by:** 02 — Plan Design Changes with Local Documentation Evidence.

**Status:** ready-for-agent

- [ ] Canonical Model Source uses the public SimpleCADAPI surface, keyword arguments, variables for tunable Design Parameters, one replayable model entry point, explicit result capture, and one top-level Model Result.
- [ ] Source validation rejects missing or multiple entry points, missing capture, bare tunable literals, positional API calls, private SDK or kernel access, unsafe imports/calls, and broken protection anchors.
- [ ] The trusted sandbox unwraps the Model Result and accepts only a semantic Part containing exactly one valid Solid; raw shapes, Assemblies, Compounds, empty results, disconnected solids, invalid geometry, non-finite metrics, zero volume, and degenerate bounds fail.
- [ ] Successful builds persist Model Graph and session artifacts bound to the Model Source digest, and stale derived artifacts cannot become current after a source change.
- [ ] Every successful result is Replayed without regenerating design intent; Replay repeats the contract checks and compares result count, validity, volume, and bounding-box tolerances.
- [ ] A CAD Revision is retained only after build and Replay succeed, before completion or Preview delivery is announced.
