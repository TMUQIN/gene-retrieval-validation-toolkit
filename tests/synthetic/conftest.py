"""Use the installed package and fresh artificial scratch data; no sys.path injection."""
from pathlib import Path
import os
import shutil
import tempfile
import uuid
import pytest

@pytest.fixture
def synthetic_workspace():
    scratch_root = os.environ.get("GENE_RETRIEVAL_TEST_SCRATCH")
    parent = Path(scratch_root or tempfile.gettempdir()).resolve()
    workspace = parent / ("synthetic-" + uuid.uuid4().hex)
    workspace.mkdir(parents=True)
    try:
        yield workspace
    finally:
        if workspace.parent == parent and workspace.name.startswith("synthetic-"):
            shutil.rmtree(workspace)
