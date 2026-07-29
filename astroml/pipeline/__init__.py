"""Inference pipelines for AstroML."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "InductiveGraphSAGE",
    "InductiveAnomalyScorer",
    "SchemaContract",
    "QualityContract",
    "SemanticContract",
    "ContractVerifier",
]

_LAZY: dict[str, tuple[str, str]] = {
    "InductiveGraphSAGE": ("astroml.pipeline.inductive", "InductiveGraphSAGE"),
    "InductiveAnomalyScorer": ("astroml.pipeline.scoring", "InductiveAnomalyScorer"),
    "SchemaContract": ("astroml.pipeline.contracts.schema_contract", "SchemaContract"),
    "QualityContract": ("astroml.pipeline.contracts.quality_contract", "QualityContract"),
    "SemanticContract": ("astroml.pipeline.contracts.semantic_contract", "SemanticContract"),
    "ContractVerifier": ("astroml.pipeline.contracts.verifier", "ContractVerifier"),
}


def __getattr__(name: str):
    if name in _LAZY:
        module_path, attr = _LAZY[name]
        module = import_module(module_path)
        value = getattr(module, attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
