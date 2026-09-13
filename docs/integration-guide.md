# Freebie Integration & Usage Guide 🔌

This guide covers step-by-step instructions on how to integrate **Freebie** with popular programming languages, AI agent frameworks, and third-party AI client applications.

---

## 📑 Table of Contents

1. [Connection Details & Base URLs](#1-connection-details--base-urls)
2. [Python Ecosystem](#2-python-ecosystem)
   - [Official OpenAI Python SDK](#official-openai-python-sdk)
   - [Async & Streaming](#async--streaming)
   - [LangChain & LangGraph](#langchain--langgraph)
   - [LlamaIndex](#llamaindex)
   - [LiteLLM](#litellm)
3. [JavaScript & TypeScript Ecosystem](#3-javascript--typescript-ecosystem)
   - [Official OpenAI Node SDK](#official-openai-node-sdk)
   - [Next.js / Browser Fetch (Streaming)](#nextjs--browser-fetch-streaming)
   - [LangChain.js](#langchainjs)
4. [Popular AI Desktop & Web Clients](#4-popular-ai-desktop--web-clients)
   - [Cherry Studio](#cherry-studio)
   - [ChatBox](#chatbox)
   - [OpenWebUI](#openwebui)
   - [NextChat (ChatGPT-Next-Web)](#nextchat-chatgpt-next-web)
   - [LibreChat](#librechat)
5. [Raw HTTP / REST & cURL](#5-raw-http--rest--curl)
   - [cURL](#curl)
   - [PowerShell (Invoke-RestMethod)](#powershell-invoke-restmethod)
6. [Tool Calling (Function Calling)](#6-tool-calling-function-calling)
7. [Production Deployment & Security](#7-production-deployment--security)

---

## 1. Connection Details & Base URLs

Freebie implements the standard OpenAI specification:

| Parameter | Value |
| :--- | :--- |
| **Default Host** | `http://127.0.0.1:8080` (or `http://localhost:8080`) |
| **OpenAI Base URL** | `http://127.0.0.1:8080/v1` |
| **Chat Completions URL** | `http://127.0.0.1:8080/v1/chat/completions` |
| **Models List URL** | `http://127.0.0.1:8080/v1/models` |
| **Health Check URL** | `http://127.0.0.1:8080/health` |
| **API Key** | Any string (e.g. `none` or `sk-freebie`) if no keys are set in `config.json` |

---

## 2. Python Ecosystem

### Official OpenAI Python SDK

Install the SDK:
```bash
pip install openai
```

#### Basic Completion:
```python
from openai import OpenAI

# Initialize client pointing to Freebie
client = OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="none"  # Any string works if Freebie has no api_keys configured
)

response = client.chat.completions.create(
    model="gemini-3.6-flash",  # or "auto", "gemini-3.5-flash-thinking"
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function to check if a number is prime."}
    ]
)

print(response.choices[0].message.content)
```

### Async & Streaming

Stream responses live token-by-token using `AsyncOpenAI`:

```python
import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI(
        base_url="http://127.0.0.1:8080/v1",
        api_key="none"
    )

    stream = await client.chat.completions.create(
        model="gemini-3.6-flash",
        messages=[{"role": "user", "content": "Explain relativity in simple terms."}],
        stream=True
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
    print()

asyncio.run(main())
```

---

### LangChain & LangGraph

Install dependencies:
```bash
pip install langchain-openai
```

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatOpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="none",
    model="gemini-3.6-flash",
    streaming=True
)

messages = [
    SystemMessage(content="You are an expert travel planner."),
    HumanMessage(content="Give me a 3-day itinerary for Kyoto.")
]

for chunk in llm.stream(messages):
    print(chunk.content, end="", flush=True)
print()
```

---

### LlamaIndex

Install dependencies:
```bash
pip install llama-index-llms-openai
```

```python
from llama_index.llms.openai import OpenAI

llm = OpenAI(
    api_base="http://127.0.0.1:8080/v1",
    api_key="none",
    model="gemini-3.6-flash"
)

response = llm.complete("What are the advantages of vector databases?")
print(response.text)
```

---

### LiteLLM

```python
import litellm

response = litellm.completion(
    model="openai/gemini-3.6-flash",
    api_base="http://127.0.0.1:8080/v1",
    api_key="none",
    messages=[{"role": "user", "content": "Hello LiteLLM!"}]
)

print(response.choices[0].message.content)
```

---

## 3. JavaScript & TypeScript Ecosystem

### Official OpenAI Node SDK

Install package:
```bash
npm install openai
```

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://127.0.0.1:8080/v1",
  apiKey: "none",
});

async function main() {
  const stream = await client.chat.completions.create({
    model: "gemini-3.6-flash",
    messages: [{ role: "user", content: "Write a haiku about TypeScript." }],
    stream: true,
  });

  for await (const chunk of stream) {
    const text = chunk.choices[0]?.delta?.content || "";
    process.stdout.write(text);
  }
  console.log();
}

main();
```

---

### Next.js / Browser Fetch (Streaming)

```javascript
async function askFreebie(prompt) {
  const response = await fetch("http://127.0.0.1:8080/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer none",
    },
    body: JSON.stringify({
      model: "auto",
      stream: true,
      messages: [{ role: "user", content: prompt }],
    }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split("\n");

    for (const line of lines) {
      if (line.startsWith("data: ") && !line.includes("[DONE]")) {
        const json = JSON.parse(line.substring(6));
        const token = json.choices[0]?.delta?.content || "";
        process.stdout.write(token);
      }
    }
  }
}
```

---

## 4. Popular AI Desktop & Web Clients

Freebie works out of the box with popular ChatGPT / LLM graphical clients:

### Cherry Studio
1. Open **Settings** ➔ **Model Providers**.
2. Select **OpenAI** (or Add Custom Provider).
3. Set **API Base URL**: `http://127.0.0.1:8080/v1`
4. Set **API Key**: `none`
5. Click **Check Connectivity** / Add Models:
   - `gemini-3.6-flash`
   - `gemini-3.5-flash-thinking`
   - `gpt-4o`
   - `o3-mini`

### ChatBox
1. Open **Settings** ➔ **Model Provider**.
2. Select **OpenAI API**.
3. **API Host**: `http://127.0.0.1:8080`
4. **API Key**: `none`
5. **Model**: Select or type `auto` or `gemini-3.6-flash`.

### OpenWebUI (Docker)
When starting OpenWebUI with Docker, connect to Freebie on your host:
```bash
docker run -d -p 3000:8080 \
  -e OPENAI_API_BASE_URL="http://host.docker.internal:8080/v1" \
  -e OPENAI_API_KEY="none" \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

### NextChat (ChatGPT-Next-Web)
1. Go to **Settings**.
2. Enable **Custom Endpoint**.
3. **Endpoint**: `http://127.0.0.1:8080`
4. **API Key**: `none`
5. **Model**: `gemini-3.6-flash`

---

## 5. Raw HTTP / REST & cURL

### cURL

```bash
curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {"role": "user", "content": "What are 3 healthy breakfast ideas?"}
    ]
  }'
```

### PowerShell (Windows)

```powershell
$body = @{
    model = "gemini-3.6-flash"
    messages = @(
        @{ role = "user"; content = "Summarize the history of computing in 3 bullets" }
    )
} | ConvertTo-Json

$res = Invoke-RestMethod -Uri "http://127.0.0.1:8080/v1/chat/completions" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$res.choices[0].message.content
```

---

## 6. Tool Calling (Function Calling)

Freebie seamlessly handles standard OpenAI tool calling:

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="none")

tools = [
    {
        "type": "function",
        "function": {
            "name": "lookup_stock_price",
            "description": "Fetch the current real-time stock ticker price",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "e.g. AAPL, GOOGL, NVDA"}
                },
                "required": ["ticker"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gemini-3.6-flash",
    messages=[{"role": "user", "content": "What is the stock price for Nvidia (NVDA)?"}],
    tools=tools
)

choice = response.choices[0]
if choice.finish_reason == "tool_calls":
    for tool_call in choice.message.tool_calls:
        print(f"Call function: {tool_call.function.name}")
        print(f"Arguments:     {tool_call.function.arguments}")
```

---

## 7. Production Deployment & Security

### 1. Protecting with API Keys
To protect your Freebie server from unauthorized access, create or edit `config.json`:

```json
{
  "host": "0.0.0.0",
  "port": 8080,
  "api_keys": [
    "sk-my-super-secret-key-12345"
  ]
}
```

Or set the environment variable:
```bash
export FREEBIE_API_KEYS="sk-my-super-secret-key-12345"
```

Now all incoming requests must supply:
`Authorization: Bearer sk-my-super-secret-key-12345`

### 2. Running as a Background Daemon (Linux Systemd)

Create `/etc/systemd/system/freebie.service`:

```ini
[Unit]
Description=Freebie API Proxy Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Freebie
ExecStart=/usr/local/bin/freebie --port 8080 --host 0.0.0.0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now freebie
```

### 3. Nginx Reverse Proxy with SSL (HTTPS)

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable buffering for SSE real-time streaming
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding on;
    }
}
```
