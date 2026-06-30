from .ab_testing import ABTestingFramework
# ---------------------------------------------------------------------------
# A/B Testing Framework
# ---------------------------------------------------------------------------

class Experiment(Base):
    """A/B test experiment for comparing models or prompts."""
    __tablename__ = "experiments"
    # ... keep full definition

class Variant(Base):
    """A variant in an A/B test experiment."""
    __tablename__ = "variants"
    # ... keep full definition

class ExperimentResult(Base):
    """Individual result from an A/B test experiment."""
    __tablename__ = "experiment_results"
    # ... keep full definition


# ---------------------------------------------------------------------------
# Golden Dataset Framework
# ---------------------------------------------------------------------------

class GoldenDataset(Base):
    """Golden dataset for model evaluation and benchmarking."""
    __tablename__ = "golden_datasets"
    # ... keep full definition

class GoldenDatasetEntry(Base):
    """Individual entry in a golden dataset with ground truth labels."""
    __tablename__ = "golden_dataset_entries"
    # ... keep full definition


# ---------------------------------------------------------------------------
# Ledger Processing
# ---------------------------------------------------------------------------

class ProcessedLedger(Base):
    """Tracking table for processed ledgers during backfill to ensure idempotency."""
    __tablename__ = "processed_ledgers"
    # ... keep full definition

