# SimpleCADAPI Backend Migration

Status: ready-for-agent

## Problem Statement

The local AI CAD application currently presents a conversational workflow for creating, validating, previewing, revising, protecting, and exporting a Part, but its modeling knowledge, generated Model Source contract, sandbox runner, geometry validation, quality records, and tests are still coupled to build123d.

The repository now vendors SimpleCADAPI and has accepted it as the only CAD Backend for new projects. Merely changing imports would not produce a safe migration: SimpleCADAPI uses a replayable Model Graph, an explicit Model Result, public API and documentation rules, semantic tags, variables for tunable Design Parameters, and stricter single-Part semantics. Without a coordinated migration, the Agent could generate source that appears valid while losing Replay, using stale documentation, weakening Protected Definitions, publishing invalid geometry, or recording misleading quality evidence.

From the CAD user's perspective, the application must keep the familiar conversation, DesignSpec, Run, CAD Revision, Preview, Stop, project-management, and Finalize experience while replacing the underlying modeling contract. New projects must reliably produce one validated Part represented by exactly one solid Body, and every successful result must be reproducible and auditable against the SimpleCADAPI version and documentation used by the Run.

## Solution

Migrate the supported new-project workflow to the repository-local SimpleCADAPI package while retaining the existing product shell and user-facing lifecycle.

Each Design Change will first produce or replace a Ready DesignSpec. One AgentRunner will then create a Model Plan, retrieve the exact local SimpleCADAPI documentation needed for that plan, write one canonical Model Source using only public SimpleCADAPI APIs, and build it inside the existing restricted execution environment. A successful build must return a replayable Model Result for one semantic Part containing exactly one valid Solid. The application will persist Model Graph artifacts tied to the Model Source digest, perform strict Replay and geometry comparison, publish the existing browser Preview, and retain the successful CAD Revision.

Protected Design Parameters will map to stable SimpleCADAPI variables. Protected Design Features will combine user-controlled source boundaries with semantic tags and traceable Model Graph operations. The Agent may preserve these definitions but may not create, remove, or change their protection state.

The Agent will use a small stable SimpleCADAPI modeling policy plus a read-only local documentation search/read surface. Every Run will record the CAD Backend version, model-contract version, consulted documentation pages and hashes, Model Plan, Model Source digests, repair attempts, build and Replay evidence, Preview identity, and final Model Result identity.

Existing build123d projects, migration, translation, detection, and compatibility behavior will not be supported. The migration is complete only when new-project behavior passes application-level acceptance through Design Change, modeling, validation, Replay, Preview delivery, CAD Revision retention, and Finalize.

## User Stories

1. As a CAD user, I want a new project to use SimpleCADAPI automatically, so that I do not need to choose or configure a CAD Backend.

2. As a CAD user, I want the existing conversational modeling experience to remain familiar, so that the backend migration does not require me to learn a new workflow.

3. As a CAD user, I want each supported project to describe one Part, so that the modeling scope is clear and predictable.

4. As a CAD user, I want each Part to contain exactly one solid Body, so that disconnected geometry is not silently presented as a valid Part.

5. As a CAD user, I want a Design Change to update the current DesignSpec before modeling continues, so that the Model Source reflects my latest intent.

6. As a CAD user, I want a Conversation to remain read-only, so that asking a question cannot modify the DesignSpec or CAD model.

7. As a CAD user, I want the Agent to request a Clarification only when missing or conflicting information blocks modeling, so that non-critical details do not interrupt the Run.

8. As a CAD user, I want non-critical choices recorded as Assumptions, so that they remain distinguishable from my explicit Design Requirements.

9. As a CAD user, I want a Ready DesignSpec to continue automatically into modeling, so that I do not have to approve an internal intermediate representation.

10. As a CAD user, I want a new Design Change to invalidate obsolete planning and derived artifacts, so that the application cannot finish an outdated design.

11. As a CAD user, I want each tunable Design Parameter represented by a stable variable, so that future Design Changes can adjust it reliably.

12. As a CAD user, I want each Design Parameter to retain its original value and unit, so that I can relate the model back to my request.

13. As a CAD user, I want lengths normalized to millimetres and angles normalized to degrees for modeling, so that calculations are consistent.

