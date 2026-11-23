"""Configurable receipt-bound opt-in for caller-managed evaluation workspaces.

This application-level check does not grant data rights or replace OS access
controls. No project-specific path, scope or environment setting is implicit.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path, PureWindowsPath
import re
import secrets


class AuthorizationError(PermissionError):
    """Evaluation authorization is absent, invalid or not explicitly enabled."""


def generate_authorization_token() -> str:
    """Generate a random token; store only its SHA-256 digest in the receipt."""
    return secrets.token_urlsafe(48)


def _workspace_file(root: Path, filename: str | Path, label: str) -> Path:
    value = os.fspath(filename)
    path = Path(value)
    windows_path = PureWindowsPath(value)
    if (not value or not path.parts or path.is_absolute() or windows_path.drive
            or windows_path.root or ".." in path.parts or ".." in windows_path.parts
            or "\x00" in value):
        raise AuthorizationError(f"{label} must be a workspace-relative file path")
    candidate = root / path
    component = root
    for part in path.parts:
        component = component / part
        if component.is_symlink() or component.is_junction():
            raise AuthorizationError(f"{label} must not traverse links")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise AuthorizationError(f"{label} escaped the workspace")
    return resolved


def require_formal_authorization(
    workspace: Path,
    *,
    authorization_filename: str | Path,
    receipt_filename: str | Path,
    environment_variable: str,
    authorization_scope: str,
) -> dict[str, object]:
    """Validate explicit workspace, receipt, token, scope and process opt-in.

    Both filenames must be relative to an existing workspace, with no parent
    traversal, absolute paths or links. The receipt must be a JSON object with
    ``authorization_token_sha256`` (64 hexadecimal characters) and an exact
    ``authorization_scope`` match. The selected environment variable must be
    exactly ``YES``. Missing/invalid inputs raise AuthorizationError.

    Returns the validated receipt without adding the plaintext token. Callers
    must keep plaintext tokens out of receipts and other provenance metadata.
    All five configuration arguments are required; no legacy defaults apply.
    """
    try:
        if not isinstance(environment_variable, str) or not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*", environment_variable
        ):
            raise AuthorizationError("environment variable name is invalid")
        if not isinstance(authorization_scope, str) or not authorization_scope.strip():
            raise AuthorizationError("authorization scope must be nonempty")
        supplied_root = Path(workspace)
        if supplied_root.is_symlink() or supplied_root.is_junction():
            raise AuthorizationError("workspace must not be a link")
        root = supplied_root.resolve(strict=True)
        if not root.is_dir():
            raise AuthorizationError("workspace must be an existing directory")
        auth_path = _workspace_file(root, authorization_filename, "authorization filename")
        receipt_path = _workspace_file(root, receipt_filename, "receipt filename")
        if auth_path == receipt_path:
            raise AuthorizationError("authorization and receipt paths must be distinct")
        if not auth_path.is_file():
            raise AuthorizationError("authorization file is missing")
        if not receipt_path.is_file():
            raise AuthorizationError("authorization receipt is missing")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not isinstance(receipt, dict):
            raise AuthorizationError("authorization receipt must be a JSON object")
        token = auth_path.read_text(encoding="utf-8").strip()
        expected_hash = receipt.get("authorization_token_sha256")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
            raise AuthorizationError("authorization receipt token digest is invalid")
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        if not token or not hmac.compare_digest(token_hash, expected_hash.lower()):
            raise AuthorizationError("authorization token hash is invalid")
        if receipt.get("authorization_scope") != authorization_scope:
            raise AuthorizationError("authorization scope is invalid")
        if os.environ.get(environment_variable) != "YES":
            raise AuthorizationError(f"set {environment_variable}=YES to explicitly opt in")
        return receipt
    except AuthorizationError:
        raise
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        raise AuthorizationError("authorization inputs are invalid or unreadable") from exc
