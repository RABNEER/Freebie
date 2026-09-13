"""Protocol conversion between OpenAI API and ChatGPT Web internal format."""
import json
import re
import uuid
from typing import Any, Dict, Generator, List, Optional, Tuple


def messages_to_prompt(messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> str:
    """Convert OpenAI chat messages and tools list into a single prompt string."""
    parts = []

    if tools:
        tool_defs = []
        for tool in tools:
            fn = tool.get("function", tool) if tool.get("type") == "function" else tool
            tool_defs.append({
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
                "parameters": fn.get("parameters", {}),
            })
        if tool_defs:
            parts.append(
                "# Tool Use Instructions\n"
                "You can call external tools. Call format:\n"
                "```tool_call\n"
                '{"name": "func_name", "arguments": {...}}\n'
                "```\n"
                f"Available tools:\n{json.dumps(tool_defs, indent=2)}\n"
            )

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
                elif isinstance(part, str):
                    text_parts.append(part)
            content = " ".join(text_parts)

        if role == "system":
            parts.append(f"[System]: {content}")
        elif role == "assistant":
            parts.append(f"[Assistant]: {content}")
        elif role == "tool":
            parts.append(f"[Tool result for {msg.get('name', '')}]: {content}")
        else:
            parts.append(f"[User]: {content}" if len(messages) > 1 else str(content))

    return "\n\n".join(parts)


def parse_tool_calls(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Extract tool_call markdown blocks from model output.

    Returns (clean_text, tool_calls).
    """
    tool_calls = []
    pattern = r"```tool_call\s*\n(.*?)\n```"
    clean_parts = []
    last_end = 0

    for m in re.finditer(pattern, text, re.DOTALL):
        clean_parts.append(text[last_end:m.start()])
        last_end = m.end()
        try:
            data = json.loads(m.group(1).strip())
            tool_calls.append({
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "type": "function",
                "function": {
                    "name": data.get("name", ""),
                    "arguments": json.dumps(data.get("arguments", {}), ensure_ascii=False),
                },
            })
        except Exception:
            pass

    clean_parts.append(text[last_end:])
    clean = "".join(clean_parts).strip()
    return clean, tool_calls


def build_conversation_payload(
    prompt: str,
    model_slug: str = "auto",
    parent_message_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    history_disabled: bool = True,
) -> Dict[str, Any]:
    """Construct payload for POST https://chatgpt.com/backend-api/conversation."""
    msg_id = str(uuid.uuid4())
    parent_id = parent_message_id or str(uuid.uuid4())

    payload: Dict[str, Any] = {
        "action": "next",
        "messages": [
            {
                "id": msg_id,
                "author": {"role": "user"},
                "content": {
                    "content_type": "text",
                    "parts": [prompt],
                },
                "metadata": {},
            }
        ],
        "parent_message_id": parent_id,
        "model": model_slug,
        "timezone_offset_min": -330,
        "suggestions": [],
        "history_and_training_disabled": history_disabled,
        "conversation_mode": {"kind": "primary_assistant"},
        "force_paragen": False,
    }

    if conversation_id:
        payload["conversation_id"] = conversation_id

    return payload


def parse_chatgpt_sse_line(line: str) -> Optional[Tuple[str, str, Optional[str]]]:
    """Parse single SSE line from ChatGPT.

    Returns:
      (event_type, text_content, reasoning_content)
      where event_type in ("content", "reasoning", "done", "error")
    """
    line = line.strip()
    if not line.startswith("data:"):
        return None

    data_str = line[5:].strip()
    if data_str == "[DONE]":
        return ("done", "", None)

    try:
        data = json.loads(data_str)
    except Exception:
        return None

    if "error" in data and data["error"]:
        err_msg = str(data["error"])
        return ("error", err_msg, None)

    message = data.get("message")
    if not message or not isinstance(message, dict):
        return None

    author_role = message.get("author", {}).get("role")
    if author_role != "assistant":
        return None

    content_obj = message.get("content", {})
    content_type = content_obj.get("content_type", "")
    parts = content_obj.get("parts", [])

    raw_text = parts[0] if parts and isinstance(parts[0], str) else ""

    if content_type == "thought":
        return ("reasoning", "", raw_text)

    return ("content", raw_text, None)