14. As a CAD user, I want tunable values to have explicit units and tolerances where relevant, so that replay and protection checks use unambiguous quantities.

15. As a CAD user, I want non-tunable constants to remain local to the operation that uses them, so that the Model Source stays understandable.

16. As a CAD user, I want the Agent to preserve my Design Requirements across later changes unless I explicitly replace them, so that constraints are not silently weakened.

17. As a CAD user, I want the Agent to derive a Model Plan from the Ready DesignSpec, so that modeling operations and validation checks are deliberate.

18. As a CAD user, I want the Model Plan to remain an internal execution gate, so that planning does not become another approval step.

19. As a CAD user, I want the Agent to use documented public SimpleCADAPI APIs, so that generated Model Source remains supported and auditable.

20. As a CAD user, I want the Agent to read exact local API documentation before using unfamiliar functions, so that it does not guess signatures.

21. As a CAD user, I want standard SimpleCADAPI parts used when they satisfy my request, so that common mechanical geometry is not needlessly reimplemented.

22. As a CAD user, I want all documented SimpleCADAPI arguments passed by keyword, so that generated source is clear and resilient to signature mistakes.

23. As a CAD user, I want generated Model Source to avoid private SDK and kernel APIs, so that my project does not depend on unstable internals.

24. As a CAD user, I want the application to retain the exact documentation evidence used by a Run, so that a generated CAD Revision can be audited later.

25. As a CAD user, I want current SDK documentation to take precedence over remembered fixes, so that stale experience does not override authoritative behavior.

26. As a CAD user, I want local documentation retrieval to remain read-only and restricted to approved roots, so that the Agent cannot use it to access unrelated files.

27. As a CAD user, I want the canonical Model Source to have one replayable model entry point, so that there is one unambiguous build definition.

28. As a CAD user, I want the Model Source to capture its result explicitly, so that the trusted runner can identify the intended output.

29. As a CAD user, I want the captured output to be a semantic Part rather than an arbitrary shape, so that the application can enforce its domain contract.

30. As a CAD user, I want the semantic Part to wrap exactly one Solid, so that compound or multi-solid output is rejected.

31. As a CAD user, I want the editable Model Source to remain the source of truth, so that generated JSON, Preview, and export files cannot compete with it.

32. As a CAD user, I want generated Model Graph and session artifacts tied to the Model Source digest, so that stale artifacts cannot become current.

33. As a CAD user, I want the application to Replay every successful Model Result, so that the result is reproducible without regenerating design intent.

34. As a CAD user, I want Replay to validate the same Part contract as the original build, so that a replayed compound or invalid shape is rejected.

35. As a CAD user, I want original and replayed results compared for result count, validity, volume, and bounding box, so that material divergence is detected.

36. As a CAD user, I want Finalize to perform a stricter BRep and material comparison, so that exported artifacts represent the validated CAD Revision.

37. As a CAD user, I want invalid, empty, non-finite, or zero-volume geometry rejected, so that unusable output is never presented as successful.

38. As a CAD user, I want the application to verify positive three-dimensional bounds, so that flat or degenerate output is not accepted as a Part.

39. As a CAD user, I want intended boolean unions to fail if they do not produce one Solid, so that disconnected pieces are not silently selected or discarded.

40. As a CAD user, I want geometry validation performed inside the trusted CAD execution boundary, so that generated Model Source cannot declare itself valid.

41. As a CAD user, I want the successful CAD Revision retained before completion is announced, so that a later Stop or failure does not erase valid work.

42. As a CAD user, I want the browser Preview to continue using the current delivery flow, so that I can inspect the Part without a viewer migration.

43. As a CAD user, I want the Agent to receive a rendered image for visual review, so that obvious geometric errors can be detected before completion.

44. As a CAD user, I want Preview delivery confirmation tied to the current Preview identity, so that an old or failed Preview cannot complete the Run.

45. As a CAD user, I want Preview delivery confirmation to mean only successful display, so that it is not confused with approval of my design.

46. As a CAD user, I want Finalize to export validated STEP and STL artifacts, so that I can use the Part outside the application.

47. As a CAD user, I want final artifacts published atomically, so that I cannot receive a mixture of old and new outputs.

