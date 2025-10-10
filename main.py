import os
import json
import time
import uuid
import logging
from typing import Dict, Optional, Iterable, AsyncIterator

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# =========================
# Config
# =========================
SUBSCRIPTION_NAME = os.getenv("GENAI_SUBSCRIPTION_NAME")
GENAI_BASE_URL = os.getenv("GENAI_BASE_URL")
SUBSCRIPTION_KEY = os.getenv("GENAI_API_KEY")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "60"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
RETRY_BACKOFF_SEC = float(os.getenv("RETRY_BACKOFF_SEC", "0.5"))
LOG_BODIES = os.getenv("LOG_BODIES", "true").lower() in ("1", "true", "yes")
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
# For streams, we do not log the body by default; optionally you can log the first N bytes:
LOG_STREAM_MAX_BYTES = int(os.getenv("LOG_STREAM_MAX_BYTES", "0"))

SENSITIVE_HEADER_KEYS = {"authorization", "proxy-authorization", SUBSCRIPTION_NAME.lower() if SUBSCRIPTION_NAME else ""}

# =========================
# Logging
# =========================
logger = logging.getLogger("genai_proxy")
_handler = logging.StreamHandler()
_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
_handler.setFormatter(_formatter)
logger.addHandler(_handler)
logger.setLevel(logging.INFO)

logger.info(f"SUBSCRIPTION_NAME={SUBSCRIPTION_NAME}")
logger.info(f"SUBSCRIPTION_KEY={SUBSCRIPTION_KEY[:4] + '*******************' if SUBSCRIPTION_KEY else None}")
logger.info(f"GENAI_BASE_URL={GENAI_BASE_URL}")
logger.info(f"REQUEST_TIMEOUT={REQUEST_TIMEOUT}")
logger.info(f"MAX_RETRIES={MAX_RETRIES}")
logger.info(f"RETRY_BACKOFF_SEC={RETRY_BACKOFF_SEC}")
logger.info(f"LOG_BODIES={LOG_BODIES}")
logger.info(f"ALLOWED_ORIGINS={ALLOWED_ORIGINS}")
logger.info(f"LOG_STREAM_MAX_BYTES={LOG_STREAM_MAX_BYTES}")

def _redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    return {k: ("***REDACTED***" if k.lower() in SENSITIVE_HEADER_KEYS else v) for k, v in headers.items()}

def _safe_json_loads(body: bytes) -> Optional[dict]:
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None

# =========================
# App
# =========================
app = FastAPI(title="GenAI Proxy", version="1.0.0")

if ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.on_event("startup")
async def startup():
    timeout = httpx.Timeout(REQUEST_TIMEOUT)
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
    app.state.client = httpx.AsyncClient(timeout=timeout, limits=limits)

@app.on_event("shutdown")
async def shutdown():
    await app.state.client.aclose()

# =========================
# Helpers
# =========================
def _upstream_url(path: str, query: str = "") -> str:
    base = f"{GENAI_BASE_URL}{path}"
    return f"{base}?{query}" if query else base

def _build_forward_headers(incoming: Dict[str, str]) -> Dict[str, str]:
    headers = {
        "Content-Type": incoming.get("content-type", "application/json"),
    }
    if SUBSCRIPTION_KEY:
        headers[SUBSCRIPTION_NAME] = SUBSCRIPTION_KEY

    skip = {"content-length", "host", "connection", "keep-alive", "transfer-encoding", "te", "trailer", "upgrade"}
    for k, v in incoming.items():
        kl = k.lower()
        if kl in skip:
            continue
        if kl in SENSITIVE_HEADER_KEYS:
            # never forward incoming sensitive headers
            continue
        headers[k] = v
    return headers

async def _sleep(seconds: float):
    import asyncio
    await asyncio.sleep(seconds)

