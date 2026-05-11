#!/usr/bin/env python3
"""
Axeng — LLM Gateway
Unified client for all LLM providers with automatic fallback.
Supports: Anthropic, OpenAI, OpenCode, Ollama, LM Studio, Groq, Google AI, OpenRouter.
"""
import os, json, time, logging
from typing import Optional

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("llm_gateway")

# ── Provider Configurations ────────────────────────────────────────────────────
PROVIDERS = {
    "anthropic": {
        "name": "Anthropic Claude",
        "env_var": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1/messages",
        "models": ["claude-sonnet-4-7", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022",
                   "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        "default_model": "claude-sonnet-4-7",
        "supports_stream": True,
        "supports_json": True,
        "requires_header": True,
        "header_key": "x-api-key",
    },
    "openai": {
        "name": "OpenAI (GPT-4o, o1, o3)",
        "env_var": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1/chat/completions",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-mini", "o1-preview", "o3-mini", "o3"],
        "default_model": "gpt-4o",
        "supports_stream": True,
        "supports_json": True,
    },
    "opencode": {
        "name": "OpenCode Zen",
        "env_var": "OPENCODE_API_KEY",
        "base_url": "https://opencode.ai/zen/v1/chat/completions",
        "models": ["minimax-m2.5-free", "deepseek-v4-flash-free", "big-pickle", "ring-2.6-1t-free",
                   "gpt-5.4", "claude-sonnet-4-6", "qwen3.6-plus"],
        "default_model": "minimax-m2.5-free",
        "supports_stream": True,
        "supports_json": True,
    },
    "ollama": {
        "name": "Ollama (Local)",
        "env_var": "OLLAMA_HOST",
        "base_url": None,  # set dynamically
        "default_base": "http://localhost:11434/v1",
        "models": ["llama3.3", "llama3.2", "llama3.1", "qwen2.5", "mistral", "codellama",
                   "phi3", "gemma2", "deepseek-r1", "codestral", "wizardlm2"],
        "default_model": "llama3.3",
        "supports_stream": True,
        "supports_json": True,
        "is_local": True,
    },
    "lmstudio": {
        "name": "LM Studio (Local)",
        "env_var": "LMSTUDIO_HOST",
        "base_url": None,
        "default_base": "http://localhost:1234/v1",
        "models": [],  # discovered at runtime
        "default_model": "local-model",
        "supports_stream": True,
        "supports_json": True,
        "is_local": True,
    },
    "groq": {
        "name": "Groq (Fast, Free Tier)",
        "env_var": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant",
                   "mixtral-8x7b-32768", "gemma2-9b-it"],
        "default_model": "llama-3.3-70b-versatile",
        "supports_stream": True,
        "supports_json": True,
    },
    "google": {
        "name": "Google AI (Gemini)",
        "env_var": "GOOGLE_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
        "models": ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"],
        "default_model": "gemini-2.0-flash",
        "supports_stream": True,
        "supports_json": False,
    },
    "openrouter": {
        "name": "OpenRouter (Multi-Provider)",
        "env_var": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "models": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "google/gemini-2.0-flash",
                   "meta-llama/llama-3.3-70b-instruct", "deepseek/deepseek-chat-v3"],
        "default_model": "anthropic/claude-3.5-sonnet",
        "supports_stream": True,
        "supports_json": True,
    },
}


# ── Environment / Config Loading ───────────────────────────────────────────────
def _env(key: str, default=None):
    return os.environ.get(key, default)


def _cfg_val(key: str, default=None):
    """Read from axeng config.yaml via config module if available."""
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from config import get
        return get(key, default)
    except:
        return default


def _get_default_provider_order() -> list:
    """Read provider order from config, fall back to smart default."""
    cfg_order = _cfg_val("llm.provider_order", None)
    if cfg_order:
        return cfg_order
    # Smart default: cloud first (speed), then local (privacy/cost)
    return ["anthropic", "openai", "opencode", "groq", "openrouter", "google",
            "ollama", "lmstudio"]


# ── Provider Availability ──────────────────────────────────────────────────────
def get_available_providers() -> list:
    """Return list of (provider_id, provider_info) for configured keys."""
    available = []
    for pid, info in PROVIDERS.items():
        # Check env var
        key = _env(info["env_var"])
        if key and key != "***":
            available.append((pid, info))
            continue
        # Check config
        cfg_key = _cfg_val(f"llm.{pid}.api_key")
        if cfg_key:
            available.append((pid, info))
            continue
        # Local providers — check if running
        if pid in ("ollama", "lmstudio"):
            base = _env(f"{pid.upper()}_BASE_URL") or _env("OLLAMA_BASE_URL") or info.get("default_base")
            if base:
                try:
                    import urllib.request
                    req = urllib.request.Request(f"{base.rstrip('/v1')}/api/tags",
                                                headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=3) as r:
                        available.append((pid, info))
                        log.info(f"{info['name']} detected at {base}")
                except:
                    pass
    return available


