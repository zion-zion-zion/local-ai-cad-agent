# Minimal DesignSpec and Reliable Stop Demo

Status: ready-for-agent

## Problem Statement

The CAD user currently sends a natural-language request directly into the modeling loop. The Agent can therefore start writing and testing CAD code before it has captured the requested parameters, Body, Design Features, Geometric Relations, and Design Requirements in a consistent form. This makes the Agent's interpretation difficult to inspect and can cause avoidable rework.

The application also appears to lack a usable Stop action during model generation. A backend Stop path already exists, but the interface hides the Stop button when streaming begins. The user cannot reliably end an unhelpful Run and may spend tokens on work they no longer want.

This feature is a small, text-only Demo for new projects. It must demonstrate a structured DesignSpec before modeling and make the existing Stop path usable. It is not a production-grade workflow and does not need migration, recovery, exhaustive validation, or per-requirement CAD acceptance.

## Solution

When the existing structured-spec feature flag is enabled, classify each text message as either a Conversation or a Design Change. A Conversation remains read-only. A Design Change first passes through a lightweight DesignSpec stage. That stage produces one current JSON DesignSpec, asks a Clarification only when information blocks modeling, normalizes length values to millimetres, and then automatically continues into the existing CAD Agent loop without asking the user to approve the specification.

Expose the current Ready DesignSpec in a read-only, collapsible interface. A later Design Change directly replaces the current DesignSpec. The Demo supports one Part and stores no DesignSpec history.

Keep the Stop action visible for the full active Run. Clicking Stop must use the existing backend cancellation path, show a stopping state, prevent another submission until the Run ends, and preserve the latest successful CAD Revision. Stop is always initiated by the user; the Demo adds no automatic stopping policy.

## User Stories

1. As a CAD user, I want my text request classified before modeling starts, so that design-changing requests and informational Conversations follow different paths.

2. As a CAD user, I want a Conversation to remain read-only, so that asking a question cannot unexpectedly modify my Part.

3. As a CAD user, I want every Design Change to produce a DesignSpec before CAD code is written, so that the Agent has a structured representation of my intent.

4. As a CAD user, I want the DesignSpec stage to continue automatically, so that I do not need to approve an internal intermediate result.

5. As a CAD user, I want the DesignSpec to summarize my request, so that I can quickly see how the Agent interpreted it.

6. As a CAD user, I want the DesignSpec to list each Design Parameter, so that the important dimensions and quantities are visible.

7. As a CAD user, I want each Design Parameter to retain its original value and unit, so that I can compare the specification with my wording.

8. As a CAD user, I want length parameters normalized to millimetres, so that the downstream CAD Agent receives consistent numeric inputs.

9. As a CAD user, I want angle parameters normalized to degrees when angles are present, so that angular values have a consistent representation.

10. As a CAD user, I want the DesignSpec to identify the Part's Body, so that its primary geometry is explicit before Design Features are applied.

11. As a CAD user, I want the DesignSpec to list holes, slots, fillets, chamfers, patterns, and other Design Features mentioned in my request, so that the intended operations are visible.

12. As a CAD user, I want the DesignSpec to record symmetry, coaxiality, equal spacing, parallelism, and other Geometric Relations, so that spatial intent is not lost in prose.

13. As a CAD user, I want explicit user conditions recorded as Design Requirements, so that the Agent does not silently weaken them during modeling.

14. As a CAD user, I want inferred non-critical choices recorded as Assumptions, so that guesses are distinguishable from my requirements.

15. As a CAD user, I want the Agent to request a Clarification only when missing information blocks modeling, so that minor omissions do not interrupt the Demo.

16. As a CAD user, I want my Clarification answer incorporated before modeling resumes, so that the resulting DesignSpec contains the required information.

17. As a CAD user, I want a Ready DesignSpec to continue into the existing model generation and CAD verification loop, so that structured intent leads to a rendered Part.

18. As a CAD user, I want a later Design Change to use the current DesignSpec as context, so that unspecified design details remain available.

19. As a CAD user, I want a later Design Change to replace the current DesignSpec, so that the Demo remains simple and shows only the latest intent.

20. As a CAD user, I want to view the current Ready DesignSpec in a collapsible panel, so that it is available without taking over the main chat interface.

21. As a CAD user, I want the DesignSpec panel to be read-only, so that the JSON does not become a second editing workflow.

