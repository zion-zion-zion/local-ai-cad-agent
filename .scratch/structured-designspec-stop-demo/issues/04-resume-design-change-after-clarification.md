# 04 — Resume a Design Change after Clarification

**What to build:** When a Design Change lacks information that blocks modeling, ask the user through the existing Clarification experience, incorporate the answer into a Ready DesignSpec, and automatically continue the same design into the CAD Agent loop.

**Blocked by:** 02 — Generate and display the first Ready DesignSpec.

**Status:** ready-for-agent

- [ ] The structured stage distinguishes a genuinely blocking omission from a non-critical missing detail.
- [ ] A blocking omission uses the existing typed Clarification UI and pauses before a Ready DesignSpec is stored or CAD mutation begins.
- [ ] While Clarification is pending, the project reports that it is waiting for the user and the current valid DesignSpec, if any, is not replaced by an incomplete draft.
- [ ] A valid answer resumes the pending Design Change rather than being classified as an unrelated new request.
- [ ] The answer is incorporated into the resulting Design Parameter, Design Requirement, or other relevant DesignSpec content.
- [ ] Once no blocking omission remains, the Ready DesignSpec is stored and the existing CAD Agent loop continues automatically without a separate approval step.
- [ ] Non-critical missing details are recorded as Assumptions and do not trigger a Clarification.
- [ ] An application-level Fake LLM test proves the full behavior: Design Change, Clarification, answer, Ready DesignSpec, then CAD modeling.
- [ ] Stopping while Clarification is pending abandons the active Run through the existing Stop behavior and does not overwrite the current Ready DesignSpec.
