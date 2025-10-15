# Tasks: Configure corporate internet proxy support

**Input**: Design documents from `/specs/003-add-the-ability/`
**Prerequisites**: `spec.md` (available), `plan.md` (missing → proceed based on spec)

**Tests**: Not requested explicitly; omit TDD tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure environment and documentation are ready

- [X] T001 Update `README.md` prerequisites to document `HTTPS_PROXY` environment variable: `/home/tedsluis/git/genai-proxy/README.md`
- [X] T002 [P] Add guidance in `genai-proxy.service` to set `Environment=HTTPS_PROXY=http://proxy.domain.org:8080`: `/home/tedsluis/git/genai-proxy/genai-proxy.service`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core behavior enabling all user stories

- [X] T003 Read `HTTPS_PROXY` from environment and expose as config: `/home/tedsluis/git/genai-proxy/main.py`
- [X] T004 Configure a single `httpx.AsyncClient` to use the proxy when `HTTPS_PROXY` is set (applies to all requests, including streaming): `/home/tedsluis/git/genai-proxy/main.py`
- [X] T005 Ensure health endpoints and forwarder use the shared client (no per-request proxy overrides): `/home/tedsluis/git/genai-proxy/main.py`

**Checkpoint**: Foundation ready - proxy-capable client instantiated at startup

---

## Phase 3: User Story 1 - Enable proxy via environment (Priority: P1) 🎯 MVP

**Goal**: When `HTTPS_PROXY` is set, all outbound requests route through the proxy; when unset, requests go direct

**Independent Test**: Start with `HTTPS_PROXY=http://proxy.domain.org:8080`; verify `/health`, `/v1/health`, and upstream calls succeed via proxy (check logs or proxy access logs).

### Implementation for User Story 1

- [X] T006 Support `http://` and `https://` proxy URLs (validate basic format; rely on httpx for parsing): `/home/tedsluis/git/genai-proxy/main.py`
- [X] T007 Streaming path: ensure SSE passthrough works under proxy (uses same client): `/home/tedsluis/git/genai-proxy/main.py`
- [X] T008 Handle malformed/unreachable proxy: log error and propagate as `proxy_error` (HTTP 502) per existing retry/error mapping: `/home/tedsluis/git/genai-proxy/main.py`

**Checkpoint**: User Story 1 fully functional and testable independently

---

## Phase 4: User Story 2 - No authentication on proxy (Priority: P2)

**Goal**: Do not send proxy authentication headers; no credential prompts

**Independent Test**: With a non-auth proxy set in `HTTPS_PROXY`, verify success and confirm no `Proxy-Authorization` header is sent.

### Implementation for User Story 2

- [X] T009 Ensure request header building omits `Proxy-Authorization` and similar sensitive headers (verify existing redaction covers it): `/home/tedsluis/git/genai-proxy/main.py`
- [X] T010 Document in `README.md` that proxy auth is not supported: `/home/tedsluis/git/genai-proxy/README.md`

**Checkpoint**: User Story 2 functional; no proxy auth used

---

## Phase 5: User Story 3 - Clear observability (Priority: P3)

**Goal**: Visible proxy status in logs (enabled/disabled, address)

**Independent Test**: Start with and without `HTTPS_PROXY`; verify startup log line indicates proxy status and address.

### Implementation for User Story 3

- [X] T011 Startup logging: print `HTTPS_PROXY` value (redact credentials if present) and whether proxying is enabled: `/home/tedsluis/git/genai-proxy/main.py`
- [X] T012 [P] README: add a section describing proxy logging and troubleshooting: `/home/tedsluis/git/genai-proxy/README.md`

**Checkpoint**: Operational behavior clear and diagnosable

---

## Phase N: Polish & Cross-Cutting Concerns

- [X] T013 [P] README: Add container run example with `-e HTTPS_PROXY=http://proxy.domain.org:8080`: `/home/tedsluis/git/genai-proxy/README.md`
- [X] T014 [P] Containerfile: Add comment noting proxy can be enabled via `HTTPS_PROXY` env: `/home/tedsluis/git/genai-proxy/Containerfile`
- [X] T015 [P] Service unit: add commented example for `Environment=HTTPS_PROXY=...` and note no auth support: `/home/tedsluis/git/genai-proxy/genai-proxy.service`

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → Phase 3 (MVP) → Phase 4 → Phase 5 → Polish
- User Story order: P1 → P2 → P3

## Parallel Opportunities

- Documentation updates can run in parallel with code changes ([P]) as they touch different files
- Within code, tasks are sequential as they modify `main.py`

## Parallel Example: User Story 3

```bash
Task: "Startup logging for HTTPS_PROXY" (T011)
Task: "README: proxy logging and troubleshooting" (T012) [P]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (proxy-capable client)
2. Complete Phase 3: User Story 1 (enable proxy routing)
3. STOP and VALIDATE: Verify outbound requests route via proxy when set

### Incremental Delivery

1. Add User Story 2 → Test independently → Commit
2. Add User Story 3 → Test independently → Commit
3. Polish items → Commit
