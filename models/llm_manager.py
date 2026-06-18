"""LLM Manager — Ollama + OpenAI + Anthropic + Groq + Cohere

Model defaults (verified June 2026):
  Groq   : llama-3.3-70b-versatile  (llama-3.1-70b-versatile decommissioned)
  Cohere : command-a-03-2025         (command-r-plus removed Sept 2025)
  Ollama : llama3.2                  (local; run `ollama serve` first)
"""

import requests
from typing import Optional, List
from config.settings import Settings


class LLMManager:
    def __init__(self, settings: Settings):
        self.settings  = settings
        self.providers = {
            "ollama":    self._ollama,
            "openai":    self._openai,
            "anthropic": self._anthropic,
            "groq":      self._groq,
            "cohere":    self._cohere,
        }

    # ── Ollama ─────────────────────────────────────────────
    def _ollama(self, prompt: str, model: Optional[str] = None, **kw) -> Optional[str]:
        _model: str = model or str(self.settings.default_models.get("ollama", "llama3.2"))
        url = str(self.settings.api_keys.get("ollama", "http://localhost:11434"))
        try:
            r = requests.post(
                f"{url}/api/generate",
                json={"model": _model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            return r.json().get("response") if r.ok else None
        except requests.exceptions.ConnectionError:
            print(
                "  \u26a0 Ollama: Server not running.\n"
                "    ▶ Start it with:  ollama serve\n"
                "    ▶ Then pull a model: ollama pull llama3.2"
            )
            return None
        except Exception as e:
            print(f"  \u26a0 Ollama: {e}")
            return None

    def list_ollama_models(self) -> List[str]:
        try:
            url = str(self.settings.api_keys.get("ollama", "http://localhost:11434"))
            r   = requests.get(f"{url}/api/tags", timeout=5)
            if r.ok:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return []

    # ── OpenAI ────────────────────────────────────────────
    def _openai(self, prompt: str, model: Optional[str] = None, **kw) -> Optional[str]:
        try:
            import openai
            key = self.settings.get_api_key("openai")
            if not key:
                return None
            _model: str = model or str(self.settings.default_models.get("openai", "gpt-4o-mini"))
            client = openai.OpenAI(api_key=key)
            resp   = client.chat.completions.create(
                model=_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"  \u26a0 OpenAI: {e}")
            return None

    # ── Anthropic ───────────────────────────────────────────
    def _anthropic(self, prompt: str, model: Optional[str] = None, **kw) -> Optional[str]:
        try:
            import anthropic
            key = self.settings.get_api_key("anthropic")
            if not key:
                return None
            _model: str = model or str(self.settings.default_models.get("anthropic", "claude-3-5-haiku-20241022"))
            client = anthropic.Anthropic(api_key=key)
            resp   = client.messages.create(
                model=_model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            # Only TextBlock has .text; filter out ThinkingBlock / ToolUseBlock etc.
            text_blocks = [
                block.text
                for block in resp.content
                if hasattr(block, "text") and isinstance(block.text, str)
            ]
            return "\n".join(text_blocks) if text_blocks else None
        except Exception as e:
            print(f"  \u26a0 Anthropic: {e}")
            return None

    # ── Groq ───────────────────────────────────────────────
    def _groq(self, prompt: str, model: Optional[str] = None, **kw) -> Optional[str]:
        """Groq — default: llama-3.3-70b-versatile (updated June 2026)"""
        try:
            from groq import Groq
            key = self.settings.get_api_key("groq")
            if not key:
                return None
            _model: str = model or str(self.settings.default_models.get("groq", "llama-3.3-70b-versatile"))
            client = Groq(api_key=key)
            resp   = client.chat.completions.create(
                model=_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"  \u26a0 Groq: {e}")
            return None

    # ── Cohere ──────────────────────────────────────────────
    def _cohere(self, prompt: str, model: Optional[str] = None, **kw) -> Optional[str]:
        """Cohere — uses v2 ClientV2 + command-a-03-2025 (updated June 2026)"""
        try:
            import cohere
            key = self.settings.get_api_key("cohere")
            if not key:
                return None
            _model: str = model or str(self.settings.default_models.get("cohere", "command-a-03-2025"))
            client = cohere.ClientV2(key)
            resp   = client.chat(
                model=_model,
                messages=[{"role": "user", "content": prompt}],
            )
            # resp.message.content is a list; guard against non-text items
            content = resp.message.content
            if content and hasattr(content[0], "text"):
                return str(content[0].text)
            return None
        except Exception as e:
            print(f"  \u26a0 Cohere: {e}")
            return None

    # ── Auto-select & generate ──────────────────────────────
    def generate(self, prompt: str, provider: Optional[str] = None, **kw) -> Optional[str]:
        if provider and provider in self.providers:
            result = self.providers[provider](prompt, **kw)
            if result:
                return result
            print(f"  ⚠ {provider} failed, trying fallback providers...")

        if self.settings.use_local_first:
            result = self._ollama(prompt, **kw)
            if result:
                return result

        for p in ["groq", "openai", "anthropic", "cohere"]:
            if self.settings.has_api_key(p):
                result = self.providers[p](prompt, **kw)
                if result:
                    return result

        print("  (No AI response — check your provider config)")
        return None

    def set_api_key(self, provider: str, key: str):
        self.settings.set_api_key(provider, key)
