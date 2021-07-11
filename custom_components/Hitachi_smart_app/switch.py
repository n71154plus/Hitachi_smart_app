from datetime import timedelta
import logging,re,asyncio
from homeassistant.components.switch import SwitchEntity

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
    switchs = []
    for device in devices:
        for key, entity in device["Command"].items():
            if (entity["Readonly"]==False) and (entity["CMDtype"]==0x00):
                switchs.append(HitachiSensor(client,device,key,))                                                                         
    async_add_entities(switchs, True)
    return True

class HitachiSensor(HitachiBaseEntity, SwitchEntity):
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
    def is_on(self) -> bool:
        if ( self.cmd in self.status):
            return bool(self.status[self.cmd])
        else:
            _LOGGER.debug(f"------- UPDATING fail {self.nickname} {self.status}-------")
            return False

    async def async_turn_on(self, **kwargs):
        await self.client.set_command(self.device, self.cmd|0x80, 1)

    async def async_turn_off(self, **kwargs):
        await self.client.set_command(self.device, self.cmd|0x80, 0)
