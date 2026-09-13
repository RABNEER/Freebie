import pytest
from freebie.protocol import messages_to_prompt, parse_tool_calls, build_conversation_payload, parse_chatgpt_sse_line
from freebie.models import resolve_model, MODELS

def test_resolve_model():
    # Authenticated user asking for gpt-4o
    name, slug, provider, _, _ = resolve_model("gpt-4o", has_openai_auth=True)
    assert name == "gpt-4o"
    assert slug == "gpt-4o"
    assert provider == "openai"

    # Alias
    name, slug, provider, _, _ = resolve_model("gpt-3.5-turbo", has_openai_auth=True)
    assert name == "gpt-4o-mini"
    assert slug == "gpt-4o-mini"
    assert provider == "openai"

    # Explicit Gemini request (zero auth)
    name, slug, provider, gemini_id, think = resolve_model("gemini-3.6-flash")
    assert name == "gemini-3.6-flash"
    assert provider == "gemini"
    assert gemini_id == 1
    assert think == 4

    # Anonymous user asking for auto -> routes to Gemini Flash!
    name, slug, provider, gemini_id, think = resolve_model("auto", has_openai_auth=False)
    assert name == "gemini-3.6-flash"
    assert provider == "gemini"

    # Authenticated user asking for auto -> routes to GPT-4o!
    name, slug, provider, _, _ = resolve_model("auto", has_openai_auth=True)
    assert name == "gpt-4o"
    assert provider == "openai"

def test_messages_to_prompt():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
    prompt = messages_to_prompt(messages)
    assert "[System]: You are a helpful assistant." in prompt
    assert "[User]: Hello!" in prompt

def test_parse_tool_calls():
    raw = (
        "Here is the result.\n"
        "```tool_call\n"
        '{"name": "get_weather", "arguments": {"city": "Paris"}}\n'
        "```\n"
        "Hope this helps!"
    )
    clean, calls = parse_tool_calls(raw)
    assert "Here is the result." in clean
    assert "Hope this helps!" in clean
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "get_weather"
    assert "Paris" in calls[0]["function"]["arguments"]

def test_parse_chatgpt_sse_line():
    line = 'data: {"message": {"id": "1", "author": {"role": "assistant"}, "content": {"content_type": "text", "parts": ["Hi there!"]}}}'
    ev, text, reasoning = parse_chatgpt_sse_line(line)
    assert ev == "content"
    assert text == "Hi there!"
    assert reasoning is None

    done_line = "data: [DONE]"
    ev, _, _ = parse_chatgpt_sse_line(done_line)
    assert ev == "done"
