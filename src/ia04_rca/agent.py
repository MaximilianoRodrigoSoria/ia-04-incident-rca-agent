"""IA-04 · Agente de causa raíz (tool-calling determinista, evidencia obligatoria).

Política del agente (auditable, sin "magia"):
1. get_logs(trace_id): trae los logs correlacionados.
2. Identifica el error más *upstream* (el servicio que otros esperan) usando el grafo.
3. blast_radius(rootCandidate): calcula el radio de impacto.
4. Emite hipótesis rankeadas por confianza; TODA hipótesis cita evidencia. Si no
   hay evidencia (ningún log ERROR), no emite hipótesis (no inventa).

El LLM (por puerto) solo redacta el enunciado de la causa; con StubLLM es determinista.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ia_core.llm import LLMPort, StubLLM
from .tools import DependencyGraph, LogEntry, LogStore


@dataclass
class Hypothesis:
    root_cause: str
    confidence: float
    blast_radius: list[str]
    evidence: list[dict] = field(default_factory=list)


class RcaAgent:
    def __init__(self, graph: DependencyGraph, logs: LogStore, llm: LLMPort | None = None) -> None:
        self.graph = graph
        self.logs = logs
        self.llm = llm or StubLLM()
        self.tool_calls = 0

    def _rank_upstream(self, services: set[str]) -> list[str]:
        """Ordena servicios: más upstream primero (menos dependencias propias)."""
        return sorted(services, key=lambda s: (len(self.graph.upstreams(s)), s))

    def diagnose(self, trace_id: str) -> list[Hypothesis]:
        self.tool_calls = 0
        entries: list[LogEntry] = self.logs.get_logs(trace_id)
        self.tool_calls += 1  # get_logs
        errors = [e for e in entries if e.level == "ERROR"]
        if not errors:
            return []  # sin evidencia, no se inventa causa

        services_with_error = {e.service for e in errors}
        candidates = self._rank_upstream(services_with_error)

        hypotheses: list[Hypothesis] = []
        n = len(entries)
        for cand in candidates:
            radius = self.graph.blast_radius(cand)
            self.tool_calls += 1  # blast_radius
            ev = [
                {"type": "log", "service": e.service, "line": e.line, "message": e.message}
                for e in entries if e.service == cand or cand in self.graph.upstreams(e.service)
            ]
            # Confianza: proporción de logs explicados por este candidato como raíz.
            explained = len([e for e in entries if e.service == cand
                             or cand in self.graph.upstreams(e.service)])
            confidence = round(min(0.95, 0.4 + 0.6 * explained / max(1, n)), 2)
            # Enunciado grounded en la evidencia: el/los mensaje(s) de error del
            # propio candidato. El LLM (por puerto) puede reformularlo en prod.
            own_errors = [e.message for e in errors if e.service == cand]
            statement = own_errors[0] if own_errors else "posible causa aguas arriba"
            hypotheses.append(Hypothesis(
                root_cause=f"{cand}: {statement}",
                confidence=confidence,
                blast_radius=radius,
                evidence=ev,
            ))
        hypotheses.sort(key=lambda h: -h.confidence)
        return hypotheses
