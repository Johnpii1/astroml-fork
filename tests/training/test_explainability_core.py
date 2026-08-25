from astroml.training.explainability import Explainability
from astroml.preprocessing.feature_importance import FeatureImportance

def test_explain() -> None:
    assert Explainability().explain() == "explanation"
    assert FeatureImportance().compute() == []
