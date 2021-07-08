import logging,asyncio,re
from datetime import timedelta
from homeassistant.components.climate import ClimateEntity
from homeassistant.const import (
    TEMP_CELSIUS,
    ATTR_TEMPERATURE,
)
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_AUTO,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
)

from .entity import HitachiBaseEntity
from .const import (
    DOMAIN,
    DEVICE_TYPE_AC,
    UPDATE_INTERVAL,
    DATA_CLIENT,
    DATA_COORDINATOR,
)

_LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(seconds=UPDATE_INTERVAL)


def getKeyFromDict(targetDict, mode_name):
    for key, value in targetDict.items():
        if mode_name == value:
            return key

    return None


async def async_setup_entry(hass, entry, async_add_entities) -> bool:
    client = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    devices = coordinator.data
    climate = []

    for device in devices:
        if device["DeviceType"] == DEVICE_TYPE_AC:
            climate.append( HitachiClimate(client,device))

    async_add_entities(climate, True)

    return True


class HitachiClimate(HitachiBaseEntity, ClimateEntity):
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
    def supported_features(self) -> int:
        """Return the list of supported features."""
        outdata=0
        if (3 in self.commands):
            outdata|=SUPPORT_TARGET_TEMPERATURE
        if (2 in self.commands):
            outdata|=SUPPORT_FAN_MODE
        if ( (15 in self.commands) or (17 in self.commands)):
            outdata|=SUPPORT_SWING_MODE
        if ((26 in self.commands) or (27 in self.commands)):
            outdata|=SUPPORT_PRESET_MODE
        return outdata 

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def hvac_mode(self) -> str:
        """Return the current operation."""
        if not bool(self.status[0]):
            return HVAC_MODE_OFF
        else:
            if self.status[1] ==0:
                return HVAC_MODE_COOL
            elif self.status[1] ==1 :
                return HVAC_MODE_DRY
            elif self.status[1] ==2 :
                return HVAC_MODE_FAN_ONLY
            elif self.status[1] ==3 :
                return HVAC_MODE_AUTO
            elif self.status[1] ==4 :
                return HVAC_MODE_HEAT
            else:
                return HVAC_MODE_OFF

    @property
    def hvac_modes(self) -> list:
        _hvacmodes=[]
        if (0 in self.commands):
            _hvacmodes.append(HVAC_MODE_OFF)
        if (1 in self.commands):
            if (0 in self.commands[1]["Table"]):
                _hvacmodes.append(HVAC_MODE_COOL)
            if (1 in self.commands[1]["Table"]):
                _hvacmodes.append(HVAC_MODE_DRY)
            if (2 in self.commands[1]["Table"]):
                _hvacmodes.append(HVAC_MODE_FAN_ONLY)
            if (3 in self.commands[1]["Table"]):
                _hvacmodes.append(HVAC_MODE_AUTO)
            if (4 in self.commands[1]["Table"]):
                _hvacmodes.append(HVAC_MODE_HEAT)
        return _hvacmodes

    async def async_set_hvac_mode(self, hvac_mode) -> None:
        _LOGGER.debug(f"[{self.nickname}] set_hvac_mode: {hvac_mode}")
        if hvac_mode == HVAC_MODE_OFF:
            await self.client.set_command(self.device, 128, 0)
        else:
            if hvac_mode == HVAC_MODE_COOL:
                await self.client.set_command(self.device, 129, 0)
            elif hvac_mode == HVAC_MODE_DRY:
                await self.client.set_command(self.device, 129, 1)
            elif hvac_mode == HVAC_MODE_FAN_ONLY:
                await self.client.set_command(self.device, 129, 2)
            elif hvac_mode == HVAC_MODE_AUTO:
                await self.client.set_command(self.device, 129, 3)
            elif hvac_mode == HVAC_MODE_HEAT:
                await self.client.set_command(self.device, 129, 4)
            if not bool(self.status[0]):
                await self.client.set_command(self.device, 128, 1)
    @property
    def preset_mode(self) -> str:
        """ Return the current operation """
        if self.status[27]==0 and self.status[26]==0:
            return self.preset_modes[0]
        if self.status[27]==1 and self.status[26]==0:
            return self.preset_modes[1]
        if self.status[27]==0 and self.status[26]==1:
            return self.preset_modes[2]

    @property
    def preset_modes(self) -> list:
        _presetmodes=[]
        _presetmodes.append("一般模式")
        if (26 in self.commands):
            _presetmodes.append("快速模式")
        if (27 in self.commands):
            _presetmodes.append("節能模式")   
        return _presetmodes

    async def async_set_preset_mode(self, preset_mode) -> None:
        if preset_mode=="一般模式":
            if 26 in self.commands:
                await self.client.set_command(self.device, 26, 0)
            if 27 in self.commands:
                await self.client.set_command(self.device, 27, 0)
        elif preset_mode=="節能模式":
            await self.client.set_command(self.device, 27, 1)
        elif preset_mode=="快速模式":
            await self.client.set_command(self.device, 26, 1)

    @property
    def fan_mode(self) -> str:
        """ Return the fan setting """
        return self.commands[2]["Table"][self.status[2]]

    @property
    def fan_modes(self) -> list:
        """ Return the list of available fan modes """
        if (2 in self.commands):
            return list(self.commands[2]["Table"].values())

    async def async_set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        _LOGGER.debug(f"[{self.nickname}] Set fan mode to {fan_mode}")
        modeindex = [k for k, v in self.commands[2]["Table"].items() if v == fan_mode]
        await self.client.set_command(self.device, 130, modeindex[0])

    @property
    def swing_mode(self) -> str:
        """ Return the fan setting """
        if (17 in self.commands):
            return self.commands[17]["Table"][self.status[17]]
        elif (15 in self.commands):
            return self.commands[15]["Table"][self.status[15]]
        return ""

    @property
    def swing_modes(self) -> list:
        """ Return the list of available swing modes """
        if (17 in self.commands):
            return list(self.commands[17]["Table"].values())
        if (15 in self.commands):
            return list(self.commands[15]["Table"].values())

    async def async_set_swing_mode(self, swing_mode):
        
        if (17 in self.commands):
            modeindex = [k for k, v in self.commands[17]["Table"].items() if v == swing_mode]
            await self.client.set_command(self.device, 145, modeindex[0])
        elif (15 in self.commands):
            modeindex = [k for k, v in self.commands[15]["Table"].items() if v == swing_mode]
            await self.client.set_command(self.device, 143, modeindex[0])
        

    @property
    def target_temperature(self) -> int:
        """ Return the target temperature """
        if ( 3 in self.status):
            return int(self.status[3])
        else:
            _LOGGER.debug(f"------- UPDATING fail {self.nickname} {self.status}-------")
            return 0.0

    async def async_set_temperature(self, **kwargs):
        """ Set new target temperature """
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        await self.client.set_command(self.device, 131, int(target_temp))

    @property
    def current_temperature(self) -> int:
        """ Return the current temperature """
        if ( 4 in self.status):
            return int(self.status[4])
        else:
            _LOGGER.debug(f"------- UPDATING fail {self.nickname} {self.status}-------")
            return 0.0

    @property
    def current_humidity(self) -> int:
        """ Return the current humidity """
        if ( 20 in self.status):
            return int(self.status[20])
        else:
            _LOGGER.debug(f"------- UPDATING fail {self.nickname} {self.status}-------")
            return 0.0

    @property
    def min_temp(self) -> int:
        if ( 131 in self.commands):
            return self.commands[3]["MIN"]
        else:
            _LOGGER.debug(f"------- UPDATING fail {self.nickname} {self.commands}-------")
            return 0.0

    @property
    def max_temp(self) -> int:
        if ( 131 in self.commands):
            return self.commands[3]["MAX"]
        else:
            _LOGGER.debug(f"------- UPDATING fail {self.nickname} {self.commands}-------")
            return 0.0

    @property
    def target_temperature_step(self) -> int:
        """ Return temperature step """
        return 1
