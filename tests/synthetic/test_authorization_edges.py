"""Artificial tokens and receipts exercise caller-controlled authorization."""
import hashlib
import json
import pytest
from gene_retrieval.evaluation import authorization as auth

SETTINGS = dict(authorization_filename="approval.txt", receipt_filename="receipt.json", environment_variable="SYNTHETIC_TOOL_OPT_IN", authorization_scope="SYNTHETIC_SCOPE")

def setup_receipt(root, token="artificial-token", scope="SYNTHETIC_SCOPE", settings=None):
    settings = settings or SETTINGS
    token_path = root / settings["authorization_filename"]
    receipt_path = root / settings["receipt_filename"]
    token_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(token, encoding="utf-8")
    receipt_path.write_text(json.dumps({"authorization_token_sha256": hashlib.sha256(token.encode()).hexdigest(), "authorization_scope": scope}), encoding="utf-8")
    return receipt_path

@pytest.mark.parametrize("case", ["malformed", "scope", "empty_token", "environment"])
def test_authorization_denies_invalid_inputs(synthetic_workspace, monkeypatch, case):
    path = setup_receipt(synthetic_workspace, token="" if case == "empty_token" else "artificial-token", scope="WRONG" if case == "scope" else SETTINGS["authorization_scope"])
    monkeypatch.setenv(SETTINGS["environment_variable"], "YES" if case != "environment" else "NO")
    if case == "malformed": path.write_text("{", encoding="utf-8")
    with pytest.raises(auth.AuthorizationError): auth.require_formal_authorization(synthetic_workspace, **SETTINGS)

def test_authorization_returns_receipt_without_plaintext(synthetic_workspace, monkeypatch):
    setup_receipt(synthetic_workspace)
    monkeypatch.setenv(SETTINGS["environment_variable"], "YES")
    receipt = auth.require_formal_authorization(synthetic_workspace, **SETTINGS)
    assert "artificial-token" not in json.dumps(receipt)
    first, second = auth.generate_authorization_token(), auth.generate_authorization_token()
    assert first != second and len(first) >= 48

@pytest.mark.parametrize("key,value", [
    ("authorization_filename", "../outside.txt"), ("receipt_filename", "../outside.json"),
    ("authorization_filename", r"..\outside.txt"), ("receipt_filename", r"C:relative.json"),
    ("authorization_filename", r"C:\outside.txt"), ("receipt_filename", r"\\server\share\receipt.json"),
    ("authorization_filename", ""), ("receipt_filename", "."),
    ("authorization_filename", "bad\x00name"), ("receipt_filename", "approval.txt"),
    ("environment_variable", ""), ("environment_variable", "NOT A NAME"),
    ("authorization_scope", ""), ("authorization_scope", None),
])
def test_authorization_rejects_invalid_configuration(synthetic_workspace, key, value):
    settings = {**SETTINGS, key: value}
    with pytest.raises(auth.AuthorizationError): auth.require_formal_authorization(synthetic_workspace, **settings)

@pytest.mark.parametrize("which", ["authorization_filename", "receipt_filename"])
def test_authorization_rejects_absolute_paths(synthetic_workspace, which):
    settings = {**SETTINGS, which: str(synthetic_workspace / "absolute.txt")}
    with pytest.raises(auth.AuthorizationError, match="relative"):
        auth.require_formal_authorization(synthetic_workspace, **settings)

@pytest.mark.parametrize("kind", ["absent", "file"])
def test_authorization_rejects_invalid_workspace(synthetic_workspace, kind):
    root = synthetic_workspace / "not_a_workspace"
    if kind == "file": root.write_text("artificial", encoding="utf-8")
    with pytest.raises(auth.AuthorizationError): auth.require_formal_authorization(root, **SETTINGS)

@pytest.mark.parametrize("payload", [[], None, "text", 3, {}, {"authorization_token_sha256": 17}, {"authorization_token_sha256": "short"}, {"authorization_token_sha256": "g" * 64}])
def test_authorization_rejects_invalid_receipt_structure(synthetic_workspace, monkeypatch, payload):
    path = setup_receipt(synthetic_workspace)
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(SETTINGS["environment_variable"], "YES")
    with pytest.raises(auth.AuthorizationError): auth.require_formal_authorization(synthetic_workspace, **SETTINGS)

@pytest.mark.parametrize("which", ["authorization_filename", "receipt_filename"])
def test_authorization_rejects_unreadable_text(synthetic_workspace, monkeypatch, which):
    setup_receipt(synthetic_workspace)
    (synthetic_workspace / SETTINGS[which]).write_bytes(b"\xff")
    monkeypatch.setenv(SETTINGS["environment_variable"], "YES")
    with pytest.raises(auth.AuthorizationError): auth.require_formal_authorization(synthetic_workspace, **SETTINGS)

def test_authorization_uses_all_custom_settings(synthetic_workspace, monkeypatch):
    settings = dict(authorization_filename="custom/token.txt", receipt_filename="metadata/approval.json", environment_variable="ANOTHER_SYNTHETIC_OPT_IN", authorization_scope="ANOTHER_SYNTHETIC_SCOPE")
    setup_receipt(synthetic_workspace, scope=settings["authorization_scope"], settings=settings)
    monkeypatch.setenv(SETTINGS["environment_variable"], "YES")
    monkeypatch.delenv(settings["environment_variable"], raising=False)
    with pytest.raises(auth.AuthorizationError): auth.require_formal_authorization(synthetic_workspace, **settings)
    monkeypatch.setenv(settings["environment_variable"], "YES")
    assert auth.require_formal_authorization(synthetic_workspace, **settings)["authorization_scope"] == settings["authorization_scope"]
