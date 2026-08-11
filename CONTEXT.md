# AI CAD Modeling

This context turns a user's design intent into a validated CAD model through a conversational modeling process.

## Language

**Run**:
One execution of the CAD agent in response to a user request. A Run can finish, fail, or be stopped.
_Avoid_: Job, session

**Stop**:
The user's decision to end the active Run while preserving the latest successful CAD Revision. Stop does not undo completed work.
_Avoid_: Cancel design, rollback

**CAD Revision**:
A retained version of the CAD model. A successful CAD Revision has completed CAD validation and remains available after a Run is stopped.
_Avoid_: Draft file, autosave

**DesignSpec**:
The structured internal representation of the user's current design intent for one Part. Each ready Design Change replaces the current DesignSpec without requiring user confirmation.
_Avoid_: Prompt, user approval contract

**Ready DesignSpec**:
A DesignSpec with no missing or conflicting information that blocks modeling. Ready means modeling can continue; it does not mean the user approved the complete specification.
_Avoid_: Approved specification, final design

**Part**:
A single parameterized CAD object described by a DesignSpec and represented by exactly one solid Body. A Part does not contain an assembly, mates, cross-part constraints, or multiple disconnected solids.
_Avoid_: Assembly, product, compound

**Design Parameter**:
A named quantity used to define a Part. Its original value and unit are retained, while lengths are normalized to millimetres and angles to degrees for modeling.
_Avoid_: Unnamed literal, source variable

**Body**:
The single solid geometry of a Part before its Design Features are applied.
_Avoid_: Complete assembly, rendered mesh

**Design Feature**:
A named geometric element or operation that adds to, removes from, or modifies a Body. A Design Feature can depend on other Design Features without becoming a source-code protection.
_Avoid_: Protected Definition, source region

**Geometric Relation**:
A spatial rule between a Body or Design Features, such as symmetry, coaxiality, equal spacing, or parallelism.
_Avoid_: Visual resemblance, source dependency

**Design Change**:
A user request that changes the intended CAD model. Every Design Change updates the current DesignSpec before modeling continues.
_Avoid_: General chat message

**Conversation**:
A user request for information that does not change the intended Part. A Conversation can read project state but cannot modify the DesignSpec or CAD model.
_Avoid_: Design Change, modeling command

**Clarification**:
A user answer required to resolve information that blocks the DesignSpec. Modeling waits for the Clarification, but the user does not approve the complete DesignSpec.
_Avoid_: Design approval

**Assumption**:
A non-critical design choice made when the request does not supply enough detail. An Assumption is recorded in the DesignSpec and must not replace an explicit user requirement.
_Avoid_: User requirement, hidden default

**Design Requirement**:
An explicit condition from the user that the CAD model must satisfy. A Design Requirement remains in force until a later Design Change explicitly replaces it.
_Avoid_: Fixed constraint, source pin

**Protected Definition**:
A user-controlled protection applied to a generated source parameter or named source feature. It protects source code and is separate from a Design Requirement.
_Avoid_: Design Requirement, semantic constraint

**CAD Backend**:
The geometry engine that turns a Ready DesignSpec into a validated CAD Revision. A CAD Backend is an execution choice, not part of the user's design intent.
_Avoid_: CAD core, renderer

**Model Graph**:
A replayable representation of the modeling operations and geometric relationships that produce one Part.
_Avoid_: Source code, mesh

**Preview**:
A visual representation of a CAD Revision used to inspect the result before final export.
_Avoid_: Final model, source artifact

**Model Source**:
The editable, executable description of one Part that is evaluated by a CAD Backend.
_Avoid_: Prompt, preview

**Model Result**:
The evaluated outcome of a Model Source, including its geometry and any replayable Model Graph data.
_Avoid_: Source revision, rendered image

**Project Identity**:
An immutable identifier for a CAD project that remains stable when its display name or storage location changes.
_Avoid_: Project name, directory name

**Replay**:
The reproduction of a Model Result from its retained Model Graph without regenerating design intent.
_Avoid_: Re-prompting, visual reconstruction

**Model Plan**:
A provisional sequence of modeling operations, API choices, and validation checks derived from a Ready DesignSpec for one Run.
_Avoid_: DesignSpec, source file, user approval
