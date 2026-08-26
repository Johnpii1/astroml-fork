"""Incremental and continuous learning modules."""

from .online_learner import (
    OnlineLearnerConfig,
    OnlineSGDClassifier,
    OnlineSGDRegressor,
    OnlinePassiveAggressiveClassifier,
    OnlinePassiveAggressiveRegressor,
)
from .adaptive_model import (
    AdaptiveModelConfig,
    AdaptiveModel,
    ExperienceReplayBuffer,
    EWCRegularizer,
)
from .stream_trainer import (
    StreamTrainerConfig,
    StreamTrainer,
    StreamDataIngestor,
)

__all__ = [
    "OnlineLearnerConfig",
    "OnlineSGDClassifier",
    "OnlineSGDRegressor",
    "OnlinePassiveAggressiveClassifier",
    "OnlinePassiveAggressiveRegressor",
    "AdaptiveModelConfig",
    "AdaptiveModel",
    "ExperienceReplayBuffer",
    "EWCRegularizer",
    "StreamTrainerConfig",
    "StreamTrainer",
    "StreamDataIngestor",
]