22. As a CAD user, I want the DesignSpec view to refresh when a new Ready DesignSpec is stored, so that the interface shows the latest Design Change.

23. As a CAD user, I want the structured-spec Demo controlled by the existing feature flag, so that I can return to the current workflow when needed.

24. As a CAD user, I want Stop to remain visible while the DesignSpec is being generated, so that I can abandon an unwanted request early.

25. As a CAD user, I want Stop to remain visible while model content and reasoning stream, so that I can end an unhelpful response.

26. As a CAD user, I want Stop to remain visible while CAD or terminal tools execute, so that I can end a long-running tool operation.

27. As a CAD user, I want Stop to remain available while the Run waits for a Clarification or preview, so that I can abandon the active Run cleanly.

28. As a CAD user, I want visible feedback after clicking Stop, so that I know the request was accepted.

29. As a CAD user, I want new message submission disabled while stopping, so that two Runs cannot overlap.

30. As a CAD user, I want an incomplete streamed reply marked as stopped, so that it is not mistaken for a completed answer.

31. As a CAD user, I want Stop to preserve the latest successful CAD Revision, so that ending the current Run does not undo completed work.

32. As a CAD user, I want Stop to avoid launching further model rounds or tools after cancellation, so that the application does not intentionally consume more tokens.

33. As a CAD user, I want Stop to be a manual action, so that normal CAD repair work is not terminated by an unreliable automatic heuristic.

34. As a developer, I want the Demo to use the existing OpenAI-compatible client and question flow, so that it fits the current application architecture.

35. As a developer, I want the Demo to use the existing Run and CAD Revision behavior, so that it does not create a parallel task or revision system.

36. As a developer, I want a failed Demo request to surface an ordinary error, so that the prototype does not require a recovery state machine.

37. As a developer, I want the feature scoped to new text-only projects, so that migration and multimodal behavior do not delay the demonstration.

38. As a developer, I want external-behavior tests around the API and client state, so that the Demo can change internally without rewriting its tests.

## Implementation Decisions

- Reuse the existing structured-spec configuration flag. It remains disabled by default so the current workflow is unchanged unless the Demo is explicitly enabled.

- Support only new projects used after the Demo is enabled. Do not inspect, migrate, or reconstruct a DesignSpec for an older project.

- Support text requests only. Reference-image interpretation is not part of the DesignSpec stage in this Demo.

- Support one Part. Assemblies, mates, and cross-part constraints are not represented.

- Add a lightweight stage before the existing CAD Agent loop. The stage classifies the request as a Conversation or Design Change and uses the configured OpenAI-compatible model with a small prompt and constrained structured output.

- A Conversation is read-only. It may use the current DesignSpec and project status as context, but it receives no interface capable of changing the DesignSpec or CAD model.

- A Design Change produces a DesignSpec before any CAD-writing or CAD-execution interface becomes available. A Ready DesignSpec proceeds automatically without user approval.

- Reuse the existing Clarification question flow when a critical dimension or other blocking fact is absent. Non-critical missing information becomes an Assumption.

- Keep one current DesignSpec in project-internal JSON storage. Store it atomically and replace it directly after each successful Design Change. Do not create DesignSpec revisions or history.

- Use a deliberately small schema containing: schema version, readiness status, request summary, Design Parameters, Body, Design Features, Geometric Relations, Design Requirements, and Assumptions. Pending Clarifications may exist while preparing the specification but must be absent from a Ready DesignSpec.

- A Design Parameter contains a name, quantity type, original value and unit, normalized value and unit, and whether it came from a user statement or an Assumption. Normalize lengths to millimetres and angles to degrees.

- Body contains a type and short description. A Design Feature contains a type and short description. A Geometric Relation contains a type and short description. Design Requirements and Assumptions are short textual statements. The Demo does not add a feature dependency graph, stable cross-reference IDs, or executable requirement mapping.

- A later Design Change receives the current DesignSpec as input and returns a complete replacement. Explicit new values replace previous values; omitted values may be retained; new requirements may replace previous Assumptions.

- Expose a read-only endpoint for the current Ready DesignSpec. Return an empty/not-available result before one exists rather than inventing a specification.

- Publish a project-scoped update event after storing a Ready DesignSpec. The client uses it to refresh a read-only, collapsible DesignSpec view.

- Keep the current backend Stop operation and strengthen its client behavior instead of creating a second cancellation subsystem.

