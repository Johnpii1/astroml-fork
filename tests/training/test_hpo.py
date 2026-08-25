from astroml.training.hyperparameter_optimization import HPOptimizer
from astroml.tracking.experiment_tracker import ExperimentTracker

def test_hpo() -> None:
    HPOptimizer().optimize()
    ExperimentTracker().track()
