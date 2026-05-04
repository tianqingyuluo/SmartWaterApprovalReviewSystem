"""Static SmartWater knowledge pack support."""

from .loader import KnowledgePackError, load_knowledge_pack, normalize_knowledge_fragments

__all__ = ["KnowledgePackError", "load_knowledge_pack", "normalize_knowledge_fragments"]
