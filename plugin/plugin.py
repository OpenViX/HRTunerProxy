from __future__ import print_function
from __future__ import absolute_import

import threading
import string
import random
import json
from sys import modules
from os import path, remove, mkdir, rename, listdir, rmdir
from shutil import rmtree

from enigma import getDesktop, eDVBResourceManager

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config, configfile, ConfigSelection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from . import _, tunerTypes, tunerfolders, tunerports, getIP, logger, isDreamOS
from .about import HRTunerProxy_About
from .getLineup import getlineup
from .getDeviceInfo import getdeviceinfo
from .ssdp import SSDPServer
from .server import server

BaseURL = {}
FriendlyName = {}
TunerCount = {}
Source = {}
NoOfChannels = {}
choicelist = []


def TunerInfoDebug(type=None):
	if type:
		logger.info('%s' % str(BaseURL[type]).replace('\n', ''))
		logger.info('%s' % str(FriendlyName[type]).replace('\n', ''))
		logger.info('%s' % str(Source[type]).replace('\n', ''))
		logger.info('%s' % str(TunerCount[type]).replace('\n', ''))
		logger.info('%s' % str(NoOfChannels[type]).replace('\n\n', ''))
		logger.info('Bouquet %s' % config.hrtunerproxy.bouquets_list[type].value)
	else:
		for type in tunerTypes:
			logger.info('%s' % str(BaseURL[type]).replace('\n', ''))
			logger.info('%s' % str(FriendlyName[type]).replace('\n', ''))
			logger.info('%s' % str(Source[type]).replace('\n', ''))
			logger.info('%s' % str(TunerCount[type]).replace('\n', ''))
			logger.info('%s' % str(NoOfChannels[type]).replace('\n\n', ''))
			logger.info('Bouquet %s' % config.hrtunerproxy.bouquets_list[type].value)


def TunerInfo(type=None):
	if type:
		discover = getdeviceinfo.discoverdata(type)
		nochl = getlineup.noofchannels(type, config.hrtunerproxy.bouquets_list[type].value)
		BaseURL[type] = 'BaseURL: %s\n' % str(discover["BaseURL"])
		FriendlyName[type] = 'FriendlyName: %s\n' % str(discover["FriendlyName"])
		TunerCount[type] = 'TunerCount: %s\n' % str(getdeviceinfo.tunercount(type)) if type != 'iptv' else 'TunerCount: %s\n' % str(config.hrtunerproxy.iptv_tunercount.value)
		Source[type] = 'Source: %s\n' % str(tunerfolders[type]).title() if type != 'iptv' else 'Source: %s\n' % str(tunerfolders[type]).upper()
		NoOfChannels[type] = 'Channels: %s\n\n' % str(nochl)

	else:
		global choicelist
		choicelist = []
		for type in tunerTypes:
			discover = getdeviceinfo.discoverdata(type)
			nochl = getlineup.noofchannels(type, 'all')
			BaseURL[type] = 'BaseURL: %s\n' % str(discover["BaseURL"])
			FriendlyName[type] = 'FriendlyName: %s\n' % str(discover["FriendlyName"])
			TunerCount[type] = 'TunerCount: %s\n' % str(getdeviceinfo.tunercount(type)) if type != 'iptv' else 'TunerCount: %s\n' % str(config.hrtunerproxy.iptv_tunercount.value)
			Source[type] = 'Source: %s\n' % str(tunerfolders[type]).title() if type != 'iptv' else 'Source: %s\n' % str(tunerfolders[type]).upper()
			NoOfChannels[type] = 'Channels: %s\n\n' % str(nochl)


if config.hrtunerproxy.debug.value:
	TunerInfo()
	TunerInfoDebug()

for type in tunerTypes:
	discover = getdeviceinfo.discoverdata(type)
	if getdeviceinfo.tunercount(type) > 0:
		choicelist.append((type, str(tunerfolders[type]).title()))

config.hrtunerproxy.type = ConfigSelection(choices=choicelist)
if config.hrtunerproxy.debug.value:
	logger.info('Using Tuner: %s' % str(config.hrtunerproxy.type.value))

