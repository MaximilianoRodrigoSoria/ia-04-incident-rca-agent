"""Puerto LLM + adaptadores.

`LLMPort.complete(prompt)` devuelve texto. Dos adaptadores:

- `StubLLM`: determinista y offline. No "razona"; aplica transformaciones
  reproducibles suficientes para que el pipeline corra sin API (p. ej. genera un
  documento hipotético para HyDE reformulando la consulta, o emite un veredicto
  de juez basado en solape de tokens). Ideal para tests y CI.
- `OpenAICompatLLM`: cliente /v1/chat/completions (consume IA-07 o una API).

La clave de diseño: TODO consumidor depende del puerto, nunca del proveedor.
"""
from __future__ import annotations

import json
import re
import urllib.request
from typing import Protocol

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


class LLMPort(Protocol):
    def complete(self, prompt: str, **kwargs) -> str: ...


class StubLLM:
    """LLM determinista para correr offline. Reconoce 'tareas' por marcadores."""

    #: marcador que HyDE antepone al pedir un documento hipotético
    HYDE_MARKER = "### HYDE_DOC"

    def complete(self, prompt: str, **kwargs) -> str:
        if self.HYDE_MARKER in prompt:
            return self._hypothetical_doc(prompt)
        # Respuesta genérica: eco expandido de la consulta (útil como baseline).
        return prompt.strip().splitlines()[-1]

    def _hypothetical_doc(self, prompt: str) -> str:
        query = prompt.split(self.HYDE_MARKER, 1)[1].strip()
        toks = _TOKEN_RE.findall(query.lower())
        # Documento hipotético: reformula la pregunta como afirmación técnica y
        # repite términos clave para acercar el embedding a los pasajes reales.
        keys = " ".join(dict.fromkeys(toks))
        return (
            f"El servicio implementa {keys}. "
            f"La solución para '{query}' se resuelve mediante {keys}, "
            f"aplicando el patrón correspondiente en la capa de aplicación e "
            f"infraestructura. Detalle técnico sobre {keys}."
        )


class OpenAICompatLLM:
    """Adaptador /v1/chat/completions (OpenAI-compatible)."""

    def __init__(self, base_url: str, model: str = "local-llm",
                 api_key: str | None = None, temperature: float = 0.0,
                 timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.timeout = timeout

    def complete(self, prompt: str, **kwargs) -> str:  # pragma: no cover - I/O
        payload = json.dumps({
            "model": self.model,
            "temperature": kwargs.get("temperature", self.temperature),
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions", data=payload, headers=headers
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
