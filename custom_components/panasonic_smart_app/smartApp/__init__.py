""" Panasonic Smart App API """
from homeassistant.core import Context
import logging, requests, json, hashlib
from pprint import pprint
from . import urls

# from .secrets import *
from . import _taiseia as taiSEIA

_LOGGER = logging.getLogger(__name__)

ServerApiKey = "23f26d38921dda92c1c2939e733bca5e"
ServerApplicationId = "ODM-HITACHI-APP-168d7d31bbd2b7cbbd"
Platform = 2
Version = "3.90.400"
email = "n71154plus@gmail.com"
password = "Kaewniaqn6375+"


class SmartApp(object):
    def __init__(self, account, password):
        self.host = "https://api.jci-hitachi-smarthome.com/3.6/"
        self.account = account
        self.password = password
        self.taiSEIA = taiSEIA
        self.HashCode = (
            account + hashlib.md5((account + password).encode("utf-8")).hexdigest()
        )

    def login(self):
        data = {
            "ServerLogin": {"Email": self.account, "HashCode": self.HashCode},
            "AppVersion": {"Platform": Platform, "Version": Version},
        }
        self.header = {
            "X-DK-API-Key": ServerApiKey,
            "X-DK-Application-Id": ServerApplicationId,
        }
        response = requests.post(
            urls.login(), json=data, headers=self.header, verify=False
        )
        response.raise_for_status()
        print(response.json()["results"]["sessionToken"])
        self.sessionToken = response.json()["results"]["sessionToken"]
        self.header = {
            "X-DK-API-Key": ServerApiKey,
            "X-DK-Application-Id": ServerApplicationId,
            "X-DK-Session-Token": self.sessionToken,
        }

    def getDevices(self):
        response = requests.post(
            urls.getDevices(), json="", headers=self.header, verify=False
        )
        response.raise_for_status()
        _LOGGER.debug(f"[getDevices {response.status_code}] - {response.json()}")
        self._devices = response.json()
        print(response.json())
        _LOGGER.debug(f"{response.json()}")
        return self._devices

    def getDeviceInfo(self, deviceId=None, options=["0x00", "0x01", "0x03", "0x04"]):
        self.header.update({"auth": deviceId})
        commands = {"CommandTypes": [], "DeviceID": 1}
        for option in options:
            commands["CommandTypes"].append({"CommandType": option})

        response = requests.post(
            urls.getDeviceInfo(), headers=self.header, json=[commands]
        )
        response.raise_for_status()
        result = {}
        if response.status_code == 200:
            for device in response.json().get("devices", []):
                for info in device.get("Info"):
                    command = info.get("CommandType")
                    status = info.get("status")
                    result[command] = status
        return result

    def setCommand(self, deviceId=None, command=0, value=0):
        self.header.update({"auth": deviceId})
        payload = {"DeviceID": 1, "CommandType": command, "Value": value}
        response = requests.get(urls.setCommand(), headers=self.header, params=payload)
        response.raise_for_status()
        # pprint(vars(response))
        return True