tunerTypes = []
for type in config.hrtunerproxy.type.choices.choices:
	tunerTypes.append(type[0])


class HRTunerProxy_Setup(ConfigListScreen, Screen):
	instance = None
	if isDreamOS: # check if DreamOS image
		skin = "%s/skins/dreamos_main.xml" % (path.dirname(modules[__name__].__file__))
	else:
		skin = "%s/skins/main.xml" % (path.dirname(modules[__name__].__file__))
	f = open(skin, "r")
	skin = f.read()
	f.close()

	def __init__(self, session, menu_path=""):
		Screen.__init__(self, session)
		if hasattr(config.usage, 'show_menupath'):
			screentitle = _("HR-Tuner Proxy for Enigma2")
			self.menu_path = menu_path
			if config.usage.show_menupath.value == 'large':
				self.menu_path += screentitle
				title = self.menu_path
				self["menu_path_compressed"] = StaticText("")
				self.menu_path += ' / '
			elif config.usage.show_menupath.value == 'small':
				title = screentitle
				condtext = ""
				if self.menu_path and not self.menu_path.endswith(' / '):
					condtext = self.menu_path + " >"
				elif self.menu_path:
					condtext = self.menu_path[:-3] + " >"
				self["menu_path_compressed"] = StaticText(condtext)
				self.menu_path += screentitle + ' / '
			else:
				title = screentitle
				self["menu_path_compressed"] = StaticText("")
		else:
			title = _("HR-Tuner Proxy for Enigma2")
			self.menu_path = ""
		Screen.setTitle(self, title)

		self.savedval = config.hrtunerproxy.type.value

		self.onChangedEntry = []
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.onChange)

		self["information"] = Label()
		self["hinttext"] = Label()
		self["actions"] = ActionMap(['ColorActions', 'OkCancelActions', 'DirectionActions'],
									{
									"cancel": self.keyCancel,
									"red": self.keyCancel,
									"green": self.keySave,
									"yellow": self.cleanfiles,
									"blue": self.about
									}, -2)
		self["actions"].setEnabled(False)

		self["okaction"] = ActionMap(['OkCancelActions'],
									{
									"ok": self.ok,
									"cancel": self.keyCancel,
									}, -2)
		self["okaction"].setEnabled(False)

		self["closeaction"] = ActionMap(['OkCancelActions', 'ColorActions'],
									{
									"ok": self.keyCancel,
									"cancel": self.keyCancel,
									"red": self.keyCancel
									}, -2)
		self["closeaction"].setEnabled(False)

		self["key_red"] = Button(_("Close"))
		self["key_red"].hide()
		self["button_red"] = Pixmap()
		self["button_red"].hide()
		self["key_green"] = Button()
		self["key_green"].hide()
		self["button_green"] = Pixmap()
		self["button_green"].hide()
		self["key_yellow"] = Button()
		self["key_yellow"].hide()
		self["button_yellow"] = Pixmap()
		self["button_yellow"].hide()
		self["key_blue"] = Button(_("About"))
		self["button_blue"] = Pixmap()

		self.firstrun = True

		assert HRTunerProxy_Setup.instance is None, "class is a singleton class and just one instance of this class is allowed!"
		HRTunerProxy_Setup.instance = self

		self.onLayoutFinish.append(self.LayoutFinish)
		self.onClose.append(self.__onClose)

	def LayoutFinish(self):
		print('LayoutFinish')
		self.createmenu()
		if getIP() == '0.0.0.0':
			self["information"].setText(_('WARNING: No IP address found. Please make sure you are connected to your LAN via ethernet or Wi-Fi.\n\nPress OK to exit.'))
			self["hinttext"].hide()
			self["key_red"].show()
			self["button_red"].show()
			self["closeaction"].setEnabled(True)
		else:
			self.populate()

	def onChange(self):
		print('onChange')
		currentconfig = self["config"].getCurrent()[0]
		if currentconfig == _('Tuner type to use.'):
			self.createmenu()
		self.populate()

	def selectionChanged(self):
		print('selectionChanged')
		self.populate()

	def __onClose(self):
		HRTunerProxy_Setup.instance = None

	def about(self):
		self.session.open(HRTunerProxy_About, self.menu_path)

	def createmenu(self):
		self.list = []
		self.list.append(getConfigListEntry(_('Tuner type to use.'), config.hrtunerproxy.type))
		self.list.append(getConfigListEntry(_('Bouquet to use.'), config.hrtunerproxy.bouquets_list[config.hrtunerproxy.type.value]))
		if config.hrtunerproxy.type.value == 'iptv':
			self.list.append(getConfigListEntry(_('Number of concurrent streams.'), config.hrtunerproxy.iptv_tunercount))
		self.list.append(getConfigListEntry(_('Debug Mode.'), config.hrtunerproxy.debug))
		self["config"].list = self.list
		self["config"].l.setList(self.list)
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)

	def populate(self, answer=None):
		print('populate')
		setup_exists = False
		self["actions"].setEnabled(False)
		self["closeaction"].setEnabled(False)
		self["key_red"].hide()
		self["key_green"].hide()
		self["key_yellow"].hide()
		self["key_blue"].hide()
		self["button_red"].hide()
		self["button_green"].hide()
		self["button_yellow"].hide()
		self["button_blue"].hide()

		type = config.hrtunerproxy.type.value
		currentconfig = self["config"].getCurrent()[0]

		TunerInfo(type)
		if config.hrtunerproxy.debug.value:
			TunerInfoDebug(type)

		self.label = (BaseURL[type] + FriendlyName[type] + Source[type] + TunerCount[type] + NoOfChannels[type])

		for types in tunerTypes:
			if path.exists('/etc/enigma2/%s.discover' % types):
				setup_exists = True

		if not path.exists('/etc/enigma2/%s.discover' % type):
			if int(NoOfChannels[type].split(': ')[1]) == 0:
				if config.hrtunerproxy.bouquets_list[type].value == None:
					self["information"].setText(_('Please note: Please now select a bouquet to use.'))
				else:
					self["information"].setText(_('Please note: You do not seem to have any channels setup for this tuner, please add some channels to Enigma2 or choose anther tuner type.'))
				self["hinttext"].setText('')
				self["key_red"].show()
				self["button_red"].show()
				self["closeaction"].setEnabled(True)
			elif int(TunerCount[type].split(': ')[1]) < 2:
				self["information"].setText(_('WARNING: It seems you have a single tuner box. If the box is not left in standby your recordings WILL fail.'))
				self["hinttext"].setText(_('Press OK to continue setting up this tuner.'))
				self.hinttext = ''
				self["okaction"].setEnabled(True)
				self["key_green"].setText(_("Save"))
				self["key_yellow"].setText("")
			else:
				if currentconfig == _('Tuner type to use.'):
					self["hinttext"].setText(_('Press OK to continue setting up this tuner or press LEFT / RIGHT to select a different tuner type.'))
					self.hinttext = _('Press LEFT / RIGHT to select a different tuner type.')
				elif currentconfig == _('Bouquet to use.'):
					self["hinttext"].setText(_('Press OK to continue setting up this tuner or select a different tuner type.'))
					self.hinttext = _('Press LEFT / RIGHT to select a different bouquet.')
				elif currentconfig == _('Debug mode to create logs.'):
					self["hinttext"].setText(_('Press OK to continue setting up this tuner or select a different tuner type.'))
					self.hinttext = _('Press LEFT / RIGHT to select a different bouquet.')
				else:
					self["hinttext"].setText(_('Press OK to continue setting up this tuner or select a different tuner type.'))
					self.hinttext = _('Press LEFT / RIGHT to set number of concurent streams.')
				if not setup_exists and self.firstrun:
					print('U1')
					self["information"].setText(_('Please note: DVR feature in Plex / Emby is a premium / premiere feature. For more information please refer to:\nhttps://www.plex.tv/features/plex-pass\nhttps://emby.media/premiere.html'))
					self["hinttext"].setText(_('Press OK to continue setting up.'))
				elif setup_exists:
					print('U2')
					self["information"].setText(_('Please note: To use another tuner type in Plex you need to setup/have another server.\nAre you sure you want to continue?'))
				else:
					print('U3')
					if currentconfig == _('Tuner type to use.'):
						self.hinttext = _('Press LEFT / RIGHT to select a different tuner type.')
						print('T2')
					elif currentconfig == _('Bouquet to use.'):
						print('T3')
						self.hinttext = _('Press LEFT / RIGHT to select a different bouquet.')
					elif currentconfig == _('Debug Mode.'):
						print('T4')
						self.hinttext = _('Press LEFT / RIGHT to enable or disable debug mode.')
					self.ok()
				self["okaction"].setEnabled(True)
				self["key_green"].setText(_("Save"))
				self["key_yellow"].setText("")
		else:
			print('T1')
			if currentconfig == _('Tuner type to use.'):
				self.hinttext = _('Press LEFT / RIGHT to select a different tuner type.')
				print('T2')
			elif currentconfig == _('Bouquet to use.'):
				print('T3')
				self.hinttext = _('Press LEFT / RIGHT to select a different bouquet.')
			elif currentconfig == _('Debug Mode.'):
				print('T4')
				self.hinttext = _('Press LEFT / RIGHT to enable or disable debug mode.')
			self["key_green"].setText(_("Save"))
			self["key_yellow"].setText(_("Delete"))
			self["key_yellow"].show()
			self["button_yellow"].show()
			self.ok()

	def cleanfiles(self):
		type = config.hrtunerproxy.type.value
		if path.exists('/etc/enigma2/%s.discover' % type):
			self.session.openWithCallback(self.cleanconfirm, MessageBox, text=_("Do you really want to remove the files for this tuner type? Doing so will cause your DVR to be none functional."), type=MessageBox.TYPE_YESNO)

	def cleanconfirm(self, answer):
		if answer is not None and answer and self["config"].getCurrent() is not None:
			type = config.hrtunerproxy.type.value
			if config.hrtunerproxy.debug.value:
				logger.info('Deleting files for %s' % type)
			if path.exists('/etc/enigma2/%s.discover' % type):
				remove('/etc/enigma2/%s.discover' % type)
			if path.exists('/etc/enigma2/%s.device' % type):
				remove('/etc/enigma2/%s.device' % type)
			self.session.openWithCallback(self.rebootconfirm, MessageBox, text=_("Files deleted. Please restart enigma2.\n\nDo you want to restart now?"), type=MessageBox.TYPE_YESNO)

	def ok(self):
		self.firstrun = False
		self["okaction"].setEnabled(False)
		self["actions"].setEnabled(True)
		self["information"].setText(self.label)
		self["hinttext"].setText(self.hinttext)
		self["hinttext"].show()

		self["key_red"].show()
		self["key_green"].show()
		self["key_blue"].show()

		self["button_red"].show()
		self["button_green"].show()
		self["button_blue"].show()

	def keySave(self):
		if self.savedval != config.hrtunerproxy.type.value and path.exists('/etc/enigma2/%s.device' % self.savedval):
			self.session.openWithCallback(self.saveconfirm, MessageBox, text=_("It seems you have already set up another tuner. Your server can only support one tuner type. To use this additional tuner type you will need to setup another server. Do you want to continue creating the files?"), type=MessageBox.TYPE_YESNO)
		else:
			self.saveconfirm(True)

	def saveconfirm(self, answer):
		if answer is not None and answer and self["config"].getCurrent() is not None:
			type = config.hrtunerproxy.type.value
			newsetup = False
			if not path.exists('/etc/enigma2/%s.discover' % type):
				newsetup = True
			if config.hrtunerproxy.debug.value:
				logger.info('Creating files for %s' % type)
			getdeviceinfo.write_discover(dvbtype=type)
			if not path.exists('/etc/enigma2/%s.device' % self.savedval):
				getdeviceinfo.write_device_xml(dvbtype=type)
				config.hrtunerproxy.type.save()
			config.hrtunerproxy.bouquets_list[config.hrtunerproxy.type.value].save()
			config.hrtunerproxy.debug.save()
			configfile.save()
			if self.savedval != config.hrtunerproxy.type.value and path.exists('/etc/enigma2/%s.device' % self.savedval) or newsetup:
				self.session.openWithCallback(self.rebootconfirm, MessageBox, text=_("Files created. Please restart enigma2 and then you should be able to add this STB to your server.\n\nDo you want to restart now?"), type=MessageBox.TYPE_YESNO)
			else:
				self.close()

	def rebootconfirm(self, answer):
		if answer is not None and answer:
			from enigma import quitMainloop
			quitMainloop(3)

	def cancelConfirm(self, result):
		if not result:
			return
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"), default=False)
		else:
			self.close()


