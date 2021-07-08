from datetime import timedelta
import logging,re,asyncio
from homeassistant.components.number import NumberEntity

from .entity import HitachiBaseEntity
from .const import (
    DOMAIN,
    UPDATE_INTERVAL,
    DATA_CLIENT,
    DATA_COORDINATOR,
)

_LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(seconds=UPDATE_INTERVAL)


async def async_setup_entry(hass, entry, async_add_entities) -> bool:
    await asyncio.sleep(1)
    client = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    devices = coordinator.data
    numbers = []
    for device in devices:
        for key, entity in device["Command"].items():
            if (entity["Readonly"]==False) and (entity["CMDtype"]==0x02):
                numbers.append(HitachiSensor(client,device,key,))                                                                         
    async_add_entities(numbers, True)
    return True

class HitachiSensor(HitachiBaseEntity, NumberEntity):
    """ Hitachi AC outdoor temperature sensor """
    def __init__(self, client ,device, cmd):
        super().__init__(client, device)
        self.commands = device["Command"][cmd]
        self.cmd=cmd

    async def async_update(self):
        if self.auth['ContMID'] in self.hass.data[DOMAIN]:
            self.status=self.hass.data[DOMAIN][self.auth['ContMID']]

    @property
    def label(self) -> str:
        return self.commands["Name"]

    @property
    def icon(self) -> str:
        return self.commands["ICON"]

    @property
    def value(self) -> int:
        if ( self.cmd in self.status):
            return int(self.status[self.cmd])
        else:
            _LOGGER.debug(f"------- UPDATING fail {self.nickname} {self.status}-------")
            return 0.0

    async def async_set_value(self, value: int) -> None:
        await self.client.set_command(self.device, self.cmd|0x80, int(value))

    @property
    def max_value(self):
        return self.commands["MAX"]

    @property
    def min_value(self):
        return self.commands["MIN"]

    @property
    def unit_of_measurement(self) -> str:
        return self.commands["UNIT"]