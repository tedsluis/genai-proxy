# Implementation Plan: Read models from models.yaml

**Branch**: `002-change-the-routine` | **Date**: 2025-10-13 | **Spec**: /home/tedsluis/git/genai-proxy/specs/002-change-the-routine/spec.md
**Input**: Feature specification from `/specs/002-change-the-routine/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Change `/v1/models` to load models from `models.yaml` instead of a hardcoded list, returning an OpenAI-compatible list. Handle missing and malformed files with clear logging and appropriate HTTP responses.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, httpx, Uvicorn, PyYAML  
**Storage**: Files (models.yaml)  
**Testing**: pytest (NEEDS CLARIFICATION if in repo)  
**Target Platform**: Linux server (containerized)
**Project Type**: single (proxy service)  
**Performance Goals**: Return models within 50ms for up to 100 entries  
**Constraints**: Localhost-only exposure per constitution; no auth; robust error handling  
**Scale/Scope**: Small config-driven endpoint

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Security & Local-Only (I): No change to exposure. Ensure README/systemd continue binding to 127.0.0.1.
- OpenAI Compatibility (II): Response shape remains `{object:list, data:[models...]}`.
- Observability (III): Log request id; redact headers; add warnings/errors for file issues.
- Reliability (IV): No retries involved; deterministic local file read; errors mapped to 200/500 as specified.
- Config/Versioning (V): Behavior driven by `models.yaml`; documented in README/specs.

Result: PASS.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

**Structure Decision**: Single project repo root. Feature docs under `specs/002-change-the-routine/`. Runtime file `models.yaml` at repo root; mount into container at `/app/models.yaml`.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