class TunerMask():
	def __init__(self):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			res_mgr.frontendUseMaskChanged.get().append(self.tunerUseMaskChanged)

	def tunerUseMaskChanged(self, mask):
		config.hrtunerproxy.slotsinuse.setValue(mask)


def startssdp(dvbtype):
	discover = getdeviceinfo.discoverdata(dvbtype)
	device_uuid = discover['DeviceUUID']
	if config.hrtunerproxy.debug.value:
		logger.info('Starting SSDP for %s, device_uuid: %s' % (dvbtype, device_uuid))
	local_ip_address = getIP()
	ssdp = SSDPServer()
	ssdp.register('local',
				  'uuid:{}::upnp:rootdevice'.format(device_uuid),
				  'upnp:rootdevice',
				  'http://{}:{}/device.xml'.format(local_ip_address, tunerports[dvbtype]))
	thread_ssdp = threading.Thread(target=ssdp.run, args=())
	thread_ssdp.daemon = True # Daemonize thread
	thread_ssdp.start()


def starthttpserver(dvbtype):
	if config.hrtunerproxy.debug.value:
		logger.info('Starting HTTPServer for %s' % dvbtype)
	thread_http = threading.Thread(target=server.run, args=(dvbtype,))
	thread_http.daemon = True # Daemonize thread
	thread_http.start()


