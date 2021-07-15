from datetime import timedelta
import logging,re,asyncio
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
)

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
    sensors = []
    for device in devices:
        for key, entity in device["Command"].items():
            if (entity["Readonly"]==True):
                sensors.append(HitachiSensor(client,device,key,))                                                                         
    async_add_entities(sensors, True)
    return True

class HitachiSensor(HitachiBaseEntity, SensorEntity):
    """ Hitachi AC outdoor temperature sensor """
    def __init__(self, client ,device, cmd):
        super().__init__(client, device)
        self.commands = device["Command"][cmd]
        self.cmd=cmd

    async def async_update(self):
        if self.auth['ContMID'] in self.hass.data[DOMAIN]:
            self.status=self.hass.data[DOMAIN][self.auth['ContMID']]

    @property
    def device_class(self):
        name = self.commands["Name"]
        if '溫度' in name:
            return DEVICE_CLASS_TEMPERATURE
        if '濕度' in name:
            return DEVICE_CLASS_HUMIDITY

    @property
    def label(self) -> str:
        return self.commands["Name"]

    @property
    def icon(self) -> str:
        return self.commands["ICON"]

    @property
    def state(self) -> int:
        if ( self.cmd in self.status):
            return self.status[self.cmd]
        else:
            _LOGGER.debug(f"------- UPDATING fail {self.nickname} {self.status}-------")
            return 0.0

    @property
    def unit_of_measurement(self) -> str:
        return self.commands["UNIT"]