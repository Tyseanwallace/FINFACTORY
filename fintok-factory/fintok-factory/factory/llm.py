"""Small wrapper around the Claude API that returns parsed JSON."""
import json, os, re

import anthropic

_client = None


def client():
    global _client
    if _client is None:
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise SystemExit("Missing ANTHROPIC_API_KEY. Copy .env.example to .env and add your key.")
        _client = anthropic.Anthropic()
    return _client


def _extract_json(text: str):
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    start = min([i for i in (text.find("{"), text.find("[")) if i != -1], default=-1)
    if start == -1:
        raise ValueError("No JSON found in model reply:\n" + text[:500])
    return json.JSONDecoder().raw_decode(text[start:])[0]


def ask_json(cfg, system: str, prompt: str, web_search: bool = False, max_tokens: int = 8000):
    """Ask Claude for JSON. With web_search=True Claude can look things up first."""
    tools = []
    if web_search:
        tools = [{"type": "web_search_20250305", "name": "web_search",
                  "max_uses": cfg["ai"].get("max_searches", 6)}]
    messages = [{"role": "user", "content": prompt}]
    for _ in range(6):  # long searches can pause; keep going until Claude finishes
        resp = client().messages.create(model=cfg["ai"]["model"], max_tokens=max_tokens,
                                        system=system, messages=messages, tools=tools or anthropic.NOT_GIVEN)
        if resp.stop_reason == "pause_turn":
            messages = [messages[0], {"role": "assistant", "content": resp.content}]
            continue
        break
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    sources = []
    for b in resp.content:
        if getattr(b, "type", "") == "web_search_tool_result" and isinstance(b.content, list):
            sources += [{"title": r.title, "url": r.url} for r in b.content if hasattr(r, "url")]
    try:
        data = _extract_json(text)
    except Exception:
        # one retry asking only for the JSON
        messages = [messages[0], {"role": "assistant", "content": text or "(no text)"},
                    {"role": "user", "content": "Reply again with ONLY the JSON, nothing else."}]
        resp = client().messages.create(model=cfg["ai"]["model"], max_tokens=max_tokens, system=system, messages=messages)
        data = _extract_json("".join(b.text for b in resp.content if getattr(b, "type", "") == "text"))
    return data, sources
