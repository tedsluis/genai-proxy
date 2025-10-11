# Code Review: genai-proxy

## Scope
- Files reviewed: `main.py`, `README.md`
- Focus: functionality, logging, error handling, configuration, and documentation alignment

## Summary
FastAPI-based OpenAI-compatible proxy that forwards requests to `GENAI_BASE_URL` while injecting a corporate subscription header (`GENAI_SUBSCRIPTION_NAME: GENAI_API_KEY`). Supports JSON responses and SSE streaming for `/v1/chat/completions`, local `/v1/models`, health checks, CORS, retries, and structured logging.

## Strengths
- Clear separation of config, logging, helpers, and routes.
- Sensitive header redaction in logs; API key masked at startup.
- Retry with exponential backoff for common transport errors.
- Proper SSE passthrough with upstream response cleanup.
- Consistent request/response logging and `X-Request-ID` propagation.

## Key Findings and Risks

| # | Finding | Impact | Recommendation |
|---|---|---|---|
| 1 | `SENSITIVE_HEADER_KEYS` includes empty string when `SUBSCRIPTION_NAME` is unset | Redaction check against empty key is unnecessary | Exclude empty string from the set |
| 2 | `req_id` derived from `dict(request.headers).get("X-Request-ID")` | Case-sensitive lookup may miss lowercase `x-request-id` | Use case-insensitive retrieval via `request.headers.get("x-request-id")` before converting to dict |
| 3 | gpt-5 normalization sets `temperature = 1` unconditionally | Overrides client intent | Only set `temperature` if not present |
| 4 | Default `max_completion_tokens` mismatch between code and docs | Code uses `128000`; docs mention `1024` in overview | Align README to `128000` default or change code to match docs |
| 5 | `LOG_BODIES` defaults to `true` | Potential PII leakage in production | Default to `false` and document risks; enable selectively |
| 6 | Health endpoint header injection without validation | Possible `None` header name if env misconfigured | Apply same guard as in general header injection |
| 7 | Unused import `Iterable` | Minor code hygiene | Remove unused imports |
| 8 | No retries on upstream 5xx responses | Reduced resilience | Consider optional retries on 5xx with capped attempts |
| 9 | Streaming timeout equals general timeout | Long streams may be cut off | Consider separate, higher timeout for streaming requests |
| 10 | Stream responses lack `X-Upstream-Status` | Reduced observability | Add `X-Upstream-Status` for streaming path |
| 11 | Mixed language in comments | Inconsistent style | Standardize comments/docstrings to one language |
| 12 | No startup validation of `GENAI_BASE_URL` | Misconfig leads to runtime errors | Validate mandatory env vars at startup and log actionable error |

## Recommended Code Changes
- Header injection:
  - In `_build_forward_headers`, inject subscription header only if `SUBSCRIPTION_NAME` and `SUBSCRIPTION_KEY` are both set.
  - Remove empty string from `SENSITIVE_HEADER_KEYS` when building the set.
- Request ID:
  - Use `req_id = request.headers.get("x-request-id") or str(uuid.uuid4())` to ensure case-insensitive lookup.
- gpt-5 normalization:
  - Set `max_completion_tokens` to `128000` only if neither `max_output_tokens` nor `max_tokens` is provided.
  - Set `temperature` only if absent.
  - Keep `Accept: text/event-stream` when `stream=true`.
- Logging and security:
  - Default `LOG_BODIES` to `false` for production safety; document trade-offs.
  - Log total streamed bytes after streaming completes.
- Streaming and retries:
  - Consider separate timeout for streaming (`STREAM_TIMEOUT` env) and optional retries on 5xx errors.
- Hygiene:
  - Remove unused imports, standardize comment language, and add type hints where helpful.
- Response headers:
  - Include `X-Upstream-Status` in streaming responses, mirroring upstream status code.
- Startup validation:
  - At startup, validate `GENAI_BASE_URL`. If missing, log error and raise.

## Operations & Security
- Treat `LOG_BODIES` with caution; disable by default in production.
- Consider rate limiting and maximum request body size if exposed publicly.
- Monitor retry rates and backoff behavior to avoid thundering herd.

## Documentation Adjustments (README)
- Correct and consistently document gpt-5 normalization:
  - Default `max_completion_tokens = 128000` when not provided.
  - Do not override `temperature` if client sets it.
- Clarify security guidance around `LOG_BODIES` and sensitive data redaction.
- Keep env var spelling consistent; if keeping `GENAI_SUBSCRIPTION_NAME`, add a note explaining the expected value.

## Action Items
- [ ] Guard subscription header injection and remove empty key from `SENSITIVE_HEADER_KEYS`
- [ ] Case-insensitive `X-Request-ID` retrieval
- [ ] gpt-5 normalization: conditional `temperature`, confirm `128000` default
- [ ] Default `LOG_BODIES=false` and update README
- [ ] Add `X-Upstream-Status` to streaming responses
- [ ] Separate streaming timeout configuration
- [ ] Remove unused imports and standardize comments
- [ ] Startup validation for mandatory env vars
- [ ] Align README with code behavior