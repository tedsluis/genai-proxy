# genai-proxy Constitution
<!--
Sync Impact Report
- Version change: N/A → 1.0.0
- Modified principles: Initial adoption (new set defined)
- Added sections: Core Principles I–V; Additional Constraints; Development Workflow & Quality Gates; Governance
- Removed sections: None
- Templates requiring updates:
	✅ .specify/templates/plan-template.md: Constitution Check gates align to principles (no file changes)
	✅ .specify/templates/spec-template.md: Requirements format aligns (no file changes)
	✅ .specify/templates/tasks-template.md: Task grouping and gates align (no file changes)
- Runtime guidance: README.md already aligns with local-only accessibility and OpenAI compatibility
- Deferred TODOs: None
-->

## Core Principles

### I. Security & Local-Only Access (NON-NEGOTIABLE)
The proxy MUST be accessible only from the local machine. It has no built-in
authentication and MUST NOT be exposed to other hosts. Enforce:
- Bind container networking to localhost: `-p 127.0.0.1:8111:8111`.
- Ensure firewall blocks inbound access to port 8111 from external networks.
- CORS configuration DOES NOT control network exposure; it only affects
	browser-origin requests. Do not rely on CORS for network isolation.
- Secrets and subscription headers MUST be redacted in logs.

### II. OpenAI API Compatibility
Maintain OpenAI-compatible endpoints and payloads. The proxy MUST:
- Support `/`, `/health`, `/v1/health`, `/v1/models`, `/v1/chat/completions`.
- Normalize `gpt-5*` chat payloads: translate `max_tokens`/`max_output_tokens`
	to `max_completion_tokens` and only set defaults when missing.
- Preserve stream semantics (SSE passthrough) and set proper
	`Accept: text/event-stream` when `stream=true`.
- Avoid breaking changes to request/response shapes; any incompatibility MUST
	be handled via documented normalization.

### III. Observability & Structured Logging
Logs MUST be structured (JSON) and include a unique request ID. Enforce:
- Redact sensitive headers (authorization, proxy-authorization, subscription).
- Control body logging via configuration; in production, bodies SHOULD NOT be
	logged except minimal previews.
- For streams, only preview up to `LOG_STREAM_MAX_BYTES` bytes.
- Never log secrets or personally identifiable information (PII).

### IV. Reliability & Streaming Correctness
The proxy MUST be reliable and respect idempotency:
- Use a shared async HTTP client with connection pooling.
- Apply exponential backoff with bounded retries; restrict retries to
	idempotent methods (e.g., GET) unless explicitly justified.
- For SSE, pass through bytes without buffering entire streams, sanitize
	hop-by-hop headers, and close upstream only after streaming completes.
- Always emit `X-Request-ID` and include upstream status on non-stream responses.

### V. Configuration, Deployment & Versioning
Behavior MUST be environment-driven and deployment-safe:
- Configure via environment variables; validate required settings on startup.
- Run containers as non-root where possible; use localhost binding in runtime
	examples and systemd units.
- Keep CORS disabled unless specific localhost origins are required.
- Use semantic versioning for the proxy (app) and this constitution.
- Document any normalization rules (e.g., `gpt-5` temperature constraints) and
	avoid silently overriding user inputs unless upstream requires it.

## Additional Constraints & Standards

- Header Injection: Only inject the subscription header when BOTH name and key
	are set and non-empty.
- Sensitive Header Set: Build the redaction set from non-empty values; do not
	include empty keys.
- URL Formation: Normalize upstream URLs to avoid double/missing slashes.
- Timeouts: Prefer distinct connect/read timeouts when necessary; document
	operational defaults.
- Logging Defaults: In production deployments, `LOG_BODIES` SHOULD be `false`.
- Limits: Connection and streaming limits SHOULD be configurable for expected
	concurrency.
- Non-JSON Responses: Log content length and type, never raw bytes.

## Development Workflow & Quality Gates

- Constitution Check (Gate): Every change MUST be reviewed for compliance with
	Principles I–V.
- Code Review: Require at least one reviewer to explicitly verify security
	(local-only binding), compatibility (payload normalization), observability
	(redaction, IDs), and reliability (idempotent retries, SSE correctness).
- Tests: Provide health checks, endpoint smoke tests, and streaming passthrough
	tests. Add contract tests for `/v1/chat/completions` normalization.
- Documentation: Update README examples to reflect localhost bindings and
	security guidance. Note that CORS is browser-side only.
- Release Notes: Record breaking changes and normalization adjustments.

## Governance

- Authority: This constitution governs development, reviews, and releases for
	genai-proxy. It supersedes informal practices.
- Amendments: Changes require a PR with rationale, migration notes (if any),
	and an explicit semantic version bump proposal.
- Versioning Policy (Constitution):
	- MAJOR: Redefine/remove principles or governance in a backward-incompatible
		manner.
	- MINOR: Add a new principle/section or materially expand guidance.
	- PATCH: Clarifications, wording, typos, non-semantic refinements.
- Compliance Review: CI and reviewers MUST verify adherence to Principles I–V
	and Quality Gates before merging.

**Version**: 1.0.0 | **Ratified**: 2025-10-12 | **Last Amended**: 2025-10-12