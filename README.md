# genai proxy

A openai compatible proxy to add an authentication header with api_key for a corperated openai endpoint.

## Build container image

```bash
$ podman build -t genai-proxy:latest -f Containerfile .
```

## Run proxy

```bash
$ export GENAI_SUBCRIPTION_NAME=some-subscription-name
$ export GENAI_API_KEY=some-api-key
$ export GENAI_BASE_URL=https://gateway.apiportal.genai.nl/genai

$ podman run --replace \
             -d \
             -p 8111:8111 \
             -e GENAI_SUBCRIPTION_NAME="${GENAI_SUBCRIPTION_NAME}" \
             -e GENAI_API_KEY="${GENAI_API_KEY}" \
             -e GENAI_BASE_URL="${GENAI_BASE_URL}" \
             -e REQUEST_TIMEOUT="60" \
             -e MAX_RETRIES="2" \
             -e RETRY_BACKOFF_SEC="0.5" \
             -e LOG_BODIES="true" \
             -e LOG_STREAM_MAX_BYTES="0" \
             -e ALLOWED_ORIGINS="http://localhost:8111" \
             --name genai-proxy \
             genai-proxy:latest

$ podman logs -f genai-proxy
2025-10-03 07:20:12,683 INFO SUBCRIPTION_NAME=*******************
2025-10-03 07:20:12,683 INFO SUBSCRIPTION_KEY=711b*******************
2025-10-03 07:20:12,683 INFO GENAI_BASE_URL=https://gateway.apiportal.genai.nl/genai
2025-10-03 07:20:12,683 INFO REQUEST_TIMEOUT=60.0
2025-10-03 07:20:12,683 INFO MAX_RETRIES=2
2025-10-03 07:20:12,683 INFO RETRY_BACKOFF_SEC=0.5
2025-10-03 07:20:12,683 INFO LOG_BODIES=True
2025-10-03 07:20:12,683 INFO ALLOWED_ORIGINS=['http://localhost:8111']
2025-10-03 07:20:12,683 INFO LOG_STREAM_MAX_BYTES=0
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8111 (Press CTRL+C to quit)
```

## List models

```bash
$ curl -X GET http://localhost:8111/v1/models | jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   570  100   570    0     0   309k      0 --:--:-- --:--:-- --:--:--  556k
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4.1",
      "object": "model",
      "created": 1759432253,
      "owned_by": "genai"
    },
    {
      "id": "gpt-4.1-mini",
      "object": "model",
      "created": 1759432253,
      "owned_by": "genai"
    },
    {
      "id": "gpt-4.1-nano",
      "object": "model",
      "created": 1759432253,
      "owned_by": "genai"
    },
    {
      "id": "llama33_70b",
      "object": "model",
      "created": 1759432253,
      "owned_by": "genai"
    },
    {
      "id": "llama32_90b_vision",
      "object": "model",
      "created": 1759432253,
      "owned_by": "genai"
    },
    {
      "id": "GPT-5",
      "object": "model",
      "created": 1759432253,
      "owned_by": "genai"
    },
    {
      "id": "GPT-5-mini",
      "object": "model",
      "created": 1759432253,
      "owned_by": "genai"
    }
  ]
}
```

## Test chat completion using gtp-4.1

```bash
$ curl -X POST http://localhost:8111/v1/chat/completions   -H "Content-Type: application/json"   -H "X-Request-ID: test-001"   -d '{
    "model": "gpt-4.1",
    "messages": [
      {"role": "system", "content": "Je bent een behulpzame assistent."},
      {"role": "user", "content": "Geef me één zin over openai."}
    ],
    "temperature": 0.2,
    "max_tokens": 64
  }' | jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  1609  100  1368  100   241   1932    340 --:--:-- --:--:-- --:--:--  2275
{
  "id": "chatcmpl-CMJ8PmvTwtTGTC8mcvURjHA67tytf",
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "logprobs": null,
      "message": {
        "content": "OpenAI is een onderzoeksorganisatie die zich richt op het ontwikkelen en bevorderen van kunstmatige intelligentie op een veilige en verantwoorde manier.",
        "refusal": null,
        "role": "assistant",
        "annotations": [],
        "audio": null,
        "function_call": null,
        "tool_calls": null
      },
      "content_filter_results": {
        "hate": {
          "filtered": false,
          "severity": "safe"
        },
        "protected_material_text": {
          "filtered": false,
          "detected": false
        },
        "self_harm": {
          "filtered": false,
          "severity": "safe"
        },
        "sexual": {
          "filtered": false,
          "severity": "safe"
        },
        "violence": {
          "filtered": false,
          "severity": "safe"
        }
      }
    }
  ],
  "created": 1759432805,
  "model": "gpt-4.1-2025-04-14",
  "object": "chat.completion",
  "service_tier": null,
  "system_fingerprint": "fp_9ab7d013ff",
  "usage": {
    "completion_tokens": 31,
    "prompt_tokens": 28,
    "total_tokens": 59,
    "completion_tokens_details": {
      "accepted_prediction_tokens": 0,
      "audio_tokens": 0,
      "reasoning_tokens": 0,
      "rejected_prediction_tokens": 0
    },
    "prompt_tokens_details": {
      "audio_tokens": 0,
      "cached_tokens": 0
    }
  },
  "prompt_filter_results": [
    {
      "prompt_index": 0,
      "content_filter_results": {
        "hate": {
          "filtered": false,
          "severity": "safe"
        },
        "jailbreak": {
          "filtered": false,
          "detected": false
        },
        "self_harm": {
          "filtered": false,
          "severity": "safe"
        },
        "sexual": {
          "filtered": false,
          "severity": "safe"
        },
        "violence": {
          "filtered": false,
          "severity": "safe"
        }
      }
    }
  ]
}
```

