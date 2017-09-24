import string
import random
import json
import uuid
from os import path, mkdir
from sys import modules

from Components.About import about
from Components.NimManager import nimmanager

try:
	from boxbranding import getMachineName, getDriverDate, getBoxType, getMachineBrand, getImageDistro
	brandingmodule = True
except:
	brandingmodule = False
	try:
		from enigma import getBoxType, getEnigmaVersionString
	except:
		def getBoxType():
			return 'STB'

		def getEnigmaVersionString():
			return '000000'

from getLineup import getlineup
from . import tunertypes, tunerports, tunerfolders, getIP

charset = {
	"auth": string.ascii_letters + string.digits,
	"id": string.ascii_uppercase + string.digits,
}

def generator(size, chars=charset['id']):
	return ''.join(random.choice(chars) for _ in range(size))

class getDeviceInfo:
	def __init__(self):
		pass

	def discoverJSON(self, dvb_type):
		ip = getIP()
		ip_port = 'http://%s:%s' % (ip, tunerports[dvb_type])
		device_uuid = str(uuid.uuid4())
		if path.exists('/etc/enigma2/%s.discover' % dvb_type):
		 	if path.exists('/www/%s/device.xml' % tunerfolders[dvb_type]):
				with open('/etc/enigma2/%s.discover' % dvb_type) as data_file:
					discover = json.load(data_file)
			else:
				with open('/etc/enigma2/%s.discover' % dvb_type) as data_file:
					discover = json.load(data_file)
					discover['DeviceUUID']='%s' % device_uuid
			discover.pop('NumChannels', None)
		else:
			discover = {}
			deviceauth = generator(24, charset['auth'])
			deviceid = generator(8, charset['id'])
			if brandingmodule:
				discover['FriendlyName']='%s %s' % (getMachineBrand(), getMachineName())
				discover['ModelNumber']='%s' % getBoxType()
				discover['FirmwareName']='%s' % getImageDistro()
				discover['FirmwareVersion']='%s' % getDriverDate()
			else:
				discover['FriendlyName']='%s' % _('Enigma2 STB')
				discover['ModelNumber']='%s' % getBoxType()
				discover['FirmwareName']='%s' % _('Enigma2')
				discover['FirmwareVersion']='%s' % getEnigmaVersionString()
			discover['DeviceID']='%s' % deviceid
			discover['DeviceAuth']='%s' % deviceauth
			discover['DeviceUUID']='%s' % device_uuid

		discover['Manufacturer']='Silicondust'
		discover['BaseURL']='%s' % ip_port
		discover['LineupURL']='%s/lineup.json' % ip_port
		discover['TunerCount']=tunercount(dvb_type)
		return discover

def tunercount(dvbtype):
	return len(nimmanager.getNimListOfType(dvbtype)) if dvbtype != "multi" else len(nimmanager.nimList())

def discoverdata(dvbtype):
	device_info = getDeviceInfo()
	output = device_info.discoverJSON(dvb_type=dvbtype)
	return output

def write_discover(dvbtype="DVB-S"):
	data = discoverdata(dvbtype=dvbtype)
	try:
		with open('/etc/enigma2/%s.discover' % dvbtype, 'w') as outfile:
			json.dump(data, outfile)
		outfile.close()
	except Exception, e:
		print "Error opening %s for writing" % writefile
		return

def devicedata(dvbtype):
	datafile = open('/etc/enigma2/%s.device' % dvbtype,'r')
	xmldoc = datafile.read()
	datafile.close()
	return xmldoc

def write_device_xml(dvbtype):
	discover = discoverdata(dvbtype=dvbtype)
	xml = """<root xmlns="urn:schemas-upnp-org:device-1-0">
    <specVersion>
        <major>1</major>
        <minor>0</minor>
    </specVersion>
    <URLBase>{base_url}</URLBase>
    <device>
        <deviceType>urn:schemas-upnp-org:device:MediaServer:1</deviceType>
        <friendlyName>{friendly_name}</friendlyName>
        <manufacturer>{manufacturer}</manufacturer>
        <modelName>{model_name}</modelName>
        <modelNumber>{model_number}</modelNumber>
        <serialNumber>{serial_number}</serialNumber>
        <UDN>uuid:{uuid}</UDN>
    </device>
</root>"""
	xmlfile = xml.format(base_url=discover['BaseURL'],
                      friendly_name=discover['FriendlyName'],
                      manufacturer=discover['Manufacturer'],
                      model_name=discover['ModelNumber'].upper(),
                      model_number=discover['ModelNumber'].lower(),
                      serial_number="",
                      uuid=discover['DeviceUUID'])

	with open('/etc/enigma2/%s.device' % dvbtype, 'w') as outfile:
		outfile.writelines(xmlfile)
	outfile.close()

getdeviceinfo = modules[__name__]