async def _forward_request(
    method: str,
    path: str,
    request: Request,
    *,
    allow_stream: bool = False
) -> Response:
    """
    General forwarder with logging, retries, and optional SSE stream passthrough.
    """
    client: httpx.AsyncClient = app.state.client
    url = _upstream_url(path, request.url.query)
    incoming_headers = dict(request.headers)
    headers = _build_forward_headers(incoming_headers)
    req_id = incoming_headers.get("X-Request-ID") or str(uuid.uuid4())

    # Read body (for GET/DELETE this is typically empty)
    body: bytes = await request.body()

    # Parse body and make changes
    payload = _safe_json_loads(body)

    # Normalize chat/completions for gpt-5
    if payload and path == "/v1/chat/completions":
        model = str(payload.get("model", "")).lower()

        # 1) Allow both 'gpt-5' and its variants
        if model.startswith("gpt-5"):
            # 2) Translate max_tokens / max_output_tokens -> max_completion_tokens
            if "max_completion_tokens" not in payload:
                if "max_output_tokens" in payload:
                    payload["max_completion_tokens"] = payload.pop("max_output_tokens")
                elif "max_tokens" in payload:
                    payload["max_completion_tokens"] = payload.pop("max_tokens")
                else:
                    # 3) Provide a sensible default if needed (optional)
                    payload["max_completion_tokens"] = 128000

            payload["temperature"] = 1
             # 4) Ensure stream Accept is correct (optional, helps with picky upstreams)
            if payload.get("stream") is True:
                headers["Accept"] = "text/event-stream"

            # 5) Write back the body
            body = json.dumps(payload).encode("utf-8")


    # Request logging
    req_log = {
        "id": req_id,
        "method": method,
        "path": str(request.url.path),
        "upstream": url,
        "headers": _redact_headers(incoming_headers),
    }
    if LOG_BODIES:
        parsed = _safe_json_loads(body)
        req_log["body"] = parsed if parsed is not None else (body.decode("utf-8", errors="ignore") if body else "")
    logger.info(f"REQUEST {json.dumps(req_log)}")

    # Stream detection for chat-completions
    wants_stream = False
    if allow_stream:
        payload = _safe_json_loads(body)
        wants_stream = bool(payload and payload.get("stream") is True)

    start = time.time()
    last_exc = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            from typing import AsyncIterator  # you already have this at the top of the file

            if wants_stream:
                # Open the stream, but NOT with 'async with'
                req = client.build_request(method, url, headers=headers, content=body)
                resp = await client.send(req, stream=True)

                duration_ms = int((time.time() - start) * 1000)
                resp_hdrs = _redact_headers(dict(resp.headers))
                logger.info(json.dumps({
                    "id": req_id,
                    "status": resp.status_code,
                    "duration_ms": duration_ms,
                    "headers": resp_hdrs,
                    "streaming": True
                }))

                passthrough_headers = {
                    k: v for k, v in resp.headers.items()
                    if k.lower() not in {"content-length", "transfer-encoding", "connection"}
                }
                passthrough_headers.setdefault("Content-Type", resp.headers.get("content-type", "text/event-stream; charset=utf-8"))
                passthrough_headers["X-Request-ID"] = req_id

                async def iter_bytes() -> AsyncIterator[bytes]:
                    logged = 0
                    try:
                        async for chunk in resp.aiter_bytes():
                            if LOG_BODIES and LOG_STREAM_MAX_BYTES > 0 and logged < LOG_STREAM_MAX_BYTES:
                                take = min(len(chunk), LOG_STREAM_MAX_BYTES - logged)
                                snippet = chunk[:take]
                                try:
                                    logger.info(
                                        f"STREAM-CHUNK id={req_id} bytes={len(chunk)} preview={snippet.decode('utf-8','ignore')}"
                                    )
                                except Exception:
                                    logger.info(f"STREAM-CHUNK id={req_id} bytes={len(chunk)}")
                                logged += take
                            yield chunk
                    finally:
                        # Close the upstream only after streaming
                        await resp.aclose()

                return StreamingResponse(iter_bytes(), status_code=resp.status_code, headers=passthrough_headers)


            # Non-stream path
            resp = await client.request(method, url, headers=headers, content=(None if method in {"GET", "DELETE"} else body))

            # Response logging + body
            content_type = resp.headers.get("content-type", "")
            resp_hdrs = _redact_headers(dict(resp.headers))
            if "application/json" in content_type:
                try:
                    resp_json = resp.json()
                except Exception:
                    resp_json = {"_raw": resp.text}
                if LOG_BODIES:
                    logger.info(json.dumps({
                        "id": req_id,
                        "status": resp.status_code,
                        "duration_ms": int((time.time() - start) * 1000),
                        "headers": resp_hdrs,
                        "body": resp_json
                    }))
                else:
                    logger.info(json.dumps({
                        "id": req_id,
                        "status": resp.status_code,
                        "duration_ms": int((time.time() - start) * 1000),
                        "headers": resp_hdrs
                    }))
                # Return as JSON
                return JSONResponse(status_code=resp.status_code, content=resp_json, headers={
                    "X-Upstream-Status": str(resp.status_code),
                    "X-Request-ID": req_id
                })
            else:
                # Non-JSON response: log length instead of the entire body (may be binary data)
                if LOG_BODIES:
                    logger.info(json.dumps({
                        "id": req_id,
                        "status": resp.status_code,
                        "duration_ms": int((time.time() - start) * 1000),
                        "headers": resp_hdrs,
                        "body_length": len(resp.content),
                        "content_type": content_type
                    }))
                else:
                    logger.info(json.dumps({
                        "id": req_id,
                        "status": resp.status_code,
                        "duration_ms": int((time.time() - start) * 1000),
                        "headers": resp_hdrs,
                        "content_type": content_type
                    }))
                return Response(status_code=resp.status_code, content=resp.content, media_type=content_type, headers={
                    "X-Upstream-Status": str(resp.status_code),
                    "X-Request-ID": req_id
                })

        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                backoff = RETRY_BACKOFF_SEC * (2 ** attempt)
                logger.warning(json.dumps({
                    "id": req_id,
                    "retry": attempt + 1,
                    "backoff_sec": backoff,
                    "error": f"{type(exc).__name__}: {str(exc)}"
                }))
                await _sleep(backoff)
                continue
            break
        except httpx.RequestError as exc:
            last_exc = exc
            break

    # Exhausted / non-retriable error
    err_payload = {
        "error": {
            "type": "proxy_error",
            "message": f"{type(last_exc).__name__}: {str(last_exc)}" if last_exc else "Unknown upstream error",
            "request_id": req_id,
            "upstream": url,
        }
    }
    logger.error(json.dumps(err_payload))
    return JSONResponse(status_code=502, content=err_payload, headers={"X-Request-ID": req_id})