48. As a CAD user, I want the final summary to describe the Part, Design Parameters, identities, public APIs, validation evidence, and limitations, so that the result is understandable without reading the complete Run log.

49. As a CAD user, I want a protected Design Parameter tied to its stable variable identity, so that later Agent edits cannot bypass the protection by changing formatting.

50. As a CAD user, I want protected parameter value, unit, and tolerance checked after every edit, so that the protection has deterministic meaning.

51. As a CAD user, I want a protected Design Feature to retain a stable semantic name, so that its identity does not depend on transient topology numbering.

52. As a CAD user, I want protected Design Features represented by source boundaries, semantic tags, and Model Graph evidence, so that protection can survive localized edits and Replay.

53. As a CAD user, I want only myself to add, remove, or change Protected Definitions, so that the Agent cannot weaken protections to make a build pass.

54. As a CAD user, I want project and Part identities to remain stable when I rename or move a project, so that revisions and protections remain associated correctly.

55. As a CAD user, I want each CAD Revision associated with its Model Source digest and verification evidence, so that revision history remains trustworthy.

56. As a CAD user, I want restoring a CAD Revision to invalidate newer derived artifacts, so that Preview and Replay evidence cannot refer to a different source.

57. As a CAD user, I want Stop to remain available throughout an active Run, so that I can end unwanted modeling work.

58. As a CAD user, I want Stop to preserve the latest successful CAD Revision, so that ending the active Run does not roll back completed work.

59. As a CAD user, I want a new Design Change to prevent an older Run from publishing completion, so that concurrent intent cannot race.

60. As a CAD user, I want Model Source writes and CAD builds serialized, so that a build cannot evaluate a partially written source.

61. As a CAD user, I want each Model Source digest built at most once per Run, so that retries have explicit new evidence rather than duplicating the same attempt.

62. As a CAD user, I want independent local documentation reads to run concurrently, so that evidence gathering does not unnecessarily slow modeling.

63. As a CAD user, I want failed builds repaired locally when possible, so that a small error does not cause an unrelated full rewrite.

64. As a CAD user, I want repair attempts bounded, so that the Agent cannot consume unlimited time and calls on one repeated failure.

65. As a CAD user, I want a full rewrite attempted only after localized repairs fail and while preserving Protected Definitions, so that escalation is controlled.

66. As a CAD user, I want repeated unresolved failure to end with a targeted Clarification or blocked result, so that the Run fails clearly instead of looping.

67. As a CAD user, I want verified repair knowledge reusable for similar failures, so that future Runs can benefit from successful experience.

68. As a CAD user, I want experience records scoped by SimpleCADAPI version, APIs, documentation, and conditions, so that a fix is not reused outside its evidence.

69. As a CAD user, I want concise phase progress events, so that I can see whether the Run is specifying, planning, reading documentation, modeling, validating, replaying, or preparing a Preview.

70. As a CAD user, I want private reasoning and full documentation payloads excluded from progress events, so that status remains useful without exposing internal context.

71. As a maintainer, I want new projects to have an explicit project schema, immutable Project Identity, CAD Backend identity, and model-contract version, so that persisted state can be validated.

72. As a maintainer, I want the local SimpleCADAPI dependency installed with the application environment, so that supported Runs do not depend on an unrelated global package.

73. As a maintainer, I want startup diagnostics to verify the SimpleCADAPI version, rendering dependency, sandbox access, and core import surface, so that configuration failures are found before a user Run.

74. As a maintainer, I want build123d-specific prompt content, dependency checks, quality fields, and test fixtures removed, so that unsupported compatibility behavior does not remain dormant.

75. As a maintainer, I want quality records to use generic CAD Backend and model-contract metadata, so that observability reflects the actual execution contract.

76. As a maintainer, I want Run and Attempt records to retain plan, documentation, source, repair, build, Replay, Preview, and final-result hashes, so that failures and successes can be reconstructed.

77. As a maintainer, I want the AGPL-3.0 dependency and source-availability obligations documented and distributed correctly, so that the application complies with SimpleCADAPI licensing.

78. As a maintainer, I want one application-level acceptance flow to prove the full migration, so that isolated primitive geometry tests cannot be mistaken for completion.

## Implementation Decisions

