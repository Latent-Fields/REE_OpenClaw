import pytest

from ree_openclaw.stores.trusted import TrustedStoreError, TrustedStores
from ree_openclaw.types import PayloadType


def test_untrusted_source_cannot_write_trusted_store() -> None:
    stores = TrustedStores()
    with pytest.raises(TrustedStoreError):
        stores.write(
            source_class="USER",
            store_type=PayloadType.POL,
            key="policy_mode",
            value="unsafe",
        )


def test_trusted_internal_can_write_and_read_trusted_store() -> None:
    stores = TrustedStores()
    stores.write(
        source_class="trusted_internal",
        store_type=PayloadType.CAPS,
        key="manifest_version",
        value="v1",
    )
    assert stores.read(store_type=PayloadType.CAPS, key="manifest_version") == "v1"