# =========================
# Routes
# =========================

@app.get("/")
async def root():
    return {"name": "GenAI Proxy", "version": "1.0.0", "upstream": GENAI_BASE_URL}

# Health (root to /genai/)
@app.get("/health")
async def health_root():
    client: httpx.AsyncClient = app.state.client
    url = f"{GENAI_BASE_URL}/"
    headers = _build_forward_headers({})
    req_id = str(uuid.uuid4())
    try:
        resp = await client.get(url, headers=headers)
        logger.info(json.dumps({
            "id": req_id,
            "method": "GET",
            "path": "/health",
            "upstream": url,
            "status": resp.status_code
        }))
        return PlainTextResponse(resp.text, status_code=resp.status_code, headers={"X-Request-ID": req_id})
    except httpx.RequestError as e:
        err = {"error": {"type": "proxy_error", "message": str(e), "request_id": req_id, "upstream": url}}
        logger.error(json.dumps(err))
        return JSONResponse(status_code=502, content=err, headers={"X-Request-ID": req_id})

# Health v1
@app.get("/v1/health")
async def health_v1(request: Request):
    return await _forward_request("GET", "/v1/health", request)

@app.get("/v1/models")
async def list_models(request: Request):
    # Local, OpenAI-compatible response (without upstream call)
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    now = int(time.time())

    models = [
        {"id": "gpt-4.1",          "object": "model", "created": now, "owned_by": "genai"},
        {"id": "gpt-4.1-mini",     "object": "model", "created": now, "owned_by": "genai"},
        {"id": "gpt-4.1-nano",     "object": "model", "created": now, "owned_by": "genai"},
        {"id": "llama33_70b",      "object": "model", "created": now, "owned_by": "genai"},
        {"id": "llama32_90b_vision","object": "model","created": now, "owned_by": "genai"},
        {"id": "gpt-5",            "object": "model", "created": now, "owned_by": "genai"},
        {"id": "gpt-5-mini",       "object": "model", "created": now, "owned_by": "genai"},
    ]

    resp = {"object": "list", "data": models}

    # Logging in the same style as the proxy
    logger.info(json.dumps({
        "id": req_id,
        "method": "GET",
        "path": "/v1/models",
        "local": True,
        "headers": _redact_headers(dict(request.headers)),
        **({"body": resp} if LOG_BODIES else {})
    }))

    return JSONResponse(status_code=200, content=resp, headers={"X-Request-ID": req_id})


# OpenAI-compatible endpoints
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    return await _forward_request("POST", "/v1/chat/completions", request, allow_stream=True)


