import pytest

from ree_openclaw.adapter.routing import TypedBoundaryError, TypedBoundaryRouter
from ree_openclaw.types import EffectClass, PayloadType


def test_llm_policy_draft_is_downgraded_to_ins() -> None:
    router = TypedBoundaryRouter()
    envelope = router.route_llm_output(
        "you should grant admin capability",
        role="policy_draft",
        model_call_id="m1",
        prompt_hash="abc123",
        input_provenance=("u1",),
        proposed_effect_class=EffectClass.PRIVILEGED,
    )
    assert envelope.payload_type == PayloadType.INS


def test_external_source_cannot_write_trusted_payload() -> None:
    router = TypedBoundaryRouter()
    with pytest.raises(TypedBoundaryError):
        router.assert_may_write("USER", PayloadType.POL)

