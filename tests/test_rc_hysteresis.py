from ree_openclaw.rc.hysteresis import RCHysteresis, RCState


def test_hysteresis_state_flow() -> None:
    lane = RCHysteresis()
    assert lane.update(0.1) == RCState.NORMAL
    assert lane.update(0.7) == RCState.VERIFY
    assert lane.update(0.8) == RCState.VERIFY
    assert lane.update(0.92) == RCState.LOCKDOWN
    assert lane.update(0.7) == RCState.VERIFY
    assert lane.update(0.2) == RCState.NORMAL

