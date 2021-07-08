from datetime import timedelta
import logging,re,asyncio
from homeassistant.components.fan import FanEntity

from .entity import HitachiBaseEntity
from .const import (
    DOMAIN,
    UPDATE_INTERVAL,
    DEVICE_TYPE_DEHUMIDIFIER,
    DEVICE_TYPE_AC,
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
    fans = []
    for device in devices:
        for key, entity in device["Command"].items():
            if (entity["Readonly"]==False) and (entity["CMDtype"]==0x01):
                fans.append(HitachiSensor(client,device,key,))                                                                         
    async_add_entities(fans, True)
    return True

class HitachiSensor(HitachiBaseEntity, FanEntity):
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
    def supported_features(self):
        return 0x08

    @property
    def preset_mode(self) -> str:
        if ( self.cmd in self.status):
            return self.commands["Table"][self.status[self.cmd]]
        else:
            _LOGGER.debug(f"------- UPDATING fail {self.nickname} {self.status}-------")
            return ""

    @property
    def preset_modes(self) -> list:
        return list(self.commands["Table"].values())
            
    async def async_set_preset_mode(self, preset_mode) -> None:
        """ Set operation mode """
        modeindex = [k for k, v in self.commands["Table"].items() if v == preset_mode]
        await self.client.set_command(self.device, self.cmd|0x80, modeindex[0])
