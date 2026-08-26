"""Tracking utilities (metrics, usage, experiment tracking, data lineage, etc)."""

# ---------------------------------------------------------------------------
# Imports & Package Exports
# ---------------------------------------------------------------------------
from __future__ import annotations

from importlib import import_module

from .ab_testing import ABTestingFramework
from .llm_usage_tracker import (
    LLMPrices,
    LLMUsage,
    LLMUsageTracker,
    default_llm_usage_tracker,
)
from .mlflow_tracker import MLflowTracker
from .model_registry import ModelRegistry

__all__ = [
    "ABTestingFramework",
    "MLflowTracker",
    "ModelRegistry",
    "LLMUsage",
    "LLMPrices",
    "LLMUsageTracker",
    "default_llm_usage_tracker",
    "DataLineageTracker",
    "ProvenanceTracker",
    "LineageVisualizer",
    "MetadataStore",
    "Budget",
    "BudgetManager",
    "BudgetPeriod",
    "CostRecord",
    "CostTracker",
    "ResourceOptimizer",
    "ResourceType",
    "ResourceUsageSample",
    "default_cost_tracker",
]

_LAZY: dict[str, tuple[str, str]] = {
    "DataLineageTracker": ("astroml.tracking.lineage.data_lineage", "DataLineageTracker"),
    "ProvenanceTracker": ("astroml.tracking.lineage.provenance", "ProvenanceTracker"),
    "LineageVisualizer": ("astroml.tracking.lineage.visualizer", "LineageVisualizer"),
    "MetadataStore": ("astroml.tracking.lineage.metadata_store", "MetadataStore"),
    "Budget": ("astroml.tracking.budget_manager", "Budget"),
    "BudgetManager": ("astroml.tracking.budget_manager", "BudgetManager"),
    "BudgetPeriod": ("astroml.tracking.budget_manager", "BudgetPeriod"),
    "CostRecord": ("astroml.tracking.cost_tracker", "CostRecord"),
    "CostTracker": ("astroml.tracking.cost_tracker", "CostTracker"),
    "ResourceType": ("astroml.tracking.cost_tracker", "ResourceType"),
    "default_cost_tracker": ("astroml.tracking.cost_tracker", "default_cost_tracker"),
    "ResourceOptimizer": ("astroml.tracking.resource_optimizer", "ResourceOptimizer"),
    "ResourceUsageSample": ("astroml.tracking.resource_optimizer", "ResourceUsageSample"),
}


def __getattr__(name: str):
    if name in _LAZY:
        module_path, attr = _LAZY[name]
        module = import_module(module_path)
        value = getattr(module, attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
