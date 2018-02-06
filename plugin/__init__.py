# -*- coding: utf-8 -*-
import gettext
import socket
import fcntl
import struct
import logging
from os import path, remove, environ as os_environ
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE

try:
	from enigma import eMediaDatabase
	isDreamOS = True
except:
	isDreamOS = False

if path.exists('/tmp/hrtunerproxy.log'):
	remove('/tmp/hrtunerproxy.log')
logger = logging.getLogger('[HRTunerProxy]')
hdlr = logging.FileHandler('/tmp/hrtunerproxy.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

tunerTypes = ('DVB-C', 'DVB-T', 'DVB-S', 'iptv', 'multi')

tunertypes = {
	'DVB-C' : 'Cable',
	'DVB-T' : 'Antenna',
	'DVB-S' : 'Cable',
	'multi' : 'Cable',
	'iptv' : 'Cable'
	}

tunerports = {
	'DVB-C' : '6081',
	'DVB-T' : '6082',
	'DVB-S' : '6083',
	'multi' : '6084',
	'iptv' : '6085'
	}

tunerfolders = {
	'DVB-C' : 'cable',
	'DVB-T' : 'antenna',
	'DVB-S' : 'satellite',
	'multi' : 'multi',
	'iptv' : 'iptv'
	}

porttypes = {
	6081 : 'DVB-C',
	6082 : 'DVB-T',
	6083 : 'DVB-S',
	6084 : 'multi',
	6085 : 'iptv'
	}

def _ifinfo(sock, addr, ifname):
	iface = struct.pack('256s', ifname[:15])
	info  = fcntl.ioctl(sock.fileno(), addr, iface)
	if addr == 0x8927:
		return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1].upper()
	else:
		return socket.inet_ntoa(info[20:24])

def getIfConfig(ifname):
	ifreq = {'ifname': ifname}
	infos = {}
	sock  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# offsets defined in /usr/include/linux/sockios.h on linux 2.6
	infos['addr']    = 0x8915 # SIOCGIFADDR
	infos['brdaddr'] = 0x8919 # SIOCGIFBRDADDR
	infos['hwaddr']  = 0x8927 # SIOCSIFHWADDR
	infos['netmask'] = 0x891b # SIOCGIFNETMASK
	try:
		for k,v in infos.items():
			ifreq[k] = _ifinfo(sock, v, ifname)
	except:
		pass
	sock.close()
	return ifreq

def getIfInfo():
	for port in ('eth0', 'eth1', 'wlan0', 'wlan1', 'wlan2', 'wlan3', 'ra0'):
		ifinfo = getIfConfig(port)
		if ifinfo.has_key('addr'):
			return ifinfo
	return None

def getIP():
	IP = '0.0.0.0'
	ifinfo = getIfInfo()
	if ifinfo:
		IP = ifinfo['addr']
	return '%s' % IP

PluginLanguageDomain = "HRTunerProxy"
PluginLanguagePath = "SystemPlugins/HRTunerProxy/locale"

def localeInit():
	if isDreamOS: # check if opendreambox image
		lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
		os_environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

if isDreamOS: # check if DreamOS image
	_ = lambda txt: gettext.dgettext(PluginLanguageDomain, txt) if txt else ""
	localeInit()
	language.addCallback(localeInit)
else:
	def _(txt):
		if gettext.dgettext(PluginLanguageDomain, txt):
			return gettext.dgettext(PluginLanguageDomain, txt)
		else:
			print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
			return gettext.gettext(txt)
	language.addCallback(localeInit())