- The existing Flask application, OpenAI-compatible client, structured DesignSpec pipeline, Run and Stop lifecycle, project management, CAD Revision history, quality workflow, Protected Definition user interface, browser STL Preview, Preview delivery confirmation, and Finalize user flow will be retained.

- New projects will use the repository-local SimpleCADAPI package as their only CAD Backend. Build123d execution, backend selection, legacy detection, translation, migration, and read-only compatibility will not be implemented.

- The dependency installer and startup diagnostics will install or reference the vendored SimpleCADAPI package in the application environment and verify its public import surface, declared version, rendering dependency, and sandbox availability. Dependency and license documentation will identify SimpleCADAPI and its AGPL-3.0 obligations.

- Every supported project will persist an immutable Project Identity, stable Part identity, project-schema version, CAD Backend name and version, and model-contract version. Display names and storage locations will not act as durable identities.

- The canonical editable artifact will remain one Python Model Source for one Part. Derived Model Graph JSON, session JSON, geometry metrics, Preview assets, renders, and export artifacts will never be alternative editable sources of truth.

- A valid canonical Model Source will use the public SimpleCADAPI import surface, declare all exposed or tunable Design Parameters as variables, contain exactly one replayable model entry point, explicitly capture the intended result, and expose exactly one top-level Model Result.

- The captured value will be a SimpleCADAPI semantic Part containing exactly one valid Solid. A raw arbitrary shape, Assembly, Compound, empty result, or multiple disconnected solids will fail the model contract.

- Generated Model Source will use documented public SimpleCADAPI functions with keyword arguments. It will not use private modules, kernel internals, direct wrapped topology access, arbitrary filesystem access, subprocesses, or network access. Trusted runner code may use restricted kernel inspection only where the public SDK does not expose sufficient verification.

- Source validation will enforce the model entry point, explicit result capture, variable discipline, public API surface, keyword arguments, one-Part/one-Solid result contract, blocked imports and calls, and required Protected Definition anchors before execution.

- Each Ready DesignSpec will be converted into a persisted Model Plan containing Part intent, Design Parameters, ordered Design Features, Geometric Relations, candidate APIs, documentation candidates, protection anchors, validation checks, and anticipated Preview evidence. The Model Plan is internal and does not require user approval.

- The static system prompt will replace the build123d identity and embedded playbook with a compact, stable SimpleCADAPI modeling policy derived from the repository-local skill. Exact API signatures will be supplied dynamically rather than placing the complete documentation tree in the static prompt.

- The Agent tool surface will add read-only local SimpleCADAPI documentation search and read operations. Allowed content will be restricted to approved skill, API, standard-library, core-type, and inspection documentation roots, with path traversal and arbitrary file access rejected.

- Documentation candidates will be preselected from the Ready DesignSpec and Model Plan. The Agent must retrieve the exact page for each unfamiliar public API or standard-library function before writing its use. Documentation pages and content hashes will be retained as Run evidence.

- One AgentRunner will own the complete Run. It will advance through message routing, DesignSpec preparation, Model Plan creation, documentation preparation, Model Source editing, build and Replay verification, visual review, Preview publication, and completion.

- Model Source writes will be prohibited until the current Ready DesignSpec, Model Plan, documentation evidence, project contract, and current Protected Definitions are loaded.

- Independent documentation reads may execute concurrently. Model Source writes and CAD builds will be serialized. A build may not overlap a write, and the same Model Source digest may be built only once in a Run.

- A new Design Change will invalidate the active Model Plan, documentation candidates, pending Replay, pending Preview, unbound derived artifacts, and any completion waiting on an older source or Preview identity.

- The trusted CAD runner will execute Model Source inside the existing Bubblewrap, seccomp, timeout, process, and resource boundaries. It will retrieve the top-level Model Result, unwrap the semantic Part, and verify exactly one Solid.

- Every successful build will validate BRep validity, finite positive volume, finite positive bounding-box dimensions, and the one-Part/one-Solid contract before publishing a CAD Revision or Preview.

- Every successful Model Result will produce Model Graph and session artifacts bound to the Model Source digest. Strict Replay will rebuild the result and repeat type and geometry validation.

- Original and replayed results will be compared using result count, validity, volume, and bounding-box tolerances. Finalize will additionally perform strict BRep/material comparison before export.

