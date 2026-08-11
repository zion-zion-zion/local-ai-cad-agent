# 03 — Route Conversations and replace later DesignSpecs

**What to build:** Keep informational Conversations read-only while allowing a later Design Change to use the current DesignSpec as context, replace it with the latest complete intent, and refresh the visible specification before CAD modeling continues.

**Blocked by:** 02 — Generate and display the first Ready DesignSpec.

**Status:** ready-for-human

- [x] The lightweight structured stage classifies each supported text message as a Conversation or Design Change.
- [x] A Conversation can answer from the current DesignSpec and project state but has no capability to write model source, execute CAD mutations, or replace the DesignSpec.
- [x] An application-level test proves that a Conversation produces a response without changing the current DesignSpec or CAD model.
- [x] A later Design Change receives the complete current DesignSpec as context and produces a complete replacement rather than an independent fragment.
- [x] Values explicitly changed by the user replace their earlier values, while details omitted by the later request may remain in the replacement specification.
- [x] A new explicit Design Requirement can replace an earlier Assumption about the same design detail.
- [x] The replacement DesignSpec applies the same millimetre and degree normalization as the initial DesignSpec.
- [x] The replacement is stored as the sole current Ready DesignSpec before the CAD Agent can apply the Design Change; no specification history is retained.
- [x] The read-only API and collapsible client view expose the replacement after the project-scoped update event.
- [x] External-behavior tests cover both routing outcomes and prove that only the Design Change path can mutate the DesignSpec or CAD model.
