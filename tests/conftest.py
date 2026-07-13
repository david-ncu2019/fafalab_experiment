from pathlib import Path
import sys
from uuid import uuid4

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


@pytest.fixture
def tmp_path() -> Path:
    """Workspace-local temp path for restricted Windows environments."""
    path = Path(".test-runtime") / uuid4().hex
    path.mkdir(parents=True)
    return path.resolve()


@pytest.fixture
def valid_source(tmp_path: Path) -> Path:
    path = tmp_path / "Sample_8-1-2.csv"
    pd.DataFrame({
        "Sieve": ["#4", "#10", "#20", "#30", "#40", "#50", "#60", "#80", "#100", "#140", "#200", "#400", "Pan"],
        "Sample_Mass(g)": [0.0, 26.34, 0.0, 0.0, 12.10, 18.55, 0.0, 0.0, 0.0, 0.0, 15.21, 10.88, 114.44],
    }).to_csv(path, index=False)
    return path
