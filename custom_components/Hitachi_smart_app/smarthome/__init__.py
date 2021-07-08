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
        self._jobtaskid=2
        self._session = session
        self._devices = []
        self._refresh_token = ""
        self.header={}
        self.sslcontext = ssl.create_default_context(cafile="/config/custom_components/Hitachi_smart_app/smarthome/certificate.crt")

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
        for device in response["results"]:
            ContDID={}
            ContDID[device["Peripherals"][0]["DataContainer"][0]["ContDetails"][0]["ContDType"]]=device["Peripherals"][0]["DataContainer"][0]["ContDetails"][0]["ContDID"]
            ContDID[device["Peripherals"][0]["DataContainer"][0]["ContDetails"][1]["ContDType"]]=device["Peripherals"][0]["DataContainer"][0]["ContDetails"][1]["ContDID"]
            ContMID =device["Peripherals"][0]["DataContainer"][0]["ContMID"]
            CONTDATA1= {"Format": 0,"DataContainer": [{"ContMID": ContMID,"ContDetails": [{"ContDID": ContDID[1]}]}]}
            response = await self.request(
            method="POST", headers=self.header,data=CONTDATA1,endpoint=urls.get_device_info()
            )
            LValue1=base64.b64decode(response["results"]["DataContainer"][0]["ContDetails"][0]["LValue"])
            info={}
            info["BLEData"]=base64.b64decode(device["Peripherals"][0]["BLEPeripheralStatus"][0]["BLEDataPayload"])
            info["MACAddress"]=(int(device["GMACAddress"])).to_bytes(length=8, byteorder="big")
            info["DeviceName"]=device["DeviceName"]
            info["DeviceID"]={}
            info["DeviceID"]["ContMID"]=device["Peripherals"][0]["DataContainer"][0]["ContMID"]
            info["DeviceID"]["ContDID"]={}
            info["DeviceID"]["ContDID"][device["Peripherals"][0]["DataContainer"][0]["ContDetails"][0]["ContDType"]]=device["Peripherals"][0]["DataContainer"][0]["ContDetails"][0]["ContDID"]
            info["DeviceID"]["ContDID"][device["Peripherals"][0]["DataContainer"][0]["ContDetails"][1]["ContDType"]]=device["Peripherals"][0]["DataContainer"][0]["ContDetails"][1]["ContDID"]
            info["ObjectID"]=device["ObjectID"]
            info["Lvalue"]=LValue1
            obj=re.findall(b".{7}(.{1})([^\x00]+)\x00([^\x00]+)\x00(.*)", LValue1,re.DOTALL)
            info["DeviceType"]= int.from_bytes(obj[0][0],byteorder="big",signed=False)
            info["Manufacturer"]=str(obj[0][1],"UTF-8")
            info["ModelName"]=str(obj[0][2],"UTF-8")
            d_commands=re.findall(b"(.{1})(.{2})",obj[0][3],re.DOTALL)
            commands={}
            for s in d_commands:
                feature={}
                cmd=int.from_bytes(s[0],byteorder="big",signed=False)
                
                if cmd < 128:
                    feature["Readonly"]=True
                else:
                    feature["Readonly"]=False
                cmdd=cmd & 0x7F
                feature["UNIT"]=""
                if info["DeviceType"]==0x01:
                    if cmdd==0:
                        """Power Control"""
                        feature["Name"]="開關"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:power"
                    elif cmdd==1:
                        """Mode Control"""
                        feature["Name"]="模式切換"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="冷氣"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="除濕"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="送風"
                        if (s[1][1] & 0x08)==0x08:
                            dictp[3]="自動"
                        if (s[1][1] & 0x10)==0x10:
                            dictp[4]="暖氣"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:ab-testing"
                    elif cmdd==2:
                        """Wind Spped Control"""
                        feature["Name"]="風速控制"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="自動"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="Level1"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="Level2"
                        if (s[1][1] & 0x08)==0x08:
                            dictp[3]="Level3"
                        if (s[1][1] & 0x10)==0x10:
                            dictp[4]="Level4"
                        if (s[1][1] & 0x20)==0x20:
                            dictp[5]="Level5"
                        if (s[1][1] & 0x40)==0x40:
                            dictp[6]="Level6"
                        if (s[1][1] & 0x80)==0x80:
                            dictp[7]="Level7"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:fan"
                    elif cmdd==3:
                        """Temperature Setting"""
                        feature["Name"]="溫度設定"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=s[1][0]
                        feature["MAX"]=s[1][1]
                        feature["UNIT"]="°C"
                        feature["ICON"]="mdi:thermometer"
                    elif cmdd==4:
                        """INDOOR Temperature"""
                        feature["Name"]="室內溫度"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=s[1][0]
                        feature["MAX"]=s[1][1]
                        feature["UNIT"]="°C"
                        feature["ICON"]="mdi:thermometer"
                    elif cmdd==6:
                        """SLEEP MODE TIMER SETTING"""
                        feature["Name"]="舒眠定時"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=0
                        feature["MAX"]=int.from_bytes(s[1],byteorder="big",signed=True)
                        feature["UNIT"]="minutes"
                        feature["ICON"]="mdi:timer-sand"
                    elif cmdd==11:
                        """BOOT TIMER SETTING"""
                        feature["Name"]="開機定時"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=0
                        feature["MAX"]=int.from_bytes(s[1],byteorder="big",signed=True)
                        feature["UNIT"]="minutes"
                        feature["ICON"]="mdi:timer-sand"
                    elif cmdd==12:
                        """SHUTDOWN TIMER SETTINGG"""
                        feature["Name"]="關機定時"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=0
                        feature["MAX"]=int.from_bytes(s[1],byteorder="big",signed=True)
                        feature["UNIT"]="minutes"
                        feature["ICON"]="mdi:timer-sand"
                    elif cmdd==14:
                        """VERTICAL WIND SWINGABLE CONTROL"""
                        feature["Name"]="風向自動垂直擺動"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:tailwind"
                    elif cmdd==15:
                        """VERTICAL WIND DIRECTION LEVEL_CONTROL"""
                        feature["Name"]="風向垂直擺動方向控制"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="自動"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="Level1"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="Level2"
                        if (s[1][1] & 0x08)==0x08:
                            dictp[3]="Level3"
                        if (s[1][1] & 0x10)==0x10:
                            dictp[4]="Level4"
                        if (s[1][1] & 0x20)==0x20:
                            dictp[5]="Level5"
                        if (s[1][1] & 0x40)==0x40:
                            dictp[6]="Level6"
                        if (s[1][1] & 0x80)==0x80:
                            dictp[7]="Level7"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:tailwind"
                    elif cmdd==17:
                        """HORIZONTAL WIND DIRECTION CONTROL"""
                        feature["Name"]="風向水平擺動方向控制"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="自動"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="最左"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="中間偏左"
                        if (s[1][1] & 0x08)==0x08:
                            dictp[3]="中間"
                        if (s[1][1] & 0x10)==0x10:
                            dictp[4]="中間偏右"
                        if (s[1][1] & 0x20)==0x20:
                            dictp[5]="最右"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:tailwind"
                    elif cmdd==18:
                        """CLEAN FILTER NOTIFY CONTROL"""
                        feature["Name"]="清除濾網提醒"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:air-filter"
                    elif cmdd==20:
                        """INDOOR HUMIDITY"""
                        feature["Name"]="室內濕度"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=s[1][0]
                        feature["MAX"]=s[1][1]
                        feature["UNIT"]="%"
                        feature["ICON"]="mdi:water-percent"

                    elif cmdd==23:
                        """MOLD PREVENT SETTING"""
                        feature["Name"]="機體防霉"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:cog"
                    elif cmdd==26:
                        """FAST OPERATION SETTING"""
                        feature["Name"]="快速運轉"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:fast-forward"
                    elif cmdd==27:
                        """ENERGY SAVING SETTING"""
                        feature["Name"]="節電"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:ev-station"
                    elif cmdd==30:
                        """SAA VOICE CONTROL"""
                        feature["Name"]="通訊提示音"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:account-voice"
                    elif cmdd==31:
                        """HOST DISPLAY BRIGHTNESS SETTING"""
                        feature["Name"]="機體顯示"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="亮"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="暗"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="關"
                        if (s[1][1] & 0x08)==0x08:
                            dictp[3]="全關"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:lightbulb"
                    elif cmdd==32:
                        """HUMIDIFIER SETTING"""
                        feature["Name"]="保濕功能"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="無"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="低"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="高"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:water-percent"
                    elif cmdd==33:
                        """OUTDOOR TEMPERATURE"""
                        feature["Name"]="室外溫度"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=s[1][0]
                        feature["MAX"]=s[1][1]
                        feature["UNIT"]="°C"
                        feature["ICON"]="mdi:thermometer"
                    elif cmdd==36:
                        """OUTDOOR HOST CURRENT"""
                        feature["Name"]="室外機電流(A)"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=s[1][0]
                        feature["MAX"]=s[1][1]
                        feature["UNIT"]="A"
                        feature["ICON"]="mdi:gauge"
                    elif cmdd==40:
                        """OUTDOOR HOST ACCUMULATION KWH"""
                        feature["Name"]="累積消耗功率(KWH)"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=0
                        feature["MAX"]=int.from_bytes(s[1],byteorder="big",signed=True)
                        feature["UNIT"]="KWH"
                        feature["ICON"]="mdi:gauge"
                    elif cmdd==47:
                        """HOURS USED AFTER MAINTAINCE"""
                        feature["Name"]="累積使用時間(時)"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=0
                        feature["MAX"]=int.from_bytes(s[1],byteorder="big",signed=True)
                        feature["UNIT"]="hours"
                        feature["ICON"]="mdi:timer"
                    elif cmdd==48:
                        """HOURS USED AFTER CLEAN_FILTER"""
                        feature["Name"]="濾網清洗時數設定(時)"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=0
                        feature["MAX"]=int.from_bytes(s[1],byteorder="big",signed=True)
                        feature["UNIT"]="hours"
                        feature["ICON"]="mdi:air-filter"
                    elif cmdd==57:
                        """ FREEZE CLEAN CONTROL"""
                        feature["Name"]="凍結洗淨開關"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:snowflake-alert"
                    elif cmdd==58:
                        """ FREEZE CLEAN NOTIFICATION"""
                        feature["Name"]="凍結洗淨通知"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:snowflake-alert"
                    elif cmdd==59:
                        """FREEZE CLEAN CLEANING STATE"""
                        feature["Name"]="凍結洗淨狀態"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="Normal"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="Phase1"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="Phase2"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:snowflake-alert"
                elif info["DeviceType"]==0x04:
                    if cmdd==0:
                        """Power Control"""
                        feature["Name"]="開關"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:power"
                    elif cmdd==1:
                        """Mode Control"""
                        feature["Name"]="模式切換"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="自動模式"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="自訂濕度"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="連續除濕"
                        if (s[1][1] & 0x08)==0x08:
                            dictp[3]="快速乾衣"
                        if (s[1][1] & 0x10)==0x10:
                            dictp[4]="空氣清淨"
                        if (s[1][1] & 0x20)==0x20:
                            dictp[5]="防霉防螨"
                        if (s[1][1] & 0x40)==0x40:
                            dictp[6]="送風模式"
                        if (s[1][1] & 0x80)==0x80:
                            dictp[7]="舒適模式"
                        if (s[1][0] & 0x01)==0x01:
                            dictp[8]="低濕乾燥"
                        if (s[1][0] & 0x01)==0x01:
                            dictp[9]="舒適節電"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:ab-testing"
                    elif cmdd==2:
                        """OPERATION TIME SETTING"""
                        feature["Name"]="關機定時(時)"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=s[1][0]
                        feature["MAX"]=s[1][1]
                        feature["UNIT"]="hours"
                        feature["ICON"]="mdi:timer-sand"
                    elif cmdd==3:
                        """RELATIVE_HUMIDITY_SETTING"""
                        feature["Name"]="設定濕度"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=s[1][0]
                        feature["MAX"]=s[1][1]
                        feature["UNIT"]="%"
                        feature["ICON"]="mdi:water-percent"
                    elif cmdd==7:
                        """ INDOOR_HUMIDITY"""
                        feature["Name"]="室內濕度"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=s[1][0]
                        feature["MAX"]=s[1][1]
                        feature["UNIT"]="%"
                        feature["ICON"]="mdi:water-percent"
                    elif cmdd==8:
                        """WIND_SWINGABLE_CONTROL"""
                        feature["Name"]="風向擺動"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:tailwind"
                    elif cmdd==10:
                        """WATER_FULL_WARNING"""
                        feature["Name"]="水箱已滿"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:cup-water"
                    elif cmdd==11:
                        """CLEAN_FILTER_NOTIFY_CONTROL"""
                        feature["Name"]="清除濾網提醒"
                        feature["CMDtype"]=0x00      
                        feature["ICON"]="mdi:air-filter"                  
                    elif cmdd==13:
                        """AIR_PURIFY_LEVEL_CONTROL"""
                        feature["Name"]="負離子"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:dots-hexagon"
                    elif cmdd==14:
                        """WIND_SPEED_CONTROL"""
                        feature["Name"]="風速控制"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="自動"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="靜音"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="微風"
                        if (s[1][1] & 0x08)==0x08:
                            dictp[3]="弱風"
                        if (s[1][1] & 0x10)==0x10:
                            dictp[4]="強風"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:fan"
                    elif cmdd==15:
                        """SIDE_VENT"""
                        feature["Name"]="側吹"
                        feature["CMDtype"]=0x00  
                        feature["ICON"]="mdi:tailwind"
                        feature["UNIT"]=""
                    elif cmdd==16:
                        """SOUND_CONTROL"""
                        feature["Name"]="提示音設定"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="靜音"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="按鍵音"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="按鍵音&滿水通知"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:account-voice"
                    elif cmdd==17:
                        """DEFROST"""
                        feature["Name"]="除霜"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:snowflake-alert"
                        feature["UNIT"]=""
                    elif cmdd==19:
                        """MOLD_PREVENT_CONTROL"""
                        feature["Name"]="機體防霉"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:cog"
                    elif cmdd==24:
                        """SAA_VOICE_CONTROL"""
                        feature["Name"]="通訊提示音"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:account-voice"
                    elif cmdd==29:
                        """CUMULATIVE_POWER_SETTING"""
                        feature["Name"]="累積消耗功率(KWH)"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=0
                        feature["MAX"]=int.from_bytes(s[1],byteorder="big",signed=True)
                        feature["UNIT"]="KWH"
                        feature["ICON"]="mdi:gauge"
                    elif cmdd==35:
                        """AIR_QUALITY_VALUE"""
                        feature["Name"]="空氣品質數值"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=s[1][0]
                        feature["MAX"]=s[1][1]
                        feature["ICON"]="mdi:dots-hexagon"
                    elif cmdd==36:
                        """AIR_QUALITY_LEVEL"""
                        feature["Name"]="空氣品質(顏色)"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="OFF"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="GREEN"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="YELLOW"
                        if (s[1][1] & 0x08)==0x08:
                            dictp[3]="ORANGE"
                        if (s[1][1] & 0x10)==0x10:
                            dictp[4]="RED"
                        if (s[1][1] & 0x20)==0x20:
                            dictp[5]="PURPLE"
                        if (s[1][1] & 0x40)==0x40:
                            dictp[6]="MAROON"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:dots-hexagon"     
                    elif cmdd==37:
                        """PM25_VALUE"""
                        feature["Name"]="PM25"
                        feature["CMDtype"]=0x02
                        feature["MIN"]=s[1][0]
                        feature["MAX"]=s[1][1]
                        feature["ICON"]="mdi:dots-hexagon"
                    elif cmdd==38:
                        """PM25_DETECT_ON_STANDBY_CONTROL"""
                        feature["Name"]="待機偵測PM25數據"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:dots-hexagon"

                    elif cmdd==39:
                        """DISPLAY_BRIGHTNESS_CONTROL"""
                        feature["Name"]="機體顯示"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="亮"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="暗"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="關"
                        if (s[1][1] & 0x08)==0x08:
                            dictp[3]="全關"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:lightbulb"
                    elif cmdd==40:
                        """ODOR_DETECT_LEVEL"""
                        feature["Name"]="異味感測"
                        feature["CMDtype"]=0x01
                        dictp={}
                        if (s[1][1] & 0x01)==0x01:
                            dictp[0]="LOW"
                        if (s[1][1] & 0x02)==0x02:
                            dictp[1]="MIDDLE"
                        if (s[1][1] & 0x04)==0x04:
                            dictp[2]="HIGH"
                        feature["Table"]=dictp
                        feature["ICON"]="mdi:dots-hexagon"
                    elif cmdd==41:
                        """FILTER_SETTING"""
                        feature["Name"]="濾網重置"
                        feature["CMDtype"]=0x00
                        feature["ICON"]="mdi:air-filter"
                if "Name" in feature:
                    commands[cmdd]=feature
            info["Command"]=commands
            self._devices.append(info)
        return self._devices

    @tryApiStatus
    async def get_device_info(
        self, deviceId
    ):
        CONTDATA= {"Format": 0,"DataContainer": [{"ContMID": deviceId["ContMID"],"ContDetails": [{"ContDID": deviceId["ContDID"][2]}]}]}
        response = await self.request(
        method="POST", headers=self.header,data=CONTDATA,endpoint=urls.get_device_info()
        )
        LValue1=base64.b64decode(response["results"]["DataContainer"][0]["ContDetails"][0]["LValue"])
        return LValue1

    @tryApiStatus
    async def set_command(self, device, command=0, value=0):
        ObjectID=device["ObjectID"]
        mac=device["MACAddress"]
        type=device["DeviceType"]
        btype=type.to_bytes(length=1, byteorder="big")
        bcommand=command.to_bytes(length=1, byteorder="big")
        bvalue=value.to_bytes(length=2, byteorder="big")
        checksum=(b"\x06"[0]^btype[0]^bcommand[0]^bvalue[0]^bvalue[1]).to_bytes(length=1, byteorder="big")
        code1=b"\x0d\x27\x80\x50\xf0\xd4\x46\x9d\xaf\xd3\x60\x5a\x6e\xbb\xdb\x13"
        code2=b"\x0d\x27\x80\x52\xf0\xd4\x46\x9d\xaf\xd3\x60\x5a\x6e\xbb\xdb\x13"
        bdata=bytearray(b"\xd0\xd1\x00\x00"+mac + b"\xff\xff\xff\xff\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x01\x00\x00"+mac+b"\x02\x00"+code1+code2+b"\x06\x00\x06"+btype+bcommand+bvalue+checksum )
        JobInformation=(base64.b64encode(bdata)).decode("UTF-8")
        self._jobtaskid=self._jobtaskid+1
        pushdata ={"Data":[{"GatewayID":ObjectID,"DeviceID":11231,"TaskID":self._jobtaskid,"JobInformation":JobInformation}]}
        Jobdone={"DeviceID":11231}
        response = await self.request(
            method="POST", headers=self.header, endpoint=urls.set_command(), data=pushdata
        )
        re_try_times=0
        re_try_for_mqtt=0
        while True:
            re_try_times=re_try_times+1
            await asyncio.sleep(1)
            response = await self.request(
             method="POST", headers=self.header, endpoint=urls.JOB_done(), data=Jobdone
            )
            if len(response["results"]) >0 :
                ReportedData=(((base64.b64decode(response["results"][0]["ReportedData"]))[4:])[:-1]).hex(":")
                while True:
                    re_try_for_mqtt=re_try_for_mqtt+1
                    await asyncio.sleep(1)
                    ReportedDatanew = ((await self.get_device_info(device["DeviceID"]))[:-1]).hex(":")
                    if ReportedData==ReportedDatanew :
                        break
                    if re_try_for_mqtt > 5:
                        break
                break
            if re_try_times >5:
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
            ssl=False,
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
