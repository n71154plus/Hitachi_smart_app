"""Contants for Hitachi Smart App integration"""

DOMAIN = "Hitachi_smart_app"
#PLATFORMS = ["humidifier", "sensor", "number", "climate","fan"]
PLATFORMS = ["humidifier","sensor","number","fan","climate","switch"]
MANUFACTURER = "Hitachi"
DEFAULT_NAME = "Hitachi Smart Application"

DEVICE_TYPE_AC = 0x01
DEVICE_TYPE_DEHUMIDIFIER = 0x04

DATA_CLIENT = "client"
DATA_COORDINATOR = "coordinator"

UPDATE_INTERVAL = 60


