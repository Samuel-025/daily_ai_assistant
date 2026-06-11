"""LLM Manager — Ollama + OpenAI + Anthropic + Groq + Cohere"""

import requests
from typing import Optional, List
from config.settings import Settings


class LLMManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.providers = {
            "ollama":    self._ollama,
            "openai":    self._openai,
            "anthropic": self._anthropic,
            "groq":      self._groq,
            "cohere":    self._cohere,
        }

    # ── Ollama ────────────────────────────────────────
    def _ollama(self, prompt: str, model: str = None, **kw) -> Optional[str]:
        model = model or self.settings.default_models["ollama"]
        url   = self.settings.api_keys["ollama"]
        try:
            r = requests.post(f"{url}/api/generate",
                              json={"model": model, "prompt": prompt, "stream": False},
                              timeout=60)
            return r.json().get("response") if r.ok else None
        except Exception as e:
            print(f"  ⚠ Ollama: {e}")
            return None

    def list_ollama_models(self) -> List[str]:
        try:
            url = self.settings.api_keys["ollama"]
            r = requests.get(f"{url}/api/tags", timeout=5)
            if r.ok:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return []

    # ── OpenAI ────────────────────────────────────────
    def _openai(self, prompt: str, model: str = None, **kw) -> Optional[str]:
        try:
            import openai
            key = self.settings.get_api_key("openai")
            if not key:
                return None
            client = openai.OpenAI(api_key=key)
            resp = client.chat.completions.create(
                model=model or self.settings.default_models["openai"],
                messages=[{"role": "user", "content": prompt}])
            return resp.choices[0].message.content
        except Exception as e:
            print(f"  ⚠ OpenAI: {e}")
            return None

    # ── Anthropic ─────────────────────────────────────
    def _anthropic(self, prompt: str, model: str = None, **kw) -> Optional[str]:
        try:
            import anthropic
            key = self.settings.get_api_key("anthropic")
            if not key:
                return None
            client = anthropic.Anthropic(api_key=key)
            resp = client.messages.create(
                model=model or self.settings.default_models["anthropic"],
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}])
            return resp.content[0].text
        except Exception as e:
            print(f"  ⚠ Anthropic: {e}")
            return None

    # ── Groq ──────────────────────────────────────────
    def _groq(self, prompt: str, model: str = None, **kw) -> Optional[str]:
        try:
            from groq import Groq
            key = self.settings.get_api_key("groq")
            if not key:
                return None
            client = Groq(api_key=key)
            resp = client.chat.completions.create(
                model=model or self.settings.default_models["groq"],
                messages=[{"role": "user", "content": prompt}])
            return resp.choices[0].message.content
        except Exception as e:
            print(f"  ⚠ Groq: {e}")
            return None

    # ── Cohere ────────────────────────────────────────
    def _cohere(self, prompt: str, model: str = None, **kw) -> Optional[str]:
        try:
            import cohere
            key = self.settings.get_api_key("cohere")
            if not key:
                return None
            client = cohere.Client(key)
            resp = client.chat(message=prompt,
                               model=model or self.settings.default_models["cohere"])
            return resp.text
        except Exception as e:
            print(f"  ⚠ Cohere: {e}")
            return None

    # ── Auto-select & generate ────────────────────────
    def generate(self, prompt: str, provider: str = None, **kw) -> Optional[str]:
        if provider and provider in self.providers:
            return self.providers[provider](prompt, **kw)

        if self.settings.use_local_first:
            result = self._ollama(prompt, **kw)
            if result:
                return result

        for p in ["groq", "openai", "anthropic", "cohere"]:
            if self.settings.has_api_key(p):
                result = self.providers[p](prompt, **kw)
                if result:
                    return result

        return None

    def set_api_key(self, provider: str, key: str):
        self.settings.set_api_key(provider, key)