def get_default_model(provider: str) -> str:
    info = PROVIDERS.get(provider, {})
    return _cfg_val(f"llm.{provider}.model") or _env(f"{provider.upper()}_MODEL") or info.get("default_model", "unknown")


def get_base_url(provider: str) -> str:
    """Get the base URL for a provider, handling local providers dynamically."""
    info = PROVIDERS.get(provider, {})
    # Check env override first
    env_url = _env(f"{provider.upper()}_BASE_URL") or _env("OLLAMA_BASE_URL") or _env("LMSTUDIO_BASE_URL")
    if env_url:
        return env_url.rstrip("/") + "/chat/completions"
    if info.get("base_url"):
        return info["base_url"]
    if info.get("default_base"):
        return info["default_base"].rstrip("/") + "/chat/completions"
    return ""


def get_api_key(provider: str) -> Optional[str]:
    info = PROVIDERS.get(provider, {})
    key = _env(info["env_var"]) or _cfg_val(f"llm.{provider}.api_key")
    return key if key and key != "***" else None


def get_headers(provider: str) -> dict:
    headers = {"Content-Type": "application/json"}
    info = PROVIDERS.get(provider, {})
    api_key = get_api_key(provider)
    if api_key:
        # Anthropic uses special header
        if info.get("requires_header") and info.get("header_key") == "x-api-key":
            headers[info["header_key"]] = api_key
        # Google Gemini uses key as query param
        elif provider == "google":
            pass  # handled in URL
        # OpenAI / OpenCode / OpenRouter use Bearer
        elif provider not in ("ollama", "lmstudio"):
            headers["Authorization"] = f"Bearer {api_key}"
    return headers


# ── Core LLM Call ─────────────────────────────────────────────────────────────
def call(
    prompt: str,
    provider: str = "anthropic",
    model: str = None,
    system: str = None,
    temperature: float = None,
    max_tokens: int = 4096,
    json_output: bool = False,
    timeout: int = 120,
    stream: bool = False,
) -> dict:
    """
    Make an LLM call via the specified provider.
    Returns {"ok": True, "text": "...", "model": "...", "usage": {...}}
    or {"ok": False, "error": "..."}
    """
    model = model or get_default_model(provider)
    base_url = get_base_url(provider)
    headers = get_headers(provider)

    if not base_url:
        return {"ok": False, "error": f"No base URL for provider: {provider}"}

    # Build body
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    # Temperature
    temp_cfg = _cfg_val(f"llm.{provider}.temperature")
    t = temperature if temperature is not None else (temp_cfg if temp_cfg is not None else 0.7)
    if provider not in ("openai", "opencode") or True:
        body["temperature"] = t

    # JSON mode
    if json_output:
        if provider in ("anthropic", "openai", "opencode", "groq", "openrouter", "ollama", "lmstudio"):
            body["response_format"] = {"type": "json_object"}
        elif provider == "google":
            body["generationConfig"] = {"responseMimeType": "application/json"}

    # Google: model name format
    if provider == "google":
        base_url = f"{base_url}/{model}:generateContent?key={get_api_key(provider)}"
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if json_output and "generationConfig" not in body:
            body["generationConfig"] = {"responseMimeType": "application/json"}
        headers.pop("Content-Type", None)
        headers["Content-Type"] = "application/json"

    # Build request URL
    url = base_url
    if provider == "google":
        pass  # already constructed
    elif provider in ("ollama", "lmstudio"):
        url = base_url  # already formatted with /chat/completions
    else:
        # Append API key for Google
        if provider == "google":
            pass

    log.info(f"Calling {provider}/{model} at {url}")

    try:
        import urllib.request
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())

        # Parse response
        if provider == "google":
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            choices = data.get("choices", [])
            if not choices:
                return {"ok": False, "error": f"No choices in response: {data}"}
            text = choices[0]["message"].get("content", "")

        usage = data.get("usage", {})
        return {
            "ok": True,
            "text": text,
            "model": model,
            "provider": provider,
            "usage": usage,
            "raw": data,
        }
    except Exception as e:
        log.error(f"{provider} error: {e}")
        return {"ok": False, "error": str(e), "provider": provider, "model": model}


