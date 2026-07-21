"""IA-04 · Herramientas del agente RCA: grafo de dependencias y logs.

El agente solo puede llamar a estas herramientas acotadas (no ejecuta libremente):
- DependencyGraph.blast_radius(service): qué servicios se ven afectados si `service` cae.
- LogStore.get_logs(trace_id): logs correlacionados por traceId (ya presentes vía MdcFilter).
"""
from __future__ import annotations

from dataclasses import dataclass, field


class DependencyGraph:
    """`depends_on[s]` = servicios *upstream* que `s` invoca."""

    def __init__(self, depends_on: dict[str, list[str]]) -> None:
        self.depends_on = {k: list(v) for k, v in depends_on.items()}

    def upstreams(self, service: str) -> list[str]:
        return list(self.depends_on.get(service, []))

    def blast_radius(self, service: str) -> list[str]:
        """Servicios que dependen (transitivamente) de `service` -> impactados si cae."""
        dependents: set[str] = set()
        changed = True
        frontier = {service}
        while changed:
            changed = False
            for svc, ups in self.depends_on.items():
                if svc in dependents:
                    continue
                if frontier & set(ups):
                    dependents.add(svc)
                    frontier.add(svc)
                    changed = True
        return sorted(dependents)


@dataclass
class LogEntry:
    service: str
    level: str  # INFO | WARN | ERROR
    message: str
    line: int


@dataclass
class LogStore:
    _by_trace: dict[str, list[LogEntry]] = field(default_factory=dict)

    def add(self, trace_id: str, entries: list[LogEntry]) -> None:
        self._by_trace.setdefault(trace_id, []).extend(entries)

    def get_logs(self, trace_id: str) -> list[LogEntry]:
        return list(self._by_trace.get(trace_id, []))


# Grafo real del ecosistema (derivado del PLAN.md §5).
DEFAULT_GRAPH = DependencyGraph({
    "identity-service": [],
    "async-job-engine": ["identity-service"],
    "url-shortener": ["identity-service"],
    "realtime-gateway": ["identity-service"],
    "collab-chat": ["identity-service", "realtime-gateway"],
    "file-storage-service": ["identity-service", "async-job-engine"],
    "file-processing-service": ["identity-service", "file-storage-service"],
    "payment-service": ["identity-service", "async-job-engine", "file-storage-service"],
    "api-gateway": ["identity-service", "file-storage-service", "payment-service", "url-shortener"],
})


def sample_logstore() -> LogStore:
    """Escenario de ejemplo: pool de JWT agotado en identity-service se propaga."""
    store = LogStore()
    store.add("trace-jwt-pool", [
        LogEntry("identity-service", "ERROR", "JWT signing key pool exhausted: cannot issue token", 42),
        LogEntry("payment-service", "ERROR", "401 from identity-service validating token; charge aborted", 88),
        LogEntry("api-gateway", "WARN", "downstream payment-service timeout after 3s", 61),
    ])
    return store
