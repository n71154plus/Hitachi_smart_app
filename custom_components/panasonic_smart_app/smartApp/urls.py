""" Panasonic Smart App API """
BASE_URL = "https://api.jci-hitachi-smarthome.com/3.6/"


def login():
    url = f"{BASE_URL}/UserLogin.php"
    return url


def getDevices():
    url = f"{BASE_URL}/GetPeripheralsByUser.php"
    return url


def getDeviceInfo():
    url = f"{BASE_URL}/GetDataContainerByID.php"
    return url


def setCommand():
    url = f"{BASE_URL}/CreateJob.php"
    return url
