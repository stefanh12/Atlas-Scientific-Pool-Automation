"""ESPHome native API transport layer."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


class ESPHomeTransportError(HomeAssistantError):
    """Raised when ESPHome transport operations fail."""


@dataclass(slots=True)
class NodeSnapshot:
    """Latest known entity metadata and values for one node."""

    device_name: str
    model: str | None
    mac_address: str | None
    infos_by_object_id: dict[str, Any] = field(default_factory=dict)
    states_by_key: dict[int, Any] = field(default_factory=dict)


class ESPHomeNodeClient:
    """Thin wrapper over aioesphomeapi APIClient."""

    def __init__(
        self,
        host: str,
        port: int,
        noise_psk: str | None,
        timeout: float,
    ) -> None:
        self._host = host
        self._port = port
        self._noise_psk = noise_psk
        self._timeout = timeout

        self._api: Any | None = None
        self._unsubscribe_state: Any | None = None
        self._snapshot = NodeSnapshot(device_name=host, model=None, mac_address=None)
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Connect and bootstrap metadata/state subscription."""
        async with self._lock:
            if self._api is not None:
                return

            try:
                from aioesphomeapi import APIClient
                from aioesphomeapi.core import APIConnectionError
            except ImportError as err:
                raise ESPHomeTransportError(
                    "aioesphomeapi is required for atlas_scientific_pool"
                ) from err

            api = APIClient(
                address=self._host,
                port=self._port,
                noise_psk=self._noise_psk or None,
            )

            try:
                await asyncio.wait_for(api.connect(login=True), timeout=self._timeout)
                device_info = await asyncio.wait_for(
                    api.device_info(), timeout=self._timeout
                )
                entities = await asyncio.wait_for(
                    api.list_entities_services(), timeout=self._timeout
                )
            except (TimeoutError, APIConnectionError) as err:
                raise ESPHomeTransportError(
                    f"Could not connect to ESPHome node {self._host}:{self._port}"
                ) from err

            infos: dict[str, Any] = {}
            for info in entities:
                object_id = getattr(info, "object_id", None)
                if object_id:
                    infos[object_id] = info

            def _state_callback(state: Any) -> None:
                key = getattr(state, "key", None)
                if key is None:
                    return
                self._snapshot.states_by_key[key] = state

            unsubscribe = api.subscribe_states(_state_callback)

            self._api = api
            self._unsubscribe_state = unsubscribe
            self._snapshot = NodeSnapshot(
                device_name=getattr(device_info, "name", self._host),
                model=getattr(device_info, "model", None),
                mac_address=getattr(device_info, "mac_address", None),
                infos_by_object_id=infos,
                states_by_key=self._snapshot.states_by_key,
            )

    async def disconnect(self) -> None:
        """Disconnect client and release callbacks."""
        async with self._lock:
            if self._unsubscribe_state is not None:
                self._unsubscribe_state()
                self._unsubscribe_state = None

            if self._api is not None:
                await self._api.disconnect(force=True)
                self._api = None

    async def refresh(self) -> NodeSnapshot:
        """Ensure connection and return latest snapshot."""
        await self.connect()
        return self._snapshot

    async def press_button(self, object_id: str) -> None:
        """Execute a button press on the node."""
        await self.connect()
        info = self._snapshot.infos_by_object_id.get(object_id)
        if info is None:
            raise ESPHomeTransportError(f"Button object_id '{object_id}' not found")

        key = getattr(info, "key", None)
        if key is None:
            raise ESPHomeTransportError(f"Button '{object_id}' has no key")

        self._api.button_command(key)  # type: ignore[union-attr]

    async def set_number(self, object_id: str, value: float) -> None:
        """Set a numeric entity value on the node."""
        await self.connect()
        info = self._snapshot.infos_by_object_id.get(object_id)
        if info is None:
            raise ESPHomeTransportError(f"Number object_id '{object_id}' not found")

        key = getattr(info, "key", None)
        if key is None:
            raise ESPHomeTransportError(f"Number '{object_id}' has no key")

        self._api.number_command(key, float(value))  # type: ignore[union-attr]

    async def set_switch(self, object_id: str, is_on: bool) -> None:
        """Set a switch entity value on the node."""
        await self.connect()
        info = self._snapshot.infos_by_object_id.get(object_id)
        if info is None:
            raise ESPHomeTransportError(f"Switch object_id '{object_id}' not found")

        key = getattr(info, "key", None)
        if key is None:
            raise ESPHomeTransportError(f"Switch '{object_id}' has no key")

        self._api.switch_command(key, bool(is_on))  # type: ignore[union-attr]

    async def set_select(self, object_id: str, option: str) -> None:
        """Set a select entity option on the node."""
        await self.connect()
        info = self._snapshot.infos_by_object_id.get(object_id)
        if info is None:
            raise ESPHomeTransportError(f"Select object_id '{object_id}' not found")

        key = getattr(info, "key", None)
        if key is None:
            raise ESPHomeTransportError(f"Select '{object_id}' has no key")

        self._api.select_command(key, str(option))  # type: ignore[union-attr]

    def value_for_object_id(self, object_id: str) -> Any | None:
        """Return latest state object for an object_id."""
        info = self._snapshot.infos_by_object_id.get(object_id)
        if info is None:
            return None
        key = getattr(info, "key", None)
        if key is None:
            return None
        return self._snapshot.states_by_key.get(key)

    def state_value(self, object_id: str) -> Any | None:
        """Return scalar `state` value for object_id when available."""
        state = self.value_for_object_id(object_id)
        if state is None:
            return None
        return getattr(state, "state", None)

    def all_sensor_object_ids(self) -> list[str]:
        """Return object IDs that look like measurable entities."""
        result: list[str] = []
        for object_id, info in self._snapshot.infos_by_object_id.items():
            class_name = type(info).__name__.lower()
            if "sensor" in class_name:
                result.append(object_id)
        return result

    def all_number_object_ids(self) -> list[str]:
        """Return object IDs for number entities."""
        result: list[str] = []
        for object_id, info in self._snapshot.infos_by_object_id.items():
            if "number" in type(info).__name__.lower():
                result.append(object_id)
        return result

    def all_button_object_ids(self) -> list[str]:
        """Return object IDs for button entities."""
        result: list[str] = []
        for object_id, info in self._snapshot.infos_by_object_id.items():
            if "button" in type(info).__name__.lower():
                result.append(object_id)
        return result

    def all_switch_object_ids(self) -> list[str]:
        """Return object IDs for switch entities."""
        result: list[str] = []
        for object_id, info in self._snapshot.infos_by_object_id.items():
            if "switch" in type(info).__name__.lower():
                result.append(object_id)
        return result

    def all_select_object_ids(self) -> list[str]:
        """Return object IDs for select entities."""
        result: list[str] = []
        for object_id, info in self._snapshot.infos_by_object_id.items():
            if "select" in type(info).__name__.lower():
                result.append(object_id)
        return result
