# Tasks: Read models from models.yaml

**Input**: Design documents from `/specs/002-change-the-routine/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Not requested explicitly; omit TDD tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure environment and dependencies are ready

- [ ] T001 Update `requirements.txt` to include `PyYAML` (done): `/home/tedsluis/git/genai-proxy/requirements.txt`
- [ ] T002 Verify `models.yaml` exists at repo root and document structure in README: `/home/tedsluis/git/genai-proxy/models.yaml`, `/home/tedsluis/git/genai-proxy/README.md`
- [ ] T003 [P] Ensure container image installs `PyYAML` (wheels) and includes runtime path guidance: `/home/tedsluis/git/genai-proxy/Containerfile`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core behavior enabling all user stories

- [ ] T004 Implement reading models from `models.yaml` in `/v1/models` endpoint: `/home/tedsluis/git/genai-proxy/main.py`
- [ ] T005 [P] Handle missing file with warning and empty list response (HTTP 200): `/home/tedsluis/git/genai-proxy/main.py`
- [ ] T006 [P] Handle malformed YAML with HTTP 500 `proxy_error`: `/home/tedsluis/git/genai-proxy/main.py`

**Checkpoint**: Foundation ready - endpoint uses file-backed configuration

---

## Phase 3: User Story 1 - Dynamic Model Listing (Priority: P1) 🎯 MVP

**Goal**: `/v1/models` returns models from `models.yaml` in OpenAI-compatible format

**Independent Test**: Update `models.yaml` and verify `/v1/models` output matches file content

### Implementation for User Story 1

- [ ] T007 [P] Parse YAML using `yaml.safe_load` and support top-level list or `models:` key: `/home/tedsluis/git/genai-proxy/main.py`
- [ ] T008 Normalize response to `{object:"list", data:[...]}`: `/home/tedsluis/git/genai-proxy/main.py`
- [ ] T009 [P] Log request in existing structured format with redaction; include body when `LOG_BODIES=true`: `/home/tedsluis/git/genai-proxy/main.py`

**Checkpoint**: User Story 1 fully functional and testable independently

---

## Phase 4: User Story 2 - Minimal Validation (Priority: P2)

**Goal**: Validate entries minimally and fill defaults

**Independent Test**: Provide entries missing optional fields; verify defaults in output

### Implementation for User Story 2

- [ ] T010 [P] Require `id` field; skip entries without `id`: `/home/tedsluis/git/genai-proxy/main.py`
- [ ] T011 Default `object` to `model`, `owned_by` to `genai`, `created` to current timestamp: `/home/tedsluis/git/genai-proxy/main.py`

**Checkpoint**: User Story 2 functional; outputs valid models with defaults

---

## Phase 5: User Story 3 - Operational Robustness (Priority: P3)

**Goal**: Clear logging and error mapping for file issues

**Independent Test**: Remove/Corrupt file; verify logs and status codes

### Implementation for User Story 3

- [X] T012 [P] Warning log on missing file (include path, request ID): `/home/tedsluis/git/genai-proxy/main.py`
- [X] T013 [P] Error log on parse failure; return `proxy_error` with `request_id`: `/home/tedsluis/git/genai-proxy/main.py`

**Checkpoint**: Operational behavior clear and diagnosable

---

## Phase N: Polish & Cross-Cutting Concerns

- [ ] T014 [P] README: Document `models.yaml` format and container mount example: `/home/tedsluis/git/genai-proxy/README.md`
- [X] T015 Code cleanup: remove redundant import inside loop; guard header injection (name+key): `/home/tedsluis/git/genai-proxy/main.py`
- [ ] T016 [P] Optional: Set StreamingResponse media_type="text/event-stream" explicitly: `/home/tedsluis/git/genai-proxy/main.py`

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → Phase 3 (MVP) → Phase 4 → Phase 5 → Polish
- User Story order: P1 → P2 → P3

## Parallel Opportunities

- YAML parsing, defaulting, and logging tasks are parallelizable ([P]) as they touch distinct code blocks
- Documentation updates can run in parallel with code cleanup

## Parallel Example: User Story 1

```bash
Task: "Parse YAML using safe_load and support shapes" (T007)
Task: "Normalize response to list format" (T008)
Task: "Log request body when enabled" (T009)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (file-backed endpoint)
3. Complete Phase 3: User Story 1
4. STOP and VALIDATE: Verify `/v1/models` reflects `models.yaml`

### Incremental Delivery

1. Add User Story 2 → Test independently → Commit
2. Add User Story 3 → Test independently → Commit
3. Polish items → Commit