- The first browser Preview format will remain STL, preserving the existing viewer and Preview identity confirmation flow. SimpleCADAPI's supported screenshot renderer will produce the rendered image used by the Agent for visual review.

- Finalize will rerun the current Model Source and Replay checks, generate STEP and STL outputs, render the final image, generate the final summary, and atomically publish artifacts tied to the current source digest.

- Protected Design Parameters will use stable SimpleCADAPI variable names and will protect value, unit, and tolerance. Protected Design Features will use a stable canonical name represented by source boundaries, semantic tags, and traceable Model Graph operations. Raw topology or graph node identifiers will be treated as build evidence rather than permanent protection keys.

- Only the user-facing protection workflow may add, remove, or change a Protected Definition. The Agent may read, preserve, and validate protections but may not modify their ownership state.

- Initial or structural modeling may replace the complete Model Source. Local feature repairs will prefer exact bounded replacements, and simple Design Parameter changes may use bounded parameter replacement. Every edit will pass source validation, protection validation, and atomic CAD Revision handling.

- A repeated build or Replay failure will allow up to three documented localized repairs, followed by at most one protected full rewrite. A further failure will produce a targeted Clarification when user information can resolve it or a terminal blocked result otherwise.

- Default Run budgets will distinguish documentation/planning calls, editing/build/repair calls, and total calls. The accepted baseline is eight documentation or plan calls, twenty-four edit/build/repair calls, and forty total calls, with explicit configuration overrides.

- Concise project-scoped phase events will report DesignSpec readiness, Model Plan readiness, documentation loading, Model Source updates, CAD verification, Replay verification, Preview readiness, and Preview display. Events will not expose system prompts, private reasoning, or complete retrieved documentation.

- Run and Attempt records will retain Model Plan digest, documentation paths and hashes, Model Source digests, edit and repair scope, build and Replay outcomes, structured phase/error codes, retry counts, Preview digest, and final Model Result digest.

- Quality environment metadata will use generic CAD Backend name/version, model-contract version, SimpleCADAPI documentation hash, and consulted pages. The build123d-specific version field and compatibility semantics will be removed.

- Experience memory may be searched for matching SimpleCADAPI failures. A new experience record may be written only after both build and Replay succeed and must include SDK version, relevant APIs, documentation evidence, conditions, failure signature, and verified fix. Current local documentation always overrides experience.

- Existing HTTP and SSE user-facing contracts will be preserved where their semantics remain valid. New phase, provenance, Replay, and backend metadata will extend the existing project-scoped records and events without turning the Model Plan into a user approval contract.

- The final project summary will record the Part and DesignSpec summary, stable identities, public APIs, key Design Parameters, build and Replay evidence, CAD Backend and documentation versions, known limitations, and skipped operations.

## Testing Decisions

- Tests will assert externally visible behavior and persisted contracts rather than internal call order or private helper structure. A good test begins with a project state or user action and verifies the resulting DesignSpec, Run events, Model Source acceptance or rejection, CAD Revision, Replay evidence, Preview identity, export artifacts, or audit records.

- The primary and highest testing seam will be the project-scoped application flow through the existing Flask and SSE surface with a deterministic fake LLM and the real AgentRunner orchestration. This single seam should prove the normal path from a Design Change through Ready DesignSpec, Model Plan, local documentation evidence, Model Source creation, sandbox build, Replay, CAD Revision retention, Preview delivery confirmation, and Finalize.

- Focused lower seams are justified only where the application seam would make a safety contract slow or ambiguous. These include Model Source contract validation, the trusted SimpleCADAPI runner and Replay comparator, documentation path restrictions and provenance, Protected Definition validation, derived-artifact digest binding, and atomic final publication.

- AgentRunner tests will cover phase guards, event order visible to clients, call budgets, cancellation, new-Design-Change invalidation, serialized writes/builds, duplicate source-digest suppression, localized repair escalation, Clarification, and terminal blocked behavior.

- CAD Backend tests will cover a minimal valid Part, parameterized feature modeling, standard-library use where applicable, semantic tagging, valid single-Solid booleans, rejected disconnected output, rejected Compound or Assembly output, invalid geometry, zero or non-finite metrics, strict Replay success, Replay divergence, and strict Finalize comparison.

