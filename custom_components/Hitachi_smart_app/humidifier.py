import logging,re
from datetime import timedelta
from homeassistant.components.humidifier import HumidifierEntity
from homeassistant.components.humidifier.const import (
    DEVICE_CLASS_DEHUMIDIFIER,
    SUPPORT_MODES,
)

from .entity import HitachiBaseEntity
from .const import (
    DOMAIN,
    UPDATE_INTERVAL,
    DEVICE_TYPE_DEHUMIDIFIER,
    DATA_CLIENT,
    DATA_COORDINATOR,
)

_LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(seconds=UPDATE_INTERVAL)

async def async_setup_entry(hass, entry, async_add_entities) -> bool:
    client = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    devices = coordinator.data
    humidifiers = []

    for device in devices:
        if device["DeviceType"] == DEVICE_TYPE_DEHUMIDIFIER:
            humidifiers.append(
                HitachiDehumidifier(client,device)
            )

    async_add_entities(humidifiers, True)

    return True


class HitachiDehumidifier(HitachiBaseEntity, HumidifierEntity):
    def __init__(self, client, device):

        super().__init__(client, device)
        self.commands=device['Command']

    async def async_update(self):
        status={}
        _status = await self.client.get_device_info(self.auth)
        obj=re.findall(b".{3}(.*)", _status,re.DOTALL)
        d_info=re.findall(b"(.{1})(.{2})",obj[0],re.DOTALL)
        for s in d_info:
            status[int.from_bytes(s[0],byteorder='big',signed=True)]=int.from_bytes(s[1],byteorder='big',signed=True)
        self.status=status
        self.hass.data[DOMAIN][self.auth['ContMID']]=status
        _LOGGER.debug(f"------- UPDATING {self.status}-------")


    @property
    def label(self):
        return ""

    @property
    def target_humidity(self):
        if ( 3 in self.status):
            return int(self.status[3])
        else:
            _LOGGER.debug(f"------- UPDATING fail {self.nickname} {self.status}-------")
            return 0.0

    @property
    def current_humidity(self) -> int:
        """ Return the current humidity """
        if ( 7 in self.status):
            return int(self.status[7])
        else:
            _LOGGER.debug(f"------- UPDATING fail {self.nickname} {self.status}-------")
            return 0.0
            
    @property
    def max_humidity(self):
        if ( 3 in self.commands):
            return self.commands[3]["MAX"]
        else:
            _LOGGER.debug(f"------- UPDATING max_humidity fail {self.nickname} {self.commands}-------")
            return 0.0

    @property
    def min_humidity(self):
        if ( 3 in self.commands):
            return self.commands[3]["MIN"]
        else:
            _LOGGER.debug(f"------- UPDATING min_humidity fail {self.nickname} {self.commands}-------")
            return 0.0

    @property
    def mode(self):
        return self.commands[1]["Table"][self.status[1]]

    @property
    def available_modes(self):
        if (1 in self.commands):
            return list(self.commands[1]["Table"].values())

    @property
    def supported_features(self):
        return SUPPORT_MODES

    @property
    def is_on(self):
        return self.status[0]

    async def async_set_mode(self, mode):
        """ Set operation mode """
        modeindex = [k for k, v in self.commands[1]["Table"].items() if v == mode]
        await self.client.set_command(self.device, 129, modeindex[0])

    async def async_set_humidity(self, humidity):
        """ Set target humidity """
        await self.client.set_command(self.device, 131, humidity)
        

    async def async_turn_on(self):
        """ Turn on dehumidifier """
        _LOGGER.debug(f"[{self.nickname}] Turning on")
        await self.client.set_command(self.device, 128, 1)


    async def async_turn_off(self):
        """ Turn off dehumidifier """
        _LOGGER.debug(f"[{self.nickname}] Turning off")
        await self.client.set_command(self.device, 128, 0)