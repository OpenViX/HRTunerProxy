import string
import random
import json
from os import path, mkdir
from sys import modules

from Components.About import about
from Components.NimManager import nimmanager

try:
	from boxbranding import getMachineName, getDriverDate, getBoxType, getMachineBrand, getImageDistro
	brandingmodule = True
import:
	from enigma import getBoxType, getEnigmaVersionString
	brandingmodule = False

from getLineup import getlineup
from . import tunertypes, tunerports, tunerfolders, getIP, device_uuids

discover = {}
noofchannels = {}

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
		if path.exists('/www/%s/discover.json' % tunerfolders[dvb_type]):
			with open('/www/%s/discover.json' % tunerfolders[dvb_type]) as data_file:
				discover[dvb_type] = json.load(data_file)
		else:
			discover[dvb_type] = {}
			deviceauth = generator(24, charset['auth'])
			deviceid = generator(8, charset['id'])
			if brandingmodule:
				discover[dvb_type]['FriendlyName']='%s %s' % (getMachineBrand(), getMachineName())
				discover[dvb_type]['ModelNumber']='%s' % getBoxType()
				discover[dvb_type]['FirmwareName']='%s' % getImageDistro()
				discover[dvb_type]['FirmwareVersion']='%s' % getDriverDate()
			else:
				discover[dvb_type]['FriendlyName']='%s' % _('Enigma2 STB')
				discover[dvb_type]['ModelNumber']='%s' % getBoxType()
				discover[dvb_type]['FirmwareName']='%s' % _('Enigma2')
				discover[dvb_type]['FirmwareVersion']='%s' % getEnigmaVersionString()
			discover[dvb_type]['DeviceID']='%s' % deviceid
			discover[dvb_type]['DeviceAuth']='%s' % deviceauth
			discover[dvb_type]['BaseURL']='%s' % ip_port
			discover[dvb_type]['LineupURL']='%s/lineup.json' % ip_port
			discover[dvb_type]['TunerCount']=len(nimmanager.getNimListOfType(dvb_type)) if dvb_type != "multi" else len(nimmanager.nimList())
			discover[dvb_type]['NumChannels']=getlineup.noofchannels(dvb_type)
			discover[dvb_type]['DeviceUUID']='%s' % device_uuids[dvb_type]
		return discover

def deviceinfo(dvbtype):
	device_info = getDeviceInfo()
	output = device_info.discoverJSON(dvb_type=dvbtype)
	return output

def write_device_xml(writefile = "/tmp/device.xml", dvbtype="DVB-S"):
	device_info = getDeviceInfo()
	discover = device_info.discoverJSON(dvb_type=dvbtype)
	if not path.exists('/www/%s' % tunerfolders[dvbtype]):
		mkdir('/www/%s' % tunerfolders[dvbtype])

	xml = """<root xmlns="urn:schemas-upnp-org:device-1-0">
    <specVersion>
        <major>1</major>
        <minor>0</minor>
    </specVersion>
    <URLBase>{base_url}</URLBase>
    <device>
        <deviceType>urn:schemas-upnp-org:device:Basic:1</deviceType>
        <friendlyName>{friendly_name}</friendlyName>
        <manufacturer>{manufacturer}</manufacturer>
        <modelName>{model_name}</modelName>
        <modelNumber>{model_number}</modelNumber>
        <serialNumber>{serial_number}</serialNumber>
        <UDN>uuid:{uuid}</UDN>
    </device>
</root>"""

	xmlfile = xml.format(base_url=discover[dvbtype]['BaseURL'],
                      friendly_name=discover[dvbtype]['FriendlyName'],
                      manufacturer="Silicondust",
                      model_name=discover[dvbtype]['ModelNumber'].upper(),
                      model_number=discover[dvbtype]['ModelNumber'].lower(),
                      serial_number="",
                      uuid=discover[dvbtype]['DeviceUUID'])

	with open(writefile, 'w') as outfile:
		outfile.writelines(xmlfile)
	outfile.close()

def write_discover(writefile = "/tmp/discover.json", dvbtype="DVB-S"):
	device_info = getDeviceInfo()
	output = device_info.discoverJSON(dvb_type=dvbtype)
	if not path.exists('/www/%s' % tunerfolders[dvbtype]):
		mkdir('/www/%s' % tunerfolders[dvbtype])
	try:
		with open(writefile, 'w') as outfile:
			json.dump(output[dvbtype], outfile)
		outfile.close()
	except Exception, e:
		print "Error opening %s for writing" % writefile
		return

getdeviceinfo = modules[__name__]
