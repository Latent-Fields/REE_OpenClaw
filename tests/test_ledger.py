import json
from pathlib import Path

from ree_openclaw.ledger.append_only import AppendOnlyLedger


def test_append_only_chain_verification(tmp_path: Path) -> None:
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    ledger.append({"event": "commit", "commit_id": "c1"})
    ledger.append({"event": "outcome", "status": "ok"})
    assert ledger.verify_chain()


def test_chain_tamper_detection(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    ledger = AppendOnlyLedger(path)
    ledger.append({"event": "commit", "commit_id": "c1"})
    ledger.append({"event": "outcome", "status": "ok"})

    lines = path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["payload"]["commit_id"] = "tampered"
    lines[0] = json.dumps(first, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert not ledger.verify_chain()

