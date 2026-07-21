"""Núcleo compartido vendorizado (subset usado por este proyecto)."""
from .llm import LLMPort, StubLLM, OpenAICompatLLM
__all__ = ['LLMPort', 'StubLLM', 'OpenAICompatLLM']
