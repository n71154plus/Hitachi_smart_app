""" Hitachi Smart App API """
from datetime import timedelta
from typing import Literal
import logging,hashlib,json,ssl,base64,re,asyncio

from homeassistant.const import HTTP_OK
from homeassistant.util import Throttle
from .exceptions import (
    HitachiRefreshTokenNotFound,
    HitachiTokenExpired,
    HitachiInvalidRefreshToken,
    HitachiLoginFailed,
)
from .const import (
    X_DK_API_Key,
    X_DK_Application_Id,
    Platform,
    Version,
    SECONDS_BETWEEN_REQUEST,
    HTTP_EXPECTATION_FAILED,
    EXCEPTION_INVALID_REFRESH_TOKEN,
)
from . import urls

_LOGGER = logging.getLogger(__name__)
REQUEST_THROTTLE = timedelta(seconds=SECONDS_BETWEEN_REQUEST)


def tryApiStatus(func):
    async def wrapper_call(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HitachiTokenExpired:
            await args[0].refresh_token()
            return await func(*args, **kwargs)
        except (HitachiInvalidRefreshToken, HitachiLoginFailed, Exception):
            await args[0].login()
            return await func(*args, **kwargs)

    return wrapper_call


class smarthome(object):
    def __init__(self, session, account, password):
        self.account = account
        self.password = password
        self._jobtaskid=1
        self._session = session
        self._devices = []
        self._commands = []
        self._refresh_token = ""
        self.header={}
        self.sslcontext = ssl.create_default_context(cafile='/config/custom_components/Hitachi_smart_app/smarthome/certificate.crt')

    @Throttle(REQUEST_THROTTLE)
    async def login(self):
        hash = hashlib.md5((self.account + self.password).encode("utf-8"))
        self.header = {
            "X-DK-API-Key": X_DK_API_Key,
            "X-DK-Application-Id": X_DK_Application_Id,
            "content-type": "application/json",
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
        }
        self.data = {
            "ServerLogin": {
                "Email": self.account,
                "HashCode": self.account
                + hashlib.md5(
                    (self.account + self.password).encode("utf-8")
                ).hexdigest(),
            },
            "AppVersion": {"Platform": Platform, "Version": Version},
        }

        response = await self.request(
            method="POST",
            headers=self.header,
            endpoint=urls.login(),
            data=self.data,
        )
        self.sessionToken = response["results"]["sessionToken"]
        self.header = {
            "X-DK-Session-Token": self.sessionToken,
            "X-DK-API-Key": X_DK_API_Key,
            "X-DK-Application-Id": X_DK_Application_Id,
            "content-type": "application/json",
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",}

    @Throttle(REQUEST_THROTTLE)
    async def refresh_token(self):
        _LOGGER.debug("Attemping to refresh token...")
        if self._refresh_token is None:
            raise HitachiRefreshTokenNotFound

        data = {"RefreshToken": self._refresh_token}
        response = await self.request(
            method="POST", headers={}, endpoint=urls.refresh_token(), data=data
        )
        self._refresh_token = response["RefreshToken"]
        self.sessionToken = response["results"]["sessionToken"]

    @tryApiStatus
    async def get_devices(self):
        response = await self.request(
            method="POST", headers=self.header,data="",endpoint=urls.get_devices()
        )
        for device in response['results']:
            ContDID={}
            ContDID[device['Peripherals'][0]['DataContainer'][0]['ContDetails'][0]['ContDType']]=device['Peripherals'][0]['DataContainer'][0]['ContDetails'][0]['ContDID']
            ContDID[device['Peripherals'][0]['DataContainer'][0]['ContDetails'][1]['ContDType']]=device['Peripherals'][0]['DataContainer'][0]['ContDetails'][1]['ContDID']
            ContMID =device['Peripherals'][0]['DataContainer'][0]['ContMID']
            CONTDATA1= {"Format": 0,"DataContainer": [{"ContMID": ContMID,"ContDetails": [{"ContDID": ContDID[1]}]}]}
            response = await self.request(
            method="POST", headers=self.header,data=CONTDATA1,endpoint=urls.get_device_info()
            )
            LValue1=base64.b64decode(response['results']['DataContainer'][0]['ContDetails'][0]['LValue'])
            info={}
            info['BLEData']=base64.b64decode(device['Peripherals'][0]['BLEPeripheralStatus'][0]['BLEDataPayload'])
            info['MACAddress']=(int(device['GMACAddress'])).to_bytes(length=8, byteorder='big')
            info['DeviceName']=device['DeviceName']
            info['DeviceID']={}
            info['DeviceID']['ContMID']=device['Peripherals'][0]['DataContainer'][0]['ContMID']
            info['DeviceID']['ContDID']={}
            info['DeviceID']['ContDID'][device['Peripherals'][0]['DataContainer'][0]['ContDetails'][0]['ContDType']]=device['Peripherals'][0]['DataContainer'][0]['ContDetails'][0]['ContDID']
            info['DeviceID']['ContDID'][device['Peripherals'][0]['DataContainer'][0]['ContDetails'][1]['ContDType']]=device['Peripherals'][0]['DataContainer'][0]['ContDetails'][1]['ContDID']
            info['ObjectID']=device['ObjectID']
            info['Lvalue']=LValue1
            obj=re.findall(b"\x00\x00\x04\x00\x03\x00(.{1})(\w+)\x00([^\x00]+)", LValue1)
            info['DeviceType']= int.from_bytes(obj[0][0],byteorder='big',signed=False)
            info['Manufacturer']=str(obj[0][1],'UTF-8')
            info['ModelName']=str(obj[0][2],'UTF-8')

            self._devices.append(info)
        return self._devices

    def get_commands(self):
        return self._commands

    @tryApiStatus
    async def get_device_info(
        self, deviceId
    ):
        CONTDATA= {"Format": 0,"DataContainer": [{"ContMID": deviceId['ContMID'],"ContDetails": [{"ContDID": deviceId['ContDID'][2]}]}]}
        response = await self.request(
        method="POST", headers=self.header,data=CONTDATA,endpoint=urls.get_device_info()
        )
        LValue1=base64.b64decode(response['results']['DataContainer'][0]['ContDetails'][0]['LValue'])
        return LValue1

    @tryApiStatus
    async def set_command(self, device, command=0, value=0):
        ObjectID=device['ObjectID']
        mac=device['MACAddress']
        type=device['DeviceType']
        btype=type.to_bytes(length=1, byteorder='big')
        bcommand=command.to_bytes(length=1, byteorder='big')
        bvalue=value.to_bytes(length=2, byteorder='big')
        checksum=(b'\x06'[0]^btype[0]^bcommand[0]^bvalue[0]^bvalue[1]).to_bytes(length=1, byteorder='big')
        code1=b'\x0d\x27\x80\x50\xf0\xd4\x46\x9d\xaf\xd3\x60\x5a\x6e\xbb\xdb\x13'
        code2=b'\x0d\x27\x80\x52\xf0\xd4\x46\x9d\xaf\xd3\x60\x5a\x6e\xbb\xdb\x13'
        bdata=bytearray(b'\xd0\xd1\x00\x00'+mac + b'\xff\xff\xff\xff\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x01\x00\x00'+mac+b'\x02\x00'+code1+code2+b'\x06\x00\x06'+btype+bcommand+bvalue+checksum )
        JobInformation=(base64.b64encode(bdata)).decode("UTF-8")
        self._jobtaskid=self._jobtaskid+1
        pushdata ={"Data":[{"GatewayID":ObjectID,"DeviceID":11231,"TaskID":self._jobtaskid,"JobInformation":JobInformation}]}
        Jobdone={"DeviceID":11231}
        response = await self.request(
            method="POST", headers=self.header, endpoint=urls.set_command(), data=pushdata
        )
        _LOGGER.debug(f" post data={pushdata}  response is {response}")
        re_try_times=0
        re_try_for_mqtt=0
        while True:
            re_try_times=re_try_times+1
            await asyncio.sleep(1)
            response = await self.request(
             method="POST", headers=self.header, endpoint=urls.JOB_done(), data=Jobdone
            )
            _LOGGER.debug(f" post data={Jobdone}  response is {response}")
            if len(response['results']) >0 :
                ReportedData=(((base64.b64decode(response['results'][0]['ReportedData']))[4:])[:-1]).hex(':')
                _LOGGER.debug(f" get data={ReportedData}")
                while True:
                    re_try_for_mqtt=re_try_for_mqtt+1
                    await asyncio.sleep(1)
                    ReportedDatanew = ((await self.get_device_info(device['DeviceID']))[:-1]).hex(':')
                    _LOGGER.debug(f" get data={ReportedDatanew}")
                    if ReportedData==ReportedDatanew :
                        break
                    if re_try_for_mqtt > 30:
                        break
                break
            if re_try_times >20:
                break
        return True

    async def request(
        self,
        method: Literal["GET", "POST"],
        headers,
        endpoint: str,
        params=None,
        data=None,
    ):
        """Shared request method"""

        resp = None

        async with self._session.request(
            method,
            url=endpoint,
            json=data,
            params=params,
            headers=headers,
            ssl=self.sslcontext,
        ) as response:
            if response.status == HTTP_OK:
                try:
                    resp = await response.json()
                except:
                    resp = {}
            elif response.status == HTTP_EXPECTATION_FAILED:
                returned_raw_data = await response.text()
                _LOGGER.error(
                    "Failed to access API. Returned" " %d: %s",
                    response.status,
                    returned_raw_data,
                )

            else:
                _LOGGER.error(
                    "Failed to access API. Returned" " %d: %s",
                    response.status,
                    await response.text(),
                )

        return resp
