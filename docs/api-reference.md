# Freebie API Reference 📖

Complete technical reference for Freebie's OpenAI-compatible REST & SSE endpoints.

---

## Base Endpoints

- **Root URL**: `http://localhost:8080`
- **OpenAI API v1**: `http://localhost:8080/v1`

---

## Endpoints

### 1. `GET /health` & `GET /`
Returns service availability, active models, upstream authentication state, and default routing.

#### Request:
```bash
curl http://localhost:8080/health
```

#### Response (200 OK):
```json
{
  "status": "ok",
  "service": "Freebie",
  "version": "0.1.0",
  "models": [
    "auto",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.5",
    "o1",
    "o1-mini",
    "o3-mini",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-thinking",
    "gemini-flash-lite"
  ],
  "authenticated_upstream": false,
  "proxy_configured": false,
  "default_mode": "Gemini Flash (Zero-auth)"
}
```

---

### 2. `GET /v1/models`
Returns list of available models formatted according to the OpenAI models schema.

#### Request:
```bash
curl http://localhost:8080/v1/models
```

#### Response (200 OK):
```json
{
  "object": "list",
  "data": [
    {
      "id": "auto",
      "object": "model",
      "created": 1741857600,
      "owned_by": "auto",
      "permission": [],
      "root": "auto",
      "parent": null,
      "description": "Auto selector: GPT-4o when authenticated, Gemini Flash when anonymous"
    },
    {
      "id": "gemini-3.6-flash",
      "object": "model",
      "created": 1741857600,
      "owned_by": "gemini",
      "permission": [],
      "root": "gemini-3.6-flash",
      "parent": null,
      "description": "Gemini 3.6 Flash (zero-auth, ultra-fast responses)"
    }
  ]
}
```

---

### 3. `POST /v1/chat/completions`
Main completions endpoint supporting both standard JSON responses and Server-Sent Events (SSE) streaming.

#### Headers:
| Header | Type | Description |
| :--- | :--- | :--- |
| `Content-Type` | `application/json` | Required |
| `Authorization` | `Bearer <key>` | Optional (required only if `api_keys` configured in `config.json`) |
| `x-access-token` | `string` | Optional ChatGPT Bearer token override per request |

#### Request Body Parameters:
| Parameter | Type | Required | Default | Description |
| :--- | :---: | :---: | :---: | :--- |
| `model` | `string` | No | `"auto"` | Model slug or alias (e.g. `auto`, `gemini-3.6-flash`, `gpt-4o`) |
| `messages` | `array` | **Yes** | - | Array of OpenAI message objects (`role`, `content`) |
| `stream` | `boolean` | No | `false` | When true, returns chunked Server-Sent Events |
| `tools` | `array` | No | `null` | OpenAI function calling definitions |
| `temperature` | `float` | No | `null` | Sampling temperature |
| `max_tokens` | `integer` | No | `null` | Maximum tokens to generate |

#### Non-Streaming Response Example:
```json
{
  "id": "chatcmpl-9414867ba748",
  "object": "chat.completion",
  "created": 1741857600,
  "model": "gemini-3.6-flash",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I assist you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 15,
    "total_tokens": 25
  }
}
```

#### Streaming SSE Chunk Example:
```text
data: {"id": "chatcmpl-9414867ba748", "object": "chat.completion.chunk", "created": 1741857600, "model": "gemini-3.6-flash", "choices": [{"index": 0, "delta": {"content": "Hello"}, "finish_reason": null}]}

data: {"id": "chatcmpl-9414867ba748", "object": "chat.completion.chunk", "created": 1741857600, "model": "gemini-3.6-flash", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}

data: [DONE]
```

---

## Reasoning Process Streaming (`o1`, `o3-mini`, `gemini-3.5-flash-thinking`)

When reasoning models are invoked with `stream: true`, thinking tokens are streamed using the OpenAI-standard `reasoning_content` delta field:

```json
{
  "id": "chatcmpl-9414867ba748",
  "object": "chat.completion.chunk",
  "choices": [
    {
      "index": 0,
      "delta": {
        "reasoning_content": "Analyzing the probability distribution..."
      },
      "finish_reason": null
    }
  ]
}
```
Client applications supporting thinking (e.g. Cherry Studio, OpenWebUI) will automatically render thought collapsibles.
