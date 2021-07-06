from datetime import timedelta
from abc import ABC, abstractmethod

from .const import (
    DOMAIN,
    MANUFACTURER,
    UPDATE_INTERVAL,
)

SCAN_INTERVAL = timedelta(seconds=UPDATE_INTERVAL)


class HitachiBaseEntity(ABC):
    def __init__(
        self,
        client,
        device,
    ):
        self.client = client
        self.device = device

    @property
    @abstractmethod
    def label(self) -> str:
        """Label to use for name and unique id."""
        ...

    @property
    def current_device_info(self) -> dict:
        return self.device

    @property
    def nickname(self) -> str:
        return self.current_device_info["DeviceName"]

    @property
    def name(self) -> str:
        return f"{self.nickname} {self.label}"

    @property
    def auth(self) -> dict:
        return self.device['DeviceID']

    @property
    def unique_id(self) -> str:
        return str(self.auth['ContMID']) + self.label

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, str(self.auth['ContMID']))},
            "name": self.nickname,
            "manufacturer": self.current_device_info["Manufacturer"],
            "model": self.current_device_info["ModelName"],
        }
