import logging
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
    LABEL_DEHUMIDIFIER,
    DEHUMIDIFIER_MIN_HUMD,
    DEHUMIDIFIER_MAX_HUMD,
    DEHUMIDIFIER_AVAILABLE_HUMIDITY,
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
    humidifiers = []

    for device in devices:
        if device["Lvalue"][7] == DEVICE_TYPE_DEHUMIDIFIER:
            humidifiers.append(
                HitachiDehumidifier(
                    client,
                    device,
                )
            )

    async_add_entities(humidifiers, True)

    return True


class HitachiDehumidifier(HitachiBaseEntity, HumidifierEntity):
    def __init__(self, client, device):

        super().__init__(client, device)

        self._is_on_status = False
        self._mode = ""
        self._current_humd = 0
        self._target_humd = 0

    async def async_update(self):
        _LOGGER.debug(f"------- UPDATING {self.nickname} {self.label} -------")
        try:
            self._status = await self.client.get_device_info(
                self.auth,
            )

        except:
            _LOGGER.error(f"[{self.nickname}] Error occured while updating status")
        else:
            _LOGGER.debug(f"[{self.nickname}] status: {self._status}")
            # _is_on
            self._is_on_status = bool(int.from_bytes(self._status[4:6],byteorder='big'))
            _LOGGER.debug(f"[{self.nickname}] _is_on: {self._is_on_status}")

            self._mode = int.from_bytes(self._status[7:9],byteorder='big')

            # _target_humd
            self._target_humd = int.from_bytes(self._status[13:15],byteorder='big',signed=True)
            _LOGGER.debug(f"[{self.nickname}] _target_humd: {self._target_humd}")

            _LOGGER.debug(f"[{self.nickname}] update completed.")

    @property
    def label(self):
        return LABEL_DEHUMIDIFIER

    @property
    def target_humidity(self):
        return self._target_humd

    @property
    def max_humidity(self):
        return DEHUMIDIFIER_MAX_HUMD

    @property
    def min_humidity(self):
        return DEHUMIDIFIER_MIN_HUMD

    @property
    def mode(self):
        mode_list=["未知","自訂濕度","未知2","快速乾衣","空氣清淨","防霉防螨","未知3","未知4","低濕乾燥","舒適節電"]
        return mode_list[self._mode]

    @property
    def available_modes(self):
        mode_list=["未知","自訂濕度","未知2","快速乾衣","空氣清淨","防霉防螨","未知3","未知4","低濕乾燥","舒適節電"]
        return mode_list

    @property
    def supported_features(self):
        return SUPPORT_MODES

    @property
    def is_on(self):
        return self._is_on_status

    @property
    def device_class(self):
        return DEVICE_CLASS_DEHUMIDIFIER

    async def async_set_mode(self, mode):
        """ Set operation mode """
        mode_list=["未知","自訂濕度","未知2","快速乾衣","空氣清淨","防霉防螨","未知3","未知4","低濕乾燥","舒適節電"]
        await self.client.set_command(self.device, 129, mode_list.index(mode))

    async def async_set_humidity(self, humidity):
        """ Set target humidity """
        await self.client.set_command(self.device, 131, humidity)
        

    async def async_turn_on(self):
        """ Turn on dehumidifier """
        _LOGGER.debug(f"[{self.nickname}] Turning on")
        await self.client.set_command(self.device, 128, 1)
        humidity

    async def async_turn_off(self):
        """ Turn off dehumidifier """
        _LOGGER.debug(f"[{self.nickname}] Turning off")
        await self.client.set_command(self.device, 128, 0)