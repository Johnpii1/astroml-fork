"""Machine learning models for AstroML."""

from .gcn import GCN
from .link_prediction import GCNEncoder, LinkPredictor
from .sage_encoder import InductiveSAGEEncoder
from .temporal import (
    TemporalAttention,
    TemporalEdgeConv,
    TemporalEncoding,
    TemporalGAT,
    TemporalGCN,
    TemporalGraphSAGE,
    TemporalGraphTransformer,
    TemporalModelFactory,
)

try:
    from .deep_svdd import DeepSVDD, DeepSVDDNetwork
    from .deep_svdd_trainer import DeepSVDDTrainer, FraudDetectionDeepSVDD
except ImportError:
    pass

__all__ = [
    'GCN',
    'TemporalGCN',
    'TemporalGraphSAGE',
    'TemporalGAT',
    'TemporalGraphTransformer',
    'TemporalEdgeConv',
    'TemporalEncoding',
    'TemporalAttention',
    'TemporalModelFactory',
    'DeepSVDD',
    'DeepSVDDNetwork',
    'DeepSVDDTrainer',
    'FraudDetectionDeepSVDD',
    'InductiveSAGEEncoder',
    'GCNEncoder',
    'LinkPredictor',
]