# ── Streaming ─────────────────────────────────────────────────────────────────
def stream_call(
    prompt: str,
    provider: str = "anthropic",
    model: str = None,
    system: str = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    on_chunk=None,
) -> str:
    """Streaming call — returns full text, calls on_chunk for each token."""
    model = model or get_default_model(provider)
    base_url = get_base_url(provider)
    headers = get_headers(provider)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }

    if provider == "google":
        url = f"{base_url}/{model}:generateContent?key={get_api_key(provider)}"
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
    else:
        url = base_url

    try:
        import urllib.request, urllib.error
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp:
            full = []
            for line in resp:
                line = line.decode().strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                try:
                    chunk = json.loads(line)
                    if provider == "google":
                        parts = chunk.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        for p in parts:
                            txt = p.get("text", "")
                            if txt:
                                full.append(txt)
                                if on_chunk:
                                    on_chunk(txt)
                    else:
                        delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if delta:
                            full.append(delta)
                            if on_chunk:
                                on_chunk(delta)
                except:
                    pass
        return "".join(full)
    except Exception as e:
        return f"[stream error: {e}]"


# ── Fallback / Smart Call ─────────────────────────────────────────────────────
def call_with_fallback(
    prompt: str,
    providers: list = None,
    system: str = None,
    model: str = None,
    json_output: bool = False,
    temperature: float = None,
    max_tokens: int = 4096,
) -> dict:
    """
    Try providers in order until one succeeds.
    providers: list of provider IDs (default: all available).
    """
    if providers is None:
        providers = _get_default_provider_order()

    errors = []
    for p in providers:
        # Skip if not available
        if not get_api_key(p) and not (p in ("ollama", "lmstudio")):
            continue
        # Try to call
        log.info(f"Trying {p}...")
        result = call(
            prompt,
            provider=p,
            model=model,
            system=system,
            json_output=json_output,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if result.get("ok"):
            log.info(f"✅ {p} succeeded")
            return result
        err = result.get("error", "unknown")
        log.warning(f"❌ {p} failed: {err}")
        errors.append(f"{p}: {err}")

    return {
        "ok": False,
        "error": f"All providers failed: {'; '.join(errors)}",
        "providers_tried": providers,
    }


# ── Utility ───────────────────────────────────────────────────────────────────
def list_models(provider: str = None) -> dict:
    """List available models for a provider or all providers."""
    if provider:
        info = PROVIDERS.get(provider, {})
        return {"provider": provider, "models": info.get("models", []),
                "default": info.get("default_model", "")}
    return {pid: {"models": info.get("models", []), "default": info.get("default_model", ""),
                  "name": info.get("name", ""), "is_local": info.get("is_local", False)}
            for pid, info in PROVIDERS.items()}


def status() -> dict:
    """Return status of all providers."""
    available = get_available_providers()
    result = {}
    for pid, info in PROVIDERS.items():
        has_key = bool(get_api_key(pid))
        is_running = False
        if pid in ("ollama", "lmstudio"):
            base = _env(f"{pid.upper()}_BASE_URL") or info.get("default_base", "")
            if base:
                try:
                    import urllib.request
                    u = f"{base.rstrip('/v1')}/api/tags"
                    urllib.request.urlopen(u, timeout=3)
                    is_running = True
                except:
                    pass
        result[pid] = {
            "name": info["name"],
            "has_api_key": has_key,
            "is_running": is_running,
            "available": has_key or is_running,
        }
    return result


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Axeng LLM Gateway CLI")
    parser.add_argument("--prompt", "-p", help="Prompt to send")
    parser.add_argument("--provider", help="Provider (anthropic, openai, opencode, ollama, etc.)")
    parser.add_argument("--model", "-m", help="Model override")
    parser.add_argument("--system", "-s", help="System prompt")
    parser.add_argument("--json", action="store_true", help="Request JSON output")
    parser.add_argument("--list-providers", action="store_true", help="Show all providers")
    parser.add_argument("--status", action="store_true", help="Show provider status")
    args = parser.parse_args()

    if args.list_providers:
        print(json.dumps(list_models(), indent=2))
    elif args.status:
        print(json.dumps(status(), indent=2))
    elif args.prompt:
        result = call_with_fallback(
            args.prompt,
            providers=[args.provider] if args.provider else None,
            system=args.system,
            model=args.model,
            json_output=args.json,
        )
        if result.get("ok"):
            print(result["text"])
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()