## test chat completion using gpt-5

```bash
$ curl -X POST http://localhost:8111/v1/chat/completions   -H "Content-Type: application/json"   -H "X-Request-ID: test-001"   -d '{
    "model": "gpt-5",
    "messages": [
      {"role": "system", "content": "you are a python develper."},
      {"role": "user", "content": "write a simple script in python to test the chat completion openai-compatible endpoint http://localhost:8111/v1/chat/completions (model gpt-5, no api_key needed)."}
    ],
    "max_completion_tokens": 4000
  }' | jq -r '.choices[0].message.content' 
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  4482  100  4129  100   353    322     27  0:00:13  0:00:12  0:00:01  1154
#!/usr/bin/env python3
import argparse
import json
import sys
import requests


def chat(prompt, url="http://localhost:8111/v1/chat/completions", model="gpt-5", stream=False):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if stream:
        payload["stream"] = True

    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60, stream=stream)
    except requests.RequestException as e:
        print(f"Request error: {e}", file=sys.stderr)
        sys.exit(1)

    if not stream:
        if resp.status_code != 200:
            print(f"HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)
        try:
            data = resp.json()
        except json.JSONDecodeError:
            print("Failed to parse JSON response", file=sys.stderr)
            sys.exit(1)
        content = data.get("choices", [{}])[0].get("message", {}).get("content")
        if content is None:
            content = data.get("choices", [{}])[0].get("text")
        print(content if content is not None else data)
        return

    # Streaming mode
    if resp.status_code != 200:
        print(f"HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data: "):
            payload = line[len("data: "):].strip()
            if payload == "[DONE]":
                break
            try:
                event = json.loads(payload)
            except Exception:
                continue
            choice = event.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            chunk = delta.get("content")
            if chunk is None:
                msg = choice.get("message", {})
                chunk = msg.get("content")
            if chunk:
                print(chunk, end="", flush=True)
    print()


def main():
    ap = argparse.ArgumentParser(description="Test OpenAI-compatible chat completions endpoint")
    ap.add_argument("prompt", nargs="*", help="User prompt to send")
    ap.add_argument("--url", default="http://localhost:8111/v1/chat/completions", help="Endpoint URL")
    ap.add_argument("--model", default="gpt-5", help="Model name")
    ap.add_argument("--stream", action="store_true", help="Use streaming responses")
    args = ap.parse_args()

    prompt = " ".join(args.prompt) if args.prompt else "Say hello in one short sentence."
    chat(prompt, url=args.url, model=args.model, stream=args.stream)


if __name__ == "__main__":
    main()
```

## Use genai models in VSCode Copilot

note: openai-compatible provider for copilot is available in VSCode(-insiders) 1.105.0 and above. 

Edit VSCode(-insiders) settings to add the genai models: **Github > Copilot > Chat**

![alt text](images/image01.png)

```json
{
  "github.copilot.chat.customOAIModels": {

    "gpt_4": {
        "name": "genai gpt-4",
        "url": "http://localhost:8111/v1",
        "toolCalling": true,
        "vision": false,
        "thinking": true,
        "maxInputTokens": 128000,
        "maxOutputTokens": 4096,
        "requiresAPIKey": false
        },
    "gpt-4.1": {
      "name": "genai gpt-4.1",
      "url": "http://localhost:8111/v1",
      "toolCalling": true,
      "vision": false,
      "thinking": true,
      "maxInputTokens": 128000,
        "maxOutputTokens": 4096,
      "requiresAPIKey": false
        },
    "gpt-4.1-mini": {
      "name": "genai gpt-4.1-mini",
      "url": "http://localhost:8111/v1",
      "toolCalling": true,
      "vision": false,
      "maxInputTokens": 128000,
        "maxOutputTokens": 4096,
      "requiresAPIKey": false
        },
    "gpt-4.1-nano": {
      "name": "genai gpt-4.1-nano",
      "url": "http://localhost:8111/v1",
      "toolCalling": true,
      "vision": false,
      "maxInputTokens": 4096,
      "maxOutputTokens": 1024,
      "requiresAPIKey": false
        },
    "llama33_70b": {
        "name": "genai llama3.3-70b",
        "url": "http://localhost:8111/v1",
        "toolCalling": true,
        "vision": false,
        "maxInputTokens": 128000,
        "maxOutputTokens": 4096,
        "requiresAPIKey": false
        },
    "llama32_90b_vision": {
        "name": "genai llama3.2-90b-vision",
        "url": "http://localhost:8111/v1",
        "toolCalling": true,
        "vision": true,
        "maxInputTokens": 4096,
        "maxOutputTokens": 1024,
        "requiresAPIKey": false
        },
    "GPT-5": {
        "name": "genai GPT-5",
        "url": "http://localhost:8111/v1",
        "toolCalling": true,
        "vision": false,
        "maxInputTokens": 128000,
        "maxOutputTokens": 4096,
        "requiresAPIKey": false
        },
    "GPT-5-mini": {
        "name": "genai GPT-5-mini",
        "url": "http://localhost:8111/v1",
        "toolCalling": true,
        "vision": false,
        "maxInputTokens": 128000,
        "maxOutputTokens": 4096,
        "requiresAPIKey": false
        }
    }
}
```

The genai models are available in copilot **model** the drop down menu:

![alt text](images/image02.png)