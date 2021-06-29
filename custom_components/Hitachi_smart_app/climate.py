import logging,asyncio
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
    CLIMATE_AVAILABLE_MODE,
    CLIMATE_AVAILABLE_PRESET,
    CLIMATE_AVAILABLE_SWING_MODE,
    CLIMATE_AVAILABLE_FAN_MODE,
    CLIMATE_TEMPERATURE_STEP,
    LABEL_CLIMATE,
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
        if device["Lvalue"][7] == DEVICE_TYPE_AC:
            climate.append(
                HitachiClimate(
                    client,
                    device,
                )
            )

    async_add_entities(climate, True)

    return True


class HitachiClimate(HitachiBaseEntity, ClimateEntity):
    def __init__(self, client, device):
        super().__init__(client, device)

        self._min_temp=int(device['BLEData'][38])
        self._max_temp=int(device['BLEData'][39])
        self._target_temperature_high=float(int(device['BLEData'][34]))
        self._target_temperature_low=float(int(device['BLEData'][35]))
        self._unit = TEMP_CELSIUS
        self._target_temperature = None
        self._current_temperature = None

    async def async_update(self):
        _LOGGER.debug(f"------- UPDATING {self.nickname} {self.label}-------")
        """Update the state of this climate device."""
        self._status = await self.client.get_device_info(
            self.auth,
        )

        self._is_on = bool(int.from_bytes(self._status[4:6],byteorder='big'))

        self._target_temperature = float(int.from_bytes(self._status[13:15],byteorder='big',signed=True))

        self._current_temperature = float(int.from_bytes(self._status[16:18],byteorder='big',signed=True))

        self._current_humidity = float(int.from_bytes(self._status[34:36],byteorder='big',signed=True))

        self._mode = int.from_bytes(self._status[7:9],byteorder='big')

        self._fan_mode = int.from_bytes(self._status[10:12],byteorder='big')

        self._swing_mode = int.from_bytes(self._status[31:33],byteorder='big')
        self._energy_mode=int.from_bytes(self._status[43:45],byteorder='big')
        self._fast_mode=int.from_bytes(self._status[40:42],byteorder='big')

    @property
    def label(self):
        return LABEL_CLIMATE

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def hvac_mode(self) -> str:
        """Return the current operation."""
        if not self._is_on:
            return HVAC_MODE_OFF
        else:
            if self._mode ==0:
                return HVAC_MODE_COOL
            elif self._mode ==1 :
                return HVAC_MODE_DRY
            elif self._mode ==2 :
                return HVAC_MODE_FAN_ONLY
            elif self._mode ==3 :
                return HVAC_MODE_AUTO
            elif self._mode ==4 :
                return HVAC_MODE_HEAT
            else:
                return HVAC_MODE_OFF
            
                


    @property
    def hvac_modes(self) -> list:
        return[HVAC_MODE_OFF,HVAC_MODE_HEAT,HVAC_MODE_COOL,HVAC_MODE_AUTO,HVAC_MODE_DRY,HVAC_MODE_FAN_ONLY]

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
            if not self._is_on:
                await self.client.set_command(self.device, 128, 1)
    @property
    def preset_mode(self) -> str:
        """ Return the current operation """
        if self._energy_mode==0 and self._fast_mode==0:
            return CLIMATE_AVAILABLE_PRESET[0]
        if self._energy_mode==1 and self._fast_mode==0:
            return CLIMATE_AVAILABLE_PRESET[1]
        if self._energy_mode==0 and self._fast_mode==1:
            return CLIMATE_AVAILABLE_PRESET[2]

    @property
    def preset_modes(self) -> list:
        return list(CLIMATE_AVAILABLE_PRESET.values())

    async def async_set_preset_mode(self, preset_mode) -> None:
        _LOGGER.debug(f"[{self.nickname}] set_preset_mode: {preset_mode}")
        value = int(getKeyFromDict(CLIMATE_AVAILABLE_PRESET, preset_mode))
        if value==0:
            await self.client.set_command(self.device, 154, 0)
            await self.client.set_command(self.device, 155, 0)
        elif value==1:
            await self.client.set_command(self.device, 154, 0)
            await self.client.set_command(self.device, 155, 1)
        elif value==2:
            await self.client.set_command(self.device, 155, 0)
            await self.client.set_command(self.device, 154, 1)

    @property
    def fan_mode(self) -> str:
        """ Return the fan setting """
        return CLIMATE_AVAILABLE_FAN_MODE[self._fan_mode]

    @property
    def fan_modes(self) -> list:
        """ Return the list of available fan modes """
        return list(CLIMATE_AVAILABLE_FAN_MODE.values())

    async def async_set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        _LOGGER.debug(f"[{self.nickname}] Set fan mode to {fan_mode}")
        mode_id = int(getKeyFromDict(CLIMATE_AVAILABLE_FAN_MODE, fan_mode))
        await self.client.set_command(self.device, 130, mode_id)

    @property
    def swing_mode(self) -> str:
        """ Return the fan setting """
        return CLIMATE_AVAILABLE_SWING_MODE[self._swing_mode]

    @property
    def swing_modes(self) -> list:
        """ Return the list of available swing modes """
        return list(CLIMATE_AVAILABLE_SWING_MODE.values())

    async def async_set_swing_mode(self, swing_mode):
        _LOGGER.debug(f"[{self.nickname}] Set swing mode to {swing_mode}")
        mode_id = int(getKeyFromDict(CLIMATE_AVAILABLE_SWING_MODE, swing_mode))
        await self.client.set_command(self.device, 154, mode_id)

    @property
    def target_temperature(self) -> int:
        """ Return the target temperature """
        return self._target_temperature

    async def async_set_temperature(self, **kwargs):
        """ Set new target temperature """
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        _LOGGER.debug(f"[{self.nickname}] Set temperature to {target_temp}")
        await self.client.set_command(self.device, 131, int(target_temp))

    @property
    def current_temperature(self) -> int:
        """ Return the current temperature """
        return self._current_temperature

    @property
    def current_humidity(self) -> int:
        """ Return the current humidity """
        return self._current_humidity

    @property
    def min_temp(self) -> int:
        """ Return the minimum temperature """
        return self._min_temp

    @property
    def max_temp(self) -> int:

        return self._max_temp

    @property
    def target_temperature_low(self) -> float:
        """ Return the minimum temperature """
        return self._target_temperature_low

    @property
    def target_temperature_high(self) -> float:

        return self._target_temperature_high

    @property
    def target_temperature_step(self) -> float:
        """ Return temperature step """
        return CLIMATE_TEMPERATURE_STEP