- Model Source validator tests will include positive canonical examples and negative cases for missing or multiple model entry points, missing explicit capture, missing top-level Model Result, bare tunable literals, positional SimpleCADAPI arguments, private API use, direct kernel access, unsafe imports, multiple solids, and broken Protected Definition anchors.

- Documentation tool tests will verify allowed scopes, exact-page retrieval, DesignSpec-driven preloading, content hashing, Run provenance, traversal rejection, symlink escape rejection, unrelated-file rejection, and the rule that current documentation supersedes experience memory.

- Persistence tests will verify immutable Project Identity, stable Part identity, model-contract versioning, source-digest binding for Model Graph and session artifacts, stale-artifact invalidation, CAD Revision restoration behavior, and generic CAD Backend quality metadata.

- Protected Definition tests will verify stable variable protection, value/unit/tolerance enforcement, source-boundary preservation, semantic tag preservation, Model Graph evidence, user-only protection mutations, localized edits, full-rewrite preservation, Replay, and revision restoration.

- Preview and Finalize tests will verify that only the current Preview identity can complete a Run, display confirmation is not user design approval, delivery failure blocks completion, Stop preserves the latest successful CAD Revision, STEP/STL/render artifacts are non-empty, and final publication is atomic.

- Installation and diagnostics tests will verify repository-local package installation, expected SimpleCADAPI version discovery, required rendering support, sandbox import and execution, removal of build123d dependency assumptions, and license/source-availability notices.

- Prior art in the repository includes existing application API tests, deterministic fake-LLM AgentRunner tests, structured DesignSpec tests, Stop and client Run-state tests, sandbox CAD tool tests, finalization tests, CAD Revision and Protected Definition tests, prompt/dependency tests, quality-store tests, and real-CAD acceptance tests. The migration should adapt these behavior patterns instead of inventing a second testing framework.

- A primitive geometry smoke test is necessary for diagnostics but is not sufficient acceptance evidence. Migration acceptance requires the full application seam plus focused safety-contract tests and the relevant repository-local SimpleCADAPI tests for every SDK surface used by the application.

## Out of Scope

- Executing, detecting, importing, translating, migrating, repairing, or displaying existing build123d projects.

- Offering build123d and SimpleCADAPI as selectable or interchangeable CAD Backends.

- Preserving build123d-specific prompts, source contracts, dependency fields, execution paths, fixtures, or compatibility flags.

- Assemblies, mates, cross-part constraints, multiple Parts in one project model, multiple disconnected solids, or compound output treated as one Part.

- Translating SimpleCADAPI Model Graphs to FreeCAD, Fusion 360, SolidWorks, or other CAD systems as part of this migration.

- Replacing the current browser STL Preview with a scene-package, GLB, or graph-native viewer.

- Making generated Model Graph or session JSON directly editable by users.

- Treating Preview display, Model Plan creation, or Ready DesignSpec creation as user approval of the complete design.

- Allowing the modeling Agent unrestricted terminal, filesystem, network, private SDK, or kernel access.

- Automatically adding, removing, or changing Protected Definitions on behalf of the user.

- Building a general-purpose remote documentation service or retrieving live SimpleCADAPI documentation from the network during a Run.

- Guaranteeing backward compatibility for persisted quality records or artifacts created by unsupported legacy project schemas.

- Expanding the application from a local single-user tool into a publicly exposed or multi-tenant service.

- Completing every possible SimpleCADAPI operation or standard-library surface before shipping; only surfaces used by the application and acceptance corpus are required.

## Further Notes

- This specification consolidates the repository's accepted decisions for using SimpleCADAPI, adopting its replayable model contract, retrieving exact local documentation, using stable project/model identity, and running a phased AgentRunner with documented repair.

- The current vendored SDK reference baseline identifies SimpleCADAPI 2.0.4b1. Persisted records must still capture the actual runtime version so that later SDK updates do not silently reinterpret older evidence.

- No separate user feedback on the proposed testing seam was present in the conversation. In accordance with the no-interview instruction, the specification uses the highest existing application seam as the primary acceptance boundary and limits additional seams to deterministic safety contracts.

- The existing early migration draft was normalized into the required issue-tracker specification template and marked `ready-for-agent`; this publication does not implement the migration or create implementation tickets.
