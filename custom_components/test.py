import ssl
import urllib.request
import base64
import json
import hashlib
import binascii


urllogin="https://api.jci-hitachi-smarthome.com/3.6/UserLogin.php"
urlgetperipheral="https://api.jci-hitachi-smarthome.com/3.6/GetPeripheralsByUser.php"
urlgetdatacontainer="https://api.jci-hitachi-smarthome.com/3.6/GetDataContainerByID.php"
ServerApiKey="23f26d38921dda92c1c2939e733bca5e"
ServerApplicationId="ODM-HITACHI-APP-168d7d31bbd2b7cbbd"
Platform=2
Version="3.90.400"
email="n71154plus@gmail.com"
password="Kaewniaqn6375+"
HashCode = email+hashlib.md5((email+password).encode("utf8")).hexdigest()

Login_data= {
	"ServerLogin": {
		"Email": email,
		"HashCode": HashCode
	},
	"AppVersion": {
		"Platform": Platform,
		"Version": Version
	}
}
header1 = {'X-DK-API-Key': ServerApiKey}
header2 = {'X-DK-Application-Id':ServerApplicationId}
#ssl._create_default_https_context = ssl._create_unverified_context
gcontext = ssl.SSLContext()
req = urllib.request.Request(urllogin)
req.add_header('X-DK-API-Key', ServerApiKey)
req.add_header('X-DK-Application-Id',ServerApplicationId)
r=urllib.request.urlopen(req,data=json.dumps(Login_data).encode('utf8'),context=gcontext)
logindata=json.loads(r.read())
sessionToken=logindata['results']['sessionToken']
print(sessionToken)
req = urllib.request.Request(urlgetperipheral)
req.add_header('X-DK-Session-Token', sessionToken)
req.add_header('X-DK-API-Key', ServerApiKey)
req.add_header('X-DK-Application-Id',ServerApplicationId)
r=urllib.request.urlopen(req,data="".encode('utf8'),context=gcontext)
alldevicedata=json.loads(r.read())
deviceBLEdata=alldevicedata['results'][0]['Peripherals'][0]['BLEPeripheralStatus'][0]['BLEDataPayload']
a=base64.b64decode(deviceBLEdata)
str1=''.join(hex(x).replace("0x",",") for x in a)
ContMID=alldevicedata['results'][1]['Peripherals'][0]['DataContainer'][0]['ContMID']
ContDID1=alldevicedata['results'][1]['Peripherals'][0]['DataContainer'][0]['ContDetails'][0]['ContDID']
ContDID2=alldevicedata['results'][1]['Peripherals'][0]['DataContainer'][0]['ContDetails'][1]['ContDID']
CONTDATA1= {
	"Format": 0,
	"DataContainer": [{
		"ContMID": ContMID,
		"ContDetails": [{
			"ContDID": ContDID1
		}]
	}]
}
req = urllib.request.Request(urlgetdatacontainer)
req.add_header('X-DK-Session-Token', sessionToken)
req.add_header('X-DK-API-Key', ServerApiKey)
req.add_header('X-DK-Application-Id',ServerApplicationId)
r=urllib.request.urlopen(req,data=json.dumps(CONTDATA1).encode('utf8'),context=gcontext)
alldevicedata=json.loads(r.read())
LValue1=alldevicedata['results']['DataContainer'][0]['ContDetails'][0]['LValue']
b=base64.b64decode(LValue1)
str3=''.join(hex(x).replace("0x"," ") for x in b)
print(str3)
CONTDATA2= {
	"Format": 0,
	"DataContainer": [{
		"ContMID": ContMID,
		"ContDetails": [{
			"ContDID": ContDID2
		}]
	}]
}
req = urllib.request.Request(urlgetdatacontainer)
req.add_header('X-DK-Session-Token', sessionToken)
req.add_header('X-DK-API-Key', ServerApiKey)
req.add_header('X-DK-Application-Id',ServerApplicationId)
r=urllib.request.urlopen(req,data=json.dumps(CONTDATA2).encode('utf8'),context=gcontext)
alldevicedata=json.loads(r.read())
LValue2=alldevicedata['results']['DataContainer'][0]['ContDetails'][0]['LValue']
b=base64.b64decode(LValue2)
str4=''.join(hex(x).replace("0x"," ") for x in b)


print(str4)
