import json
from pathlib import Path

import pytest

from ree_openclaw.ledger.append_only import AppendOnlyLedger
from ree_openclaw.offline.consolidation import OfflineConsolidator, OfflineTriggerError


def test_offline_consolidation_emits_skill_reliability_summary(tmp_path: Path) -> None:
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    ledger.append(
        {
            "event": "commit_executed",
            "action_class": "WRITE_FILE",
            "execution": {"returncode": 0},
        }
    )
    ledger.append(
        {
            "event": "proposal_rejected",
            "action_class": "SEND_EMAIL",
            "reason": "consent_required",
        }
    )
    consolidator = OfflineConsolidator(ledger, tmp_path / "offline")

    result = consolidator.consolidate(trigger_source="operator_cli")
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))

    assert result.processed_entries == 2
    assert payload["action_reliability"]["WRITE_FILE"]["commit_events"] == 1
    assert payload["action_reliability"]["WRITE_FILE"]["success_rate"] == 1.0
    assert payload["action_reliability"]["SEND_EMAIL"]["commit_events"] == 0


def test_offline_consolidation_blocks_untrusted_trigger(tmp_path: Path) -> None:
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    consolidator = OfflineConsolidator(ledger, tmp_path / "offline")
    with pytest.raises(OfflineTriggerError):
        consolidator.consolidate(trigger_source="user_ins")
