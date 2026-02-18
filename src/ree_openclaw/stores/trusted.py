from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ree_openclaw.adapter.routing import TypedBoundaryRouter
from ree_openclaw.types import PayloadType


class TrustedStoreError(PermissionError):
    """Raised when an untrusted source attempts trusted-store mutation."""


@dataclass
class TrustedStores:
    router: TypedBoundaryRouter = field(default_factory=TypedBoundaryRouter)
    policy_store: dict[str, Any] = field(default_factory=dict)
    identity_store: dict[str, Any] = field(default_factory=dict)
    capability_store: dict[str, Any] = field(default_factory=dict)

    def _target_store(self, store_type: PayloadType) -> dict[str, Any]:
        if store_type == PayloadType.POL:
            return self.policy_store
        if store_type == PayloadType.ID:
            return self.identity_store
        if store_type == PayloadType.CAPS:
            return self.capability_store
        raise ValueError(f"unsupported trusted store type: {store_type.value}")

    def write(self, *, source_class: str, store_type: PayloadType, key: str, value: Any) -> None:
        try:
            self.router.assert_may_write(source_class, store_type)
        except ValueError as exc:
            raise TrustedStoreError(str(exc)) from exc
        store = self._target_store(store_type)
        store[key] = value

    def read(self, *, store_type: PayloadType, key: str) -> Any | None:
        store = self._target_store(store_type)
        return store.get(key)
