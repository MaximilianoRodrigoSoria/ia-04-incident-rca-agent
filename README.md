<p align="center">
<a href="https://www.linkedin.com/in/soriamaximilianorodrigo/" target="_blank" rel="noopener noreferrer">
<img width="100%" height="100%" src="docs/img/banner.gif" alt="ia-04-incident-rca-agent"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square" alt="Python-3.11+">
  <img src="https://img.shields.io/badge/agent-tool_calling-14B8A6?style=flat-square" alt="agent-tool_calling">
  <img src="https://img.shields.io/badge/RCA-blast_radius-22D3EE?style=flat-square" alt="RCA-blast_radius">
  <img src="https://img.shields.io/badge/tests-pytest-1DE9B6?style=flat-square" alt="tests-pytest">
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=1DE9B6&center=true&vCenter=true&width=820&lines=RCA+sobre+el+grafo+de+dependencias;tool-calling+determinista+%C2%B7+evidencia+obligatoria;nunca+afirma+sin+citar" alt="typing SVG">
</p>

<hr/>

<h1 align="center">ia-04-incident-rca-agent</h1>

<p align="center">
Agente de <b>causa raíz</b>: ante un stacktrace correlaciona logs, traza el blast radius sobre el grafo de dependencias y propone la causa — citando evidencia.
</p>

## ¿Qué resuelve este proyecto?

En un ecosistema de 9 servicios integrados, una falla rara vez es local: un timeout en `payment-service` puede originarse en `identity-service`. El agente recibe una señal (traceId/stacktrace) y produce un **informe de causa raíz**: servicios involucrados, blast radius calculado sobre el grafo real, cadena causal más probable y acciones — **todo citando la evidencia** (líneas de log, aristas del grafo) para que sea auditable.

## ¿Qué pasos sigue?

El agente sólo puede llamar herramientas acotadas (get_logs, blast_radius); identifica el error más *aguas arriba* y emite hipótesis rankeadas por confianza. Sin evidencia, no inventa causa.

```mermaid
flowchart TB
    SIG[traceId / stacktrace] --> AG[RCA Agent]
    AG -->|get_logs| LOGS[(Logs por traceId)]
    AG -->|blast_radius| G[(Grafo de dependencias)]
    AG --> REP[Hipótesis rankeadas + evidencia + confianza]
```

## Componentes principales

- **`RcaAgent`** — loop de tool-calling determinista con presupuesto de evidencia.
- **`DependencyGraph`** — `blast_radius` = quién se ve afectado si un servicio cae.
- **`LogStore`** — logs correlacionados por `traceId`.
- **`Hypothesis`** — causa + confianza + blast radius + evidencia citada.

## ¿Por qué así?

El tool-calling acotado (el LLM elige herramientas, no ejecuta libre) lo hace **determinista y auditable** en vez de mágico. La regla dura —toda hipótesis cita evidencia, sin evidencia no se emite— evita alucinaciones de causa raíz.

## Uso

```bash
pip install -e ".[dev]"
pytest -q
```

> Parte del portafolio de **Maximiliano Rodrigo Soria** — capa de IA sobre el ecosistema
> de 9 backends. Corre **offline** (embedder por hashing + LLM stub deterministas);
> en producción se cambian los adaptadores por los reales (IA-07 local / API OpenAI-compatible)
> por los mismos puertos. Diseño y contrato completos en [`TASK.md`](./TASK.md).
