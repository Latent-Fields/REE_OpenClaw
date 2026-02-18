import pytest

from ree_openclaw.rc.scoring import RCConflictScorer, RCConflictSignals, RCConflictWeights


def test_rc_conflict_scorer_weighted_average() -> None:
    scorer = RCConflictScorer(
        RCConflictWeights(
            provenance_mismatch=0.4,
            identity_capability_inconsistency=0.3,
            temporal_discontinuity=0.2,
            tool_output_inconsistency=0.1,
        )
    )
    score = scorer.score(
        RCConflictSignals(
            provenance_mismatch=1.0,
            identity_capability_inconsistency=0.5,
            temporal_discontinuity=0.0,
            tool_output_inconsistency=0.0,
        )
    )
    assert score == pytest.approx(0.55)


def test_rc_conflict_scorer_rejects_out_of_range_signal() -> None:
    scorer = RCConflictScorer()
    with pytest.raises(ValueError):
        scorer.score(
            RCConflictSignals(
                provenance_mismatch=1.2,
                identity_capability_inconsistency=0.0,
                temporal_discontinuity=0.0,
                tool_output_inconsistency=0.0,
            )
        )
