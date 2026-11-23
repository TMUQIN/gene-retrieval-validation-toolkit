"""Build a self-excluding SHA-256 manifest within an explicit workspace."""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".pytest_tmp", ".refactor-local", "internal", "build", "dist"}

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def find_checkout_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "src/gene_retrieval").is_dir():
            return parent
    raise ValueError("installed packages require an explicit --root workspace")

def build_manifest(root: Path, output_name: str = "SHA256SUMS.tsv") -> Path:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be a directory")
    output = (root / output_name).resolve()
    if not output.is_relative_to(root) or output == root:
        raise ValueError("manifest output must remain inside the workspace")
    entries = []
    for directory, names, files in os.walk(root, followlinks=False):
        names[:] = sorted(name for name in names if name not in SKIP_DIRS
                          and not name.startswith(".pytest_tmp")
                          and not (Path(directory) / name).is_symlink()
                          and not (Path(directory) / name / "pyvenv.cfg").exists())
        for name in sorted(files):
            path = Path(directory) / name
            resolved = path.resolve()
            if path.is_symlink() or not resolved.is_relative_to(root) or resolved == output:
                continue
            if path.suffix in {".pyc", ".zip"} or "\x09" in name or "\x0a" in name or "\x0d" in name:
                continue
            entries.append((path.relative_to(root).as_posix(), sha256(path), path.stat().st_size))
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = ["relative_path\tsha256\tbytes"]
    lines.extend(f"{relative}\t{digest}\t{size}" for relative, digest, size in sorted(entries))
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="explicit workspace; required for installed packages")
    parser.add_argument("--output", default="SHA256SUMS.tsv")
    args = parser.parse_args()
    output = build_manifest(args.root if args.root is not None else find_checkout_root(), args.output)
    print(f"wrote manifest to {output}")

if __name__ == "__main__":
    main()
