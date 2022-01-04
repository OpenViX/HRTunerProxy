# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import

import gettext
import socket
import fcntl
import struct
import logging
from os import path, remove, environ as os_environ

from Components.config import config, ConfigSubsection, ConfigSubDict, ConfigSelection, ConfigSelectionNumber, ConfigNumber, ConfigEnableDisable, NoSave
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE

from .getLineup import getBouquetsList

try:
	from enigma import eMediaDatabase
	isDreamOS = True
except:
	isDreamOS = False

import six

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
	'DVB-C': 'Cable',
	'DVB-T': 'Antenna',
	'DVB-S': 'Cable',
	'multi': 'Cable',
	'iptv': 'Cable'
	}

tunerports = {
	'DVB-C': '6081',
	'DVB-T': '6082',
	'DVB-S': '6083',
	'multi': '6084',
	'iptv': '6085'
	}

tunerfolders = {
	'DVB-C': 'cable',
	'DVB-T': 'antenna',
	'DVB-S': 'satellite',
	'multi': 'multi',
	'iptv': 'iptv'
	}

porttypes = {
	6081: 'DVB-C',
	6082: 'DVB-T',
	6083: 'DVB-S',
	6084: 'multi',
	6085: 'iptv'
	}

config.hrtunerproxy = ConfigSubsection()
config.hrtunerproxy.bouquets_list = ConfigSubDict()
for type in tunerTypes:
	config.hrtunerproxy.bouquets_list[type] = ConfigSelection(default=None, choices=[(None, _('Not set')), ('all', _('All'))] + getBouquetsList())
config.hrtunerproxy.iptv_tunercount = ConfigSelectionNumber(min=1, max=10, stepwidth=1, default=2, wraparound=True)
config.hrtunerproxy.slotsinuse = NoSave(ConfigNumber())
config.hrtunerproxy.debug = ConfigEnableDisable(default=False)


def getVersion():
	if path.exists("/usr/lib/enigma2/python/Plugins/SystemPlugins/HRTunerProxy/PLUGIN_VERSION"):
		f = open("/usr/lib/enigma2/python/Plugins/SystemPlugins/HRTunerProxy/PLUGIN_VERSION")
		PLUGIN_VERSION = _('v%s ') % f.read().replace('\n', '')
		f.close()
	else:
		PLUGIN_VERSION = ''
	return PLUGIN_VERSION


if config.hrtunerproxy.debug.value:
	logger.info('Version: %s' % getVersion())


def _ifinfo(sock, addr, ifname):
	iface = struct.pack('256s', six.ensure_binary(ifname[:15]))
	info = fcntl.ioctl(sock.fileno(), addr, iface)
	if addr == 0x8927:
		return ':'.join(['%02x' % (char if six.PY3 else ord(char)) for char in info[18:24]]).upper()
	else:
		return socket.inet_ntoa(info[20:24])


def getIfConfig(ifname):
	ifreq = {'ifname': ifname}
	infos = {}
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# offsets defined in /usr/include/linux/sockios.h on linux 2.6
	infos['addr'] = 0x8915 # SIOCGIFADDR
	infos['brdaddr'] = 0x8919 # SIOCGIFBRDADDR
	infos['hwaddr'] = 0x8927 # SIOCSIFHWADDR
	infos['netmask'] = 0x891b # SIOCGIFNETMASK
	try:
		for k, v in infos.items():
			ifreq[k] = _ifinfo(sock, v, ifname)
	except:
		pass
	sock.close()
	return ifreq


def getIfInfo():
	for port in ('eth0', 'eth1', 'wlan0', 'wlan1', 'wlan2', 'wlan3', 'ra0'):
		ifinfo = getIfConfig(port)
		if 'addr' in ifinfo:
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
			print("[" + PluginLanguageDomain + "] fallback to default translation for " + txt)
			return gettext.gettext(txt)
	language.addCallback(localeInit())
