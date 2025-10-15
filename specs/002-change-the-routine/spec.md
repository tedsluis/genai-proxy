# Feature Specification: Read models from models.yaml

**Feature Branch**: `002-change-the-routine`  
**Created**: 2025-10-12  
**Status**: Draft  
**Input**: User description: "change the routine list_models (in main.py) in a way that it reads the list of models from a file named models.yaml, instead of having a static list of models in the python code."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Dynamic Model Listing (Priority: P1)

As a developer or client integrating with the proxy, I want the `/v1/models` endpoint to return models defined in a local file (`models.yaml`) so that model configuration can be changed without modifying code.

**Why this priority**: Enables configuration-driven behavior and avoids code deployments for simple model list updates.

**Independent Test**: Update `models.yaml` with a known list, call `/v1/models`, verify the response matches the file content and format.

**Acceptance Scenarios**:

1. **Given** a valid `models.yaml` with multiple models, **When** calling `GET /v1/models`, **Then** the response contains those models in OpenAI-compatible list format.
2. **Given** a missing `models.yaml`, **When** calling `GET /v1/models`, **Then** the endpoint returns an empty list with HTTP 200 and logs a warning.
3. **Given** an invalid `models.yaml` (malformed YAML), **When** calling `GET /v1/models`, **Then** the endpoint returns HTTP 500 with a `proxy_error` message and request ID.

---

### User Story 2 - Minimal Validation (Priority: P2)

As a maintainer, I need the proxy to validate model entries minimally (require `id`) and set defaults for missing fields (`object`, `owned_by`, `created`) to keep compatibility without strict schema enforcement.

**Why this priority**: Prevents malformed responses while keeping configuration simple.

**Independent Test**: Provide `models.yaml` with entries missing optional fields; verify `/v1/models` response fills defaults.

**Acceptance Scenarios**:

1. **Given** an entry with only `id`, **When** calling `/v1/models`, **Then** `object` defaults to `model`, `owned_by` defaults to `genai`, and `created` defaults to current timestamp.

---

### User Story 3 - Operational Robustness (Priority: P3)

As an operator, I want clear logging and error handling behavior when the file is missing or malformed, so I can diagnose issues quickly.

**Why this priority**: Improves reliability and maintainability.

**Independent Test**: Remove the file or add bad YAML; verify logs and HTTP status codes match expectations.

**Acceptance Scenarios**:

1. **Given** a missing file, **When** calling `/v1/models`, **Then** a warning is logged with the path and the endpoint returns an empty list.
2. **Given** malformed YAML, **When** calling `/v1/models`, **Then** an error is logged and the endpoint returns 500 with `proxy_error`.

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

- File not found
- YAML parse error
- Model entries missing required fields (id, object)
- Large file performance considerations

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: The system MUST read model definitions from `models.yaml` at repository root (or working directory).
- **FR-002**: The `/v1/models` endpoint MUST return an OpenAI-compatible list object `{object: "list", data: [...]}` using file content.
- **FR-003**: The system MUST handle missing files gracefully (empty list, 200, warning log).
- **FR-004**: The system MUST handle malformed YAML with a clear error (500 JSON with `proxy_error`).
- **FR-005**: The system SHOULD validate model objects minimally (require `id` and set defaults for `object`, `owned_by`, `created`).

### Key Entities *(include if feature involves data)*

- **Model**: id (string), object (model), created (unix timestamp), owned_by (string)

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Updating `models.yaml` reflects in `/v1/models` output on next request without code change.
- **SC-002**: Missing `models.yaml` returns `{object: "list", data: []}` with HTTP 200 and logs a warning containing the path.
- **SC-003**: Malformed `models.yaml` yields HTTP 500 with `proxy_error` and includes a request ID.
- **SC-004**: Valid entries are returned within 50ms for files up to 100 models on typical hardware.
