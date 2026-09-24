# Tutorial: Build a Snapshot and Train a Baseline GCN

## 1. Backfill a Ledger Range
```python
from astroml.ingestion import run_backfill
run_backfill(start_ledger=1000, end_ledger=2000)
```

## 2. Build a Snapshot
```python
from astroml.pipeline import build_snapshot
build_snapshot(ledger_range=(1000, 2000))
```

## 3. Train the Baseline GCN
```python
from astroml.training import train_gcn
train_gcn(snapshot_path="data/snapshot.pt", epochs=50)
```

## FAQ
- **Q**: What if OOM occurs?
  **A**: Try reducing batch size or ledger range.
