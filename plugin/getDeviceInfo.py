from __future__ import print_function
from __future__ import absolute_import

import string
import random
import json
import uuid
from socket import gethostname
from os import path, mkdir
from sys import modules

from Components.About import about
from Components.NimManager import nimmanager
from Components.config import config

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

from .getLineup import getlineup
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
			with open('/etc/enigma2/%s.discover' % dvb_type) as data_file:
				discover = json.load(data_file)
			discover.pop('NumChannels', None)
		else:
			discover = {}
			deviceauth = generator(24, charset['auth'])
			deviceid = generator(8, charset['id'])
			if brandingmodule:
				discover['FriendlyName'] = '%s %s' % (getMachineBrand(), getMachineName())
				discover['ModelNumber'] = '%s' % getBoxType()
				discover['FirmwareName'] = '%s' % getImageDistro()
				discover['FirmwareVersion'] = '%s' % getDriverDate()
			else:
				discover['FriendlyName'] = '%s' % gethostname()
				discover['ModelNumber'] = '%s' % getBoxType()
				discover['FirmwareName'] = '%s' % _('Enigma2')
				discover['FirmwareVersion'] = '%s' % getEnigmaVersionString()
			discover['DeviceID'] = '%s' % deviceid
			discover['DeviceAuth'] = '%s' % deviceauth
			discover['DeviceUUID'] = '%s' % device_uuid

		discover['Manufacturer'] = 'Silicondust'
		discover['BaseURL'] = '%s' % ip_port
		discover['LineupURL'] = '%s/lineup.json' % ip_port
		discover['TunerCount'] = tunercount(dvb_type)
		return discover

	def tunersInUse(self):
		# returns list of nim.slot numbers that are currenly in use
		mask = config.hrtunerproxy.slotsinuse.value
		print("[HRTunerProxy] mask:%s\n" % mask)
		slots = []
		for i in range(len(format(mask, 'b'))):
			if (mask >> i) & 0x1:
				slots.append(i)
		return slots

	def getTunerInfo(self, dvb_type):
		nimList = getNimList(dvb_type)
		tunersInUse = self.tunersInUse()
		print("[HRTunerProxy] tunersInUse", tunersInUse)
		tunerstatus = {}
		x = 0
		for nim in nimList:
			status = _("In use") if nim in tunersInUse else "none"
			tunerstatus["tuner%s" % x] = status
			x += 1
		return tunerstatus


def getNimList(dvbtype):
	return nimmanager.getNimListOfType(dvbtype) if dvbtype not in ('multi', 'iptv') else nimmanager.nimList()


def tunercount(dvbtype):
	return len(nimmanager.getNimListOfType(dvbtype)) if dvbtype not in ('multi', 'iptv') else len(nimmanager.nimList())


def tunerdata(dvbtype):
	device_info = getDeviceInfo()
	output = device_info.getTunerInfo(dvbtype)
	return output


def tunerstatus(dvbtype):
	discover = discoverdata(dvbtype=dvbtype)
	ts = tunerdata(dvbtype)
	data = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<title>Tuner Status</title>
<link rel="stylesheet" type="text/css" href="/style.css" />
</head>
<body>
<div class="B C" style="background: #c0c0c0">
<a href="/"><div class="T">%s</div></a>
<div class="S">Tuner Status</div>
<table>
""" % discover['FriendlyName']
	for x in range(tunercount(dvbtype)):
		data += "<tr><td>Tuner %s Channel</td><td>%s</td></tr>\n" % (x, ts["tuner%s" % x])
	data += """</table>
</div>
</body>
</html>"""
	return data


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
	except Exception as e:
		print("Error opening %s for writing" % writefile)
		return


def devicedata(dvbtype):
	if path.exists('/etc/enigma2/%s.device' % dvbtype):
		datafile = open('/etc/enigma2/%s.device' % dvbtype, 'r')
		xmldoc = datafile.read()
		datafile.close()
	else:
		xmldoc = ""
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