- Track whether a Run is active separately from whether a thinking indicator is visible. Streaming events must not hide Stop while a Run remains active.

- Clicking Stop immediately changes the client to a stopping state, disables Stop and new submissions, and sends the existing project-scoped stop request.

- The client returns to idle only after the server reports that the Run stopped or otherwise reached a terminal state. Any incomplete displayed assistant response is marked stopped.

- Backend cancellation remains best-effort for an in-flight upstream model request. Stop must prevent deliberate subsequent model rounds, stop active CAD or terminal subprocesses through the existing mechanism, and preserve the latest successful CAD Revision.

- Do not add automatic no-progress detection, automatic token budgets, or browser-disconnect cancellation.

- If DesignSpec generation or the happy-path integration fails, report an error and leave retry or project deletion to the user. Do not add retry orchestration, rollback, stale-state reconciliation, or a recovery state machine.

## Testing Decisions

- Tests assert externally visible behavior: HTTP responses, persisted project outputs, published project events, client control state, and whether CAD mutation was allowed. They do not assert private method calls or internal class layout.

- The primary seam is a Flask application plus AgentRunner integration test using a temporary new project and a deterministic Fake LLM. This follows the existing acceptance and application test suites, which already submit chat requests, fake model tool calls, wait for the Runner, and inspect project-visible results.

- The primary happy-path test enables structured spec, submits a text Design Change, observes a Ready DesignSpec through the read-only API, and verifies that the existing CAD loop is entered only after that specification exists.

- A Conversation test verifies that an informational message can produce a response without changing the current DesignSpec or model source.

- A Clarification test verifies that a blocking question pauses before CAD mutation and that answering it allows a Ready DesignSpec and normal modeling to continue.

- A feature-flag test verifies that the disabled setting preserves the existing direct chat-to-CAD behavior.

- A Stop integration test exercises the existing project-scoped endpoint during an active Run and verifies that the Run reaches the stopped state without deleting the latest successful CAD Revision.

- The second seam is a small Node client-state test using the repository's existing `node:test` convention. It verifies the visible behavior of Run states: Stop remains visible during stream start and tool activity, clicking it produces a stopping state, and a terminal stop event restores idle controls.

- Do not introduce Playwright or another browser automation stack for this Demo. Do not add tests for migration, image requests, provider billing, socket-level cancellation guarantees, specification history, recovery, or executable CAD acceptance.

## Out of Scope

- Existing-project migration or DesignSpec reconstruction.
- Reference images and multimodal DesignSpec generation.
- DesignSpec approval or an editable specification UI.
- DesignSpec revisions, history, rollback, or links to historical CAD Revisions.
- Assemblies, mates, multiple-Part specifications, or cross-part constraints.
- Executable acceptance conditions, generated CADTests, per-requirement evidence, or requirement-to-feature mappings.
- Feature dependency graphs, localized feature repair, and source-region repair planning.
- Deterministic validation of hole counts, diameters, symmetry, coaxiality, spacing, parallelism, tolerances, or manufacturability against the DesignSpec.
- Automatic stopping based on semantic progress, token use, time, repeated failures, or browser disconnection.
- Guaranteed provider-side cancellation, billing reconciliation, or partial-token accounting.
- Production-grade retry, rollback, crash recovery, stale-state reconciliation, concurrent Run support, or compatibility guarantees.
- A new model, fine-tuning, RAG expansion, multi-Agent orchestration, or support for additional CAD kernels.
- Exhaustive error and corner-case handling beyond returning a readable Demo error.

## Further Notes

- The backend already has a project-scoped Stop endpoint, a shared stop signal, and CAD/terminal subprocess termination. The main observed defect is that the client hides Stop when model streaming starts.

- The codebase already has a question flow, model revision history, Protected Definitions, quality Run storage, SSE events, and an OpenAI-compatible client. The Demo should compose these capabilities rather than replace them.

- Protected Definitions remain source-code protections. Design Requirements remain semantic statements in the DesignSpec; the Demo does not synchronize the two.

- The repository research plan describes a larger Specification-Test architecture. This spec intentionally implements only the minimal structured-spec and Stop demonstration, not that complete research system.

- Use the vocabulary in the root domain glossary: Run, Stop, CAD Revision, DesignSpec, Ready DesignSpec, Part, Body, Design Feature, Geometric Relation, Design Change, Conversation, Clarification, Assumption, Design Requirement, and Protected Definition.
