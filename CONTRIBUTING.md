# Contributing to AstroML

Thank you for your interest in contributing to AstroML! This document provides the workflow and expectations for contributing code, documentation, and research to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style and Quality](#code-style-and-quality)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Questions & Support](#questions--support)

---

## Code of Conduct

AstroML is committed to providing a welcoming and inclusive environment. All contributors are expected to:

- Be respectful and constructive in all interactions
- Welcome feedback and criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

---

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/<your-username>/astroml.git
cd astroml
git remote add upstream https://github.com/Traqora/astroml.git
```

### 2. Create a Feature Branch

```bash
# Sync with latest upstream
git fetch upstream
git checkout -b feature/your-feature-name upstream/main

# Or for bug fixes:
git checkout -b fix/bug-description upstream/main
```

### 3. Set Up Development Environment

See [Development Setup](#development-setup) section below.

---

## Development Setup

### Prerequisites

- **Python 3.10+**
- **PostgreSQL 12+** (for ingestion tests; SQLite for unit tests)
- **Git**

### Installation

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) CPU-only PyTorch
pip install -r requirements-cpu.txt

# 4. Install development tools
pip install -e .[dev]

# 5. Configure database
# Create or edit config/database.yaml with your PostgreSQL credentials

# 6. Install pre-commit hooks
pre-commit install

# 7. Run tests to verify setup
pytest tests/ -v
```

### Database Setup (for integration tests)

```bash
# Create a test database
createdb astroml_test

# Update config/database.yaml to point to test database
# Then run migrations:
alembic upgrade head
```

---

## Code Style and Quality

### Python Style

AstroML follows **PEP 8** with these conventions:

- **Line length**: 100 characters (Black formatter)
- **Imports**: Organized by ruff import sorting (replaces isort)
- **Docstrings**: Use Google-style docstrings for all public functions/classes
- **Type hints**: Required for all new function signatures and return values
- **Formatter**: Black (auto-formats on save via pre-commit hooks)
- **Linter**: Ruff (replaces flake8, isort, pyupgrade, and more)
- **Enforcement**: All formatting is enforced via pre-commit hooks and CI checks

#### Example:

```python
from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

from astroml.db.session import Base


def calculate_node_importance(
    graph: 'nx.DiGraph',
    measure: str = 'betweenness',
) -> dict:
    """Calculate node importance metrics for a transaction graph.
    
    Args:
        graph: NetworkX directed graph of transactions
        measure: One of 'betweenness', 'degree', 'closeness'
        
    Returns:
        Dictionary mapping node IDs to importance scores
        
    Raises:
        ValueError: If measure is not recognized
    """
    if measure not in ('betweenness', 'degree', 'closeness'):
        raise ValueError(f"Unknown measure: {measure}")
    
    # Implementation
    return {}
```

### Type Hints

- Use type hints for all function parameters and return types
- Import from `typing` module for complex types
- Prefer concrete return types over `Any` when possible

```python
from typing import List, Dict, Optional, Tuple

def process_accounts(
    accounts: List[str],
    filters: Optional[Dict[str, int]] = None,
) -> Tuple[int, List[str]]:
    """Process a list of account IDs."""
    pass
```

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: Prefix with `_`

```python
class TransactionGraph:
    DEFAULT_WINDOW_SIZE = 30  # days
    
    def __init__(self):
        self._cache = {}
    
    def get_node_count(self) -> int:
        """Return number of nodes."""
        pass
```

### Comments & Documentation

- Write comments that explain **why**, not **what**
- Use docstrings for all public APIs
- Keep comments concise and up-to-date
- Update the relevant documentation for user-visible behavior changes

```python
# Good: explains reasoning
# Use cached result if available to avoid re-querying Stellar Horizon
if node_id in self._cache:
    return self._cache[node_id]

# Avoid: obvious from code
# increment counter
count += 1
```

---

## Testing Requirements

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_schema.py -v

# Run a targeted subset
pytest tests/ -k "feature or ingestion"

# Run with coverage
pytest tests/ --cov=astroml --cov-report=html

# Run async tests (marked with @pytest.mark.asyncio)
pytest tests/test_stream.py -v
```

### Writing Tests

**Test file naming**: `test_<module_name>.py`

```python
import pytest
from astroml.features import calculate_asset_diversity


class TestAssetDiversity:
    """Tests for asset diversity feature calculation."""
    
    def test_single_asset(self):
        """Single asset should have diversity = 1."""
        result = calculate_asset_diversity(['USD'])
        assert result == 1.0
    
    def test_empty_assets(self):
        """Empty list should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_asset_diversity([])
    
    @pytest.mark.asyncio
    async def test_async_feature_extraction(self):
        """Test async feature pipeline."""
        result = await extract_features_async([...])
        assert len(result) > 0


@pytest.fixture
def sample_graph():
    """Fixture providing sample transaction graph."""
    import networkx as nx
    G = nx.DiGraph()
    G.add_edges_from([('A', 'B'), ('B', 'C')])
    return G
```

### Test Checklist

Before submitting a PR:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] New tests added for new functionality
- [ ] Edge cases covered (empty inputs, None values, etc.)
- [ ] Async functions tested with `@pytest.mark.asyncio`
- [ ] Integration tests verify database interactions
- [ ] No hardcoded test data paths (use fixtures)
- [ ] Coverage remains at or above the project target of 80%

### Testing Different Stages

| Stage | Test Type | Command |
|-------|-----------|---------|
| Ingestion | Unit + Integration | `pytest tests/test_*stream*.py` |
| Graph Building | Unit + Snapshot | `pytest tests/test_snapshot.py` |
| Features | Unit + Functional | `pytest tests/test_*features*.py` |
| Models | Unit + Training | `pytest tests/test_*.py -k model` |

---

## Pull Request Process

### PR Checklist (Copy into your PR description)

```markdown
## PR Checklist

### Tests
- [ ] `pytest tests/ -v` passes locally with no failures
- [ ] New functionality has unit tests covering the happy path and edge cases
- [ ] Any new async functions are tested with `@pytest.mark.asyncio`
- [ ] No hardcoded test data paths — fixtures and `test_data/` only

### Lint & Style
- [ ] `black --check astroml/ tests/` reports no formatting violations
- [ ] `ruff check astroml/ tests/` reports no errors
- [ ] All public functions/classes have Google-style docstrings
- [ ] Type hints are present on all new function signatures

### Changelog & Docs
- [ ] `CHANGELOG.md` entry added under `## [Unreleased]`
- [ ] `README.md` updated if new features, CLI flags, or config keys were added
- [ ] Example scripts in `examples/` updated or added where appropriate
```

Every pull request **must** pass all of the following before requesting review.

### Required checks

- [ ] `pytest tests/ -v` passes locally
- [ ] `ruff check .` passes
- [ ] `black --check .` passes
- [ ] `mypy astroml/` passes
- [ ] The change is documented when it affects user-facing behavior or configuration

#### Tests
- [ ] `pytest tests/ -v` passes locally with no failures
- [ ] New functionality has unit tests covering the happy path and edge cases
- [ ] Any new async functions are tested with `@pytest.mark.asyncio`
- [ ] Integration tests pass against a real database (not mocked) where applicable
- [ ] No hardcoded test data paths — fixtures and `test_data/` only

#### Lint & Style
- [ ] `black --check astroml/ tests/` reports no formatting violations (line length 100)
- [ ] `ruff check astroml/ tests/` reports no errors
- [ ] `mypy astroml/` passes with no new type errors
- [ ] All public functions/classes have Google-style docstrings
- [ ] Type hints are present on all new function signatures

#### Changelog & Docs
- [ ] `CHANGELOG.md` entry added under `## [Unreleased]` describing the change
- [ ] `README.md` updated if new features, CLI flags, or config keys were added
- [ ] Any new config fields are documented in the relevant YAML file
- [ ] Example scripts in `examples/` updated or added where appropriate

#### Security & Safety
- [ ] No secrets, credentials, or API keys in the diff
- [ ] No hardcoded file paths pointing to local machine directories
- [ ] Database migrations include a safe `downgrade` function
- [ ] Random seeds are fixed for any reproducibility-sensitive tests

#### Reproducibility (pipeline changes only)
- [ ] Checksums/snapshots updated in `test_snapshots/` if graph output changed
- [ ] Hyperparameter changes are config-driven (not hardcoded)
- [ ] `CHANGELOG.md` notes any model output or feature change that breaks reproducibility

---

### Before Opening a PR

1. **Sync with upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run linting & tests locally:**
   ```bash
   # Format check
   black --check astroml/ tests/

   # Lint
   ruff check astroml/ tests/

   # Type check
   mypy astroml/

   # Full test suite
   pytest tests/ -v --cov=astroml
   ```

3. **Ensure commits are clean:**
   - Meaningful commit messages (see [Commit Convention](#commit-convention))
   - Logical, separated changes
   - No secrets or credentials

### Commit Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`

**Examples of good messages**:

```text
feat(training): add configurable early stopping
fix(ingestion): handle duplicate ledger ranges
docs(security): add vulnerability reporting guidance
```

**Scope**: `ingestion`, `graph`, `features`, `models`, `training`, `db`

**Examples:**

```
feat(features): add temporal decay feature extractor

- Implements exponential decay based on transaction age
- Configured via decay_rate parameter
- Tested with synthetic graphs

Closes #123
```

```
fix(ingestion): handle duplicate transaction deduplication

Fixes idempotency issue when re-running backfill on same ledger range.

Fixes #456
```

### PR Template

When opening a PR, fill out:

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issue
Closes #<issue_number>

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Tested against sample data

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed the code
- [ ] Updated documentation
- [ ] No new warnings generated
```

### Review Process

**Expectations:**

- Reviewers will provide feedback constructively
- Critical feedback focuses on the code, not the person
- Contributors should respond to all feedback (even if just acknowledging)
- Approval requires at least one maintainer sign-off
- Bug fixes should include a clear reproduction case when feasible
- New features should include configuration updates or examples when relevant

**What reviewers check:**

- ✅ Code correctness and logic
- ✅ Test coverage (especially for pipeline stages)
- ✅ Reproducibility (configs, seeds, checksums)
- ✅ Documentation completeness
- ✅ Alignment with "Research to Production" workflow
- ✅ Database integrity (for ingestion changes)

---

## Documentation

### Docstring Requirements

All public functions, classes, and modules must have docstrings:

```python
"""Module for extracting temporal features from transaction graphs.

This module implements exponential decay and recency weighting
for node features based on transaction timestamps.
"""

def calculate_temporal_decay(
    transactions: List[Transaction],
    decay_rate: float = 0.1,
) -> pd.DataFrame:
    """Calculate temporal decay weights for accounts.
    
    Uses exponential decay: weight = exp(-decay_rate * age_in_days)
    
    Args:
        transactions: List of Transaction objects (sorted by time)
        decay_rate: Decay coefficient (higher = faster decay)
        
    Returns:
        DataFrame with columns: [account_id, decay_weight, timestamp]
        
    Raises:
        ValueError: If decay_rate is negative or transactions list is empty
        
    Examples:
        >>> df = calculate_temporal_decay(transactions, decay_rate=0.1)
        >>> df.shape
        (1000, 3)
    """
```

### README Updates

When adding new features, update [README.md](README.md):

- Add to feature list if it's major functionality
- Update architecture diagram if pipeline changes
- Link to new example scripts or documentation

### Example Scripts

For new features, add an example in `examples/`:

```python
# examples/temporal_decay_example.py
"""Example: Extract temporal decay features."""

from astroml.features.temporal_decay import calculate_temporal_decay
from astroml.db.session import get_session

# Fetch transactions
session = get_session()
transactions = session.query(Transaction).all()

# Calculate temporal features
decay_df = calculate_temporal_decay(transactions, decay_rate=0.1)

print(f"Extracted temporal features for {len(decay_df)} accounts")
print(decay_df.head())
```

### Configuration Documentation

Document YAML config fields in docstrings and update [docs/CONFIGURATION.md](docs/CONFIGURATION.md) when configuration behavior changes:

```python
"""
Expected config (config/database.yaml):
    
    database:
      host: localhost
      port: 5432
      user: postgres
      password: ${DB_PASSWORD}  # From environment
      database: astroml
"""
```

---

## Questions & Support

- **Bug reports**: Open an issue on GitHub with reproducible example
- **Feature requests**: Use GitHub Discussions or open an issue with `[FEATURE]` tag
- **Questions**: Post in GitHub Discussions or tag with `[QUESTION]`
- **Security issues**: Follow [SECURITY.md](SECURITY.md) and report privately (do not open a public issue)

### Getting Help

1. **Check existing issues/discussions** for similar questions
2. **Search the documentation** in `docs/` and README
3. **Review example scripts** in `examples/`
4. **Run the discovery checklist** from [copilot-instructions.md](.github/copilot-instructions.md)

---

## Additional Resources

- [README.md](README.md) - Project overview and quick start
- [docs/](docs/) - Full documentation
- [examples/](examples/) - Example scripts for common tasks
- [alembic/versions/](alembic/versions/) - Database migration history
- [configs/](configs/) - Example configuration files

---

## Thank You! 🙏

Your contributions make AstroML better for the entire research community. Whether you're fixing bugs, adding features, or improving documentation, every contribution matters.

**Happy coding!**
