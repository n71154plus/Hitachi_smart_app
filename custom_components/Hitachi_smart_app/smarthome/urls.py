""" Hitachi Smart App API """

from .const import BASE_URL


def login():
    url = f"{BASE_URL}/UserLogin.php"
    return url


def get_devices():
    url = f"{BASE_URL}/GetPeripheralsByUser.php"
    return url


def get_device_info():
    url = f"{BASE_URL}/GetDataContainerByID.php"
    return url


def set_command():
    url = f"{BASE_URL}/CreateJob.php"
    return url


def refresh_token():
    url = f"{BASE_URL}/RefreshToken1"
    return url

def JOB_done():
    url = f"{BASE_URL}/GetJobDoneReport.php"
    return url
