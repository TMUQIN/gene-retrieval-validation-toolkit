import csv
from pathlib import Path
import pytest
from gene_retrieval.evaluation.build_manifest import build_manifest, find_checkout_root, sha256

def test_manifest_containment_and_self_exclusion(synthetic_workspace):
    root = synthetic_workspace
    (root / "literal.txt").write_bytes(b"artificial\n")
    for folder in [".git", "internal", "__pycache__", ".venv", ".pytest_tmp"]:
        (root / folder).mkdir()
        (root / folder / "excluded.txt").write_text("artificial", encoding="utf-8")
    (root / "other_env").mkdir()
    (root / "other_env" / "pyvenv.cfg").write_text("include-system-site-packages = false", encoding="utf-8")
    result = build_manifest(root)
    first = result.read_bytes()
    build_manifest(root)
    assert result.read_bytes() == first
    with result.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert rows == [{"relative_path": "literal.txt", "sha256": sha256(root / "literal.txt"), "bytes": "11"}]
    with pytest.raises(ValueError, match="inside"):
        build_manifest(root, "../escape.tsv")
    with pytest.raises(ValueError, match="inside"):
        build_manifest(root, str(root.parent / "escape.tsv"))

def test_installed_manifest_requires_explicit_root():
    # The clean-room suite executes the wheel-installed package outside a checkout.
    import gene_retrieval
    if "site-packages" in Path(gene_retrieval.__file__).parts:
        with pytest.raises(ValueError, match="explicit --root"):
            find_checkout_root()
    else:
        assert (find_checkout_root() / "pyproject.toml").is_file()
