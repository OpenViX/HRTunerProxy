# -*- coding: utf-8 -*-
import gettext
import socket
import fcntl
import struct

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE

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

def getIF():
	eth0 = getIfConfig('eth0')
	eth1 = getIfConfig('eth1')
	if eth0.has_key('addr'):
		return 'eth0'
	elif eth1.has_key('addr'):
		return 'eth1'

def getIP():
	IP = '0.0.0.0'
	eth = getIfConfig(getIF())
	if eth.has_key('addr'):
		IP = eth['addr']
	return '%s' % IP

PluginLanguageDomain = "PlexDVRAPI"
PluginLanguagePath = "SystemPlugins/PlexDVRAPI/locale"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())
