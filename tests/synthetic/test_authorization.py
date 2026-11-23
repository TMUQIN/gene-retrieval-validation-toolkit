"""The inherited fail-closed scenario, adapted to explicit generic settings."""
import hashlib
import json
import pytest
from gene_retrieval.evaluation.authorization import AuthorizationError, require_formal_authorization


def test_formal_truth_access_is_fail_closed(monkeypatch: pytest.MonkeyPatch, synthetic_workspace) -> None:
    run_root = synthetic_workspace
    (run_root / "inputs").mkdir()
    settings = dict(authorization_filename="inputs/consent.txt", receipt_filename="reports/receipt.json", environment_variable="SYNTHETIC_EVALUATION_OPT_IN", authorization_scope="SYNTHETIC_EVALUATION")
    with pytest.raises(AuthorizationError, match="missing"):
        require_formal_authorization(run_root, **settings)
    auth = run_root / settings["authorization_filename"]
    auth.write_text("synthetic-random-token", encoding="utf-8")
    with pytest.raises(AuthorizationError, match="receipt is missing"):
        require_formal_authorization(run_root, **settings)
    (run_root / "reports").mkdir()
    receipt = {"authorization_token_sha256": hashlib.sha256(b"different-token").hexdigest(), "authorization_scope": settings["authorization_scope"]}
    receipt_path = run_root / settings["receipt_filename"]
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(AuthorizationError, match="token hash is invalid"):
        require_formal_authorization(run_root, **settings)
    receipt["authorization_token_sha256"] = hashlib.sha256(b"synthetic-random-token").hexdigest()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.delenv(settings["environment_variable"], raising=False)
    with pytest.raises(AuthorizationError, match=settings["environment_variable"]):
        require_formal_authorization(run_root, **settings)
    monkeypatch.setenv(settings["environment_variable"], "YES")
    require_formal_authorization(run_root, **settings)
