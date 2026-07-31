"""LLM-based recommendation system for issue #474.

Provides intelligent suggestions for platform features, actions, and insights
based on user activity and context.

Components:
- Engine: Recommendation orchestrator
- Profiler: User profiling
- Ranker: Result ranking
- Generators: Suggestion generators
"""

from __future__ import annotations

from .engine import RecommendationEngine
from .profiler import UserProfile, UserProfiler
from .ranker import RecommendationRanker
from .generators import (
    RecommendationGenerator,
    FeatureRecommendationGenerator,
    ModelRecommendationGenerator,
    QuerySuggestionGenerator,
    InsightGenerator,
)

__all__ = [
    "RecommendationEngine",
    "UserProfile",
    "UserProfiler",
    "RecommendationRanker",
    "RecommendationGenerator",
    "FeatureRecommendationGenerator",
    "ModelRecommendationGenerator",
    "QuerySuggestionGenerator",
    "InsightGenerator",
]