def HRTunerProxy_AutoStart(reason, session=None, **kwargs):
	if config.hrtunerproxy.debug.value:
		logger.info('Starting AutoSart reason: %s, for types: %s' % (reason, tunerTypes))
	if reason == 0:
		for type in tunerTypes:
			if path.exists('/etc/enigma2/%s.discover' % type):
				starthttpserver(type)
			if path.exists('/etc/enigma2/%s.device' % type):
				startssdp(type)
			if not isDreamOS: # check if DreamOS image
				TunerMask()


def HRTunerProxy_SetupMain(session, **kwargs):
	session.open(HRTunerProxy_Setup)


def startHRTunerProxy_Setup(menuid):
	if menuid != "system":
		return []
	return [(_("HR-Tuner Proxy"), HRTunerProxy_SetupMain, "dvr_setup", None)]


def Plugins(**kwargs):
	screenwidth = getDesktop(0).size().width()
	if screenwidth and screenwidth == 1920:
		iconpic = "plugin-hd.png"
	else:
		iconpic = "plugin.png"
	return [PluginDescriptor(name="HRTunerProxy", description=_("Setup the HR-Tuner Proxy server"), where=PluginDescriptor.WHERE_SESSIONSTART, fnc=HRTunerProxy_AutoStart, needsRestart=True),
			PluginDescriptor(name="HRTunerProxy", description=_("Setup the HR-Tuner Proxy server"), icon=iconpic, where=PluginDescriptor.WHERE_PLUGINMENU, fnc=HRTunerProxy_SetupMain),
			PluginDescriptor(name="HRTunerProxy", description=_("Setup the HR-Tuner Proxy server"), where=PluginDescriptor.WHERE_MENU, needsRestart=False, fnc=startHRTunerProxy_Setup)]
