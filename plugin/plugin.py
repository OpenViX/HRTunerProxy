import threading
import string
import random
import json
from os import path, remove, mkdir, rename, listdir, rmdir
from shutil import rmtree

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config, configfile, ConfigSubsection, ConfigSubDict, ConfigSelection, getConfigListEntry, ConfigSelectionNumber, ConfigNumber, NoSave
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from . import _, tunerTypes, tunerfolders, tunerports, getIP, logger
from about import HRTunerProxy_About
from enigma import getDesktop, eDVBResourceManager
from getLineup import getlineup, getBouquetsList
from getDeviceInfo import getdeviceinfo
from ssdp import SSDPServer
from server import server

config.hrtunerproxy = ConfigSubsection()
config.hrtunerproxy.bouquets_list = ConfigSubDict()
for type in tunerTypes:
	config.hrtunerproxy.bouquets_list[type] = ConfigSelection(default = None, choices = [(None, _('Not set')), ('all', _('All'))] + getBouquetsList())
config.hrtunerproxy.iptv_tunercount = ConfigSelectionNumber(min = 1, max = 10, stepwidth = 1, default = 2, wraparound = True)
config.hrtunerproxy.slotsinuse = NoSave(ConfigNumber(default = ""))

BaseURL = {}
FriendlyName = {}
TunerCount = {}
Source = {}
NoOfChannels = {}
choicelist = []

def TunerInfoDebug(type=None):
	if type:
		logger.info('%s' % str(BaseURL[type]).replace('\n',''))
		logger.info('%s' % str(FriendlyName[type]).replace('\n',''))
		logger.info('%s' % str(Source[type]).replace('\n',''))
		logger.info('%s' % str(TunerCount[type]).replace('\n',''))
		logger.info('%s' % str(NoOfChannels[type]).replace('\n\n',''))
		logger.info('Bouquet %s' % config.hrtunerproxy.bouquets_list[type].value)
	else:
		for type in tunerTypes:
			logger.info('%s' % str(BaseURL[type]).replace('\n',''))
			logger.info('%s' % str(FriendlyName[type]).replace('\n',''))
			logger.info('%s' % str(Source[type]).replace('\n',''))
			logger.info('%s' % str(TunerCount[type]).replace('\n',''))
			logger.info('%s' % str(NoOfChannels[type]).replace('\n\n',''))
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

			if getdeviceinfo.tunercount(type) > 0 and nochl > 0:
				choicelist.append((type, str(tunerfolders[type]).title()))

TunerInfo()
TunerInfoDebug()
config.hrtunerproxy.type = ConfigSelection(default = "multi", choices = choicelist)
logger.info('Using Tuner: %s' % str(config.hrtunerproxy.type.value))

tunerTypes = []
for type in config.hrtunerproxy.type.choices.choices:
	tunerTypes.append(type[0])

class HRTunerProxy_Setup(ConfigListScreen, Screen):
	skin="""
	<screen position="50,50" size="600,350">
		<widget name="config" position="10,10" size="580,75" scrollbarMode="showOnDemand" />
		<widget name="information" position="10,95" size="580,185" font="Regular;22"/>
		<widget name="description" position="10,225" size="580,75" font="Regular;22" valign="bottom"/>
		<widget name="button_red" pixmap="skin_default/buttons/red.png" position="0,310" size="140,40" alphatest="on"/>
		<widget name="button_green" pixmap="skin_default/buttons/green.png" position="150,310" size="140,40" alphatest="on"/>
		<widget name="button_yellow" pixmap="skin_default/buttons/yellow.png" position="300,310" size="140,40" alphatest="on"/>
		<widget name="button_blue" pixmap="skin_default/buttons/blue.png" position="450,310" size="140,40" alphatest="on"/>
		<widget name="key_red" position="0,310" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>
		<widget name="key_green" position="150,310" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1"/>
		<widget name="key_yellow" position="300,310" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1"/>
		<widget name="key_blue" position="450,310" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1"/>
	</screen>"""

	def __init__(self, session, menu_path=""):
		instance = None
		Screen.__init__(self, session)
		if hasattr(config.usage, 'show_menupath'):
			screentitle =  _("HR-Tuner Proxy for Enigma2")
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
			title =  _("HR-Tuner Proxy for Enigma2")
			self.menu_path = ""
		Screen.setTitle(self, title)

		self.savedval = config.hrtunerproxy.type.value

		self.onChangedEntry = [ ]
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.populate)

		self["information"] = Label()
		self["description"] = Label()
		self["actions"] = ActionMap(['ColorActions','OkCancelActions', 'DirectionActions'],
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

		self["closeaction"] = ActionMap(['OkCancelActions'],
									{
									"ok": self.keyCancel,
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

		assert HRTunerProxy_Setup.instance is None, "class is a singleton class and just one instance of this class is allowed!"
		HRTunerProxy_Setup.instance = self

		self.onLayoutFinish.append(self.populate)
		self.onClose.append(self.__onClose)

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
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def populate(self, answer=None):
		self.createmenu()
		setup_exists = False
		self["actions"].setEnabled(False)
		self["key_red"].hide()
		self["key_green"].hide()
		self["key_yellow"].hide()
		self["key_blue"].hide()
		self["button_red"].hide()
		self["button_green"].hide()
		self["button_yellow"].hide()
		self["button_blue"].hide()

		if getIP() == '0.0.0.0' or not config.hrtunerproxy.type.value:
			if getIP() == '0.0.0.0':
				self["information"].setText(_('WARNING: No IP address found. Please make sure you are connected to your LAN via ethernet or Wi-Fi.\n\nPress OK to exit.'))
			else:
				self["information"].setText(_('WARNING: It seems you have no tuners with channels setup on this device. Please perform a channels scan or run ABM.\n\nPress OK to exit.'))
			self["description"].hide()
			self["closeaction"].setEnabled(True)

		elif self["config"].getCurrent() is not None:
			type = config.hrtunerproxy.type.value
			currentconfig = self["config"].getCurrent()[0]

			TunerInfo(type)
			TunerInfoDebug(type)

			self.label = (BaseURL[type]+FriendlyName[type]+Source[type]+TunerCount[type]+NoOfChannels[type])

			for types in tunerTypes:
				if path.exists('/etc/enigma2/%s.discover' % types):
					setup_exists = True

			if not path.exists('/etc/enigma2/%s.discover' % type):
				if getdeviceinfo.tunercount(type) < 2:
					self["information"].setText(_('WARNING: It seems you have a single tuner box. If the box is not left in standby your recordings WILL fail.'))
					self["description"].setText(_('Press OK to continue setting up this tuner.'))
					self.hinttext = _('Press GREEN to save your configuration files.')
					self["okaction"].setEnabled(True)
					self["key_green"].setText(_("Save"))
					self["key_yellow"].setText("")
				else:
					if not setup_exists:
						self["information"].setText(_('Please note: To use the DVR feature in Plex Server you need to be a Plex Pass user. For more information about Plex Pass see https://www.plex.tv/features/plex-pass'))
					else:
						self["information"].setText(_('Please note: To use another tuner type you need to setup/have another server. Are you sure you want to continue?'))
					if currentconfig == _('Tuner type to use'):
						self["description"].setText(_('Press OK to continue setting up this tuner or press LEFT / RIGHT to select a different tuner type.'))
						self.hinttext = _('Press LEFT / RIGHT to select a different tuner type.')
					elif currentconfig == _('Bouquet to use.'):
						self["description"].setText(_('Press OK to continue setting up this tuner or select a different tuner type.'))
						self.hinttext = _('Press LEFT / RIGHT to select a different bouquet.')
					else:
						self["description"].setText(_('Press OK to continue setting up this tuner or select a different tuner type.'))
						self.hinttext = _('Press LEFT / RIGHT to set number of concurent streams.')
					self.hinttext = self.hinttext + '\n'+_('Press GREEN to save your configuration.')
					self["okaction"].setEnabled(True)
					self["key_green"].setText(_("Save"))
					self["key_yellow"].setText("")
			else:
				if currentconfig == _('Tuner type to use'):
					self.hinttext = _('Press LEFT / RIGHT to select a different tuner type.')
				else:
					self.hinttext = _('Press LEFT / RIGHT to select a different bouquet.')
				self.hinttext = self.hinttext + '\n'+_('Press GREEN to save your configuration.')
				self["key_green"].setText(_("Save"))
				self["key_yellow"].setText(_("Delete"))
				self.ok()

	def cleanfiles(self):
		type = config.hrtunerproxy.type.value
		if path.exists('/etc/enigma2/%s.discover' % type):
			self.session.openWithCallback(self.cleanconfirm, MessageBox,text = _("Do you really want to remove the files for this tuner type? Doing so will cause your DVR to be none functional."), type = MessageBox.TYPE_YESNO)

	def cleanconfirm(self, answer):
		if answer is not None and answer and self["config"].getCurrent() is not None:
			type = config.hrtunerproxy.type.value
			logger.info('Deleting files for %s' % type)
			if path.exists('/etc/enigma2/%s.discover' % type):
				remove('/etc/enigma2/%s.discover' % type)
			if path.exists('/etc/enigma2/%s.device' % type):
				remove('/etc/enigma2/%s.device' % type)
			self.session.openWithCallback(self.rebootconfirm, MessageBox,text = _("Files deleted. Please restart enigma2.\n\nDo you want to restart now?"), type = MessageBox.TYPE_YESNO)

	def ok(self):
		self["okaction"].setEnabled(False)
		self["actions"].setEnabled(True)
		self["information"].setText(self.label)
		self["description"].setText(self.hinttext)
		self["description"].show()

		self["key_red"].show()
		self["key_green"].show()
		self["key_yellow"].show()
		self["key_blue"].show()

		self["button_red"].show()
		self["button_green"].show()
		self["button_yellow"].show()
		self["button_blue"].show()


	def keySave(self):
		if self.savedval != config.hrtunerproxy.type.value and path.exists('/etc/enigma2/%s.device' % self.savedval):
			self.session.openWithCallback(self.saveconfirm, MessageBox,text = _("It seems you have already set up another tuner. Your server can only support one tuner type. To use this additional tuner type you will need to setup another server. Do you want to continue creating the files?"), type = MessageBox.TYPE_YESNO)
		else:
			self.saveconfirm(True)

	def saveconfirm(self, answer):
		if answer is not None and answer and self["config"].getCurrent() is not None:
			type = config.hrtunerproxy.type.value
			newsetup = False
			if not path.exists('/etc/enigma2/%s.discover' % type):
				newsetup = True
			logger.info('Creating files for %s' % type)
			getdeviceinfo.write_discover(dvbtype=type)
			if not path.exists('/etc/enigma2/%s.device' % self.savedval):
				getdeviceinfo.write_device_xml(dvbtype=type)
				config.hrtunerproxy.type.save()
			config.hrtunerproxy.bouquets_list[config.hrtunerproxy.type.value].save()
			configfile.save()
			if self.savedval != config.hrtunerproxy.type.value and path.exists('/etc/enigma2/%s.device' % self.savedval) or newsetup:
				self.session.openWithCallback(self.rebootconfirm, MessageBox,text = _("Files created. Please restart enigma2 and then you should be able to add this STB to your server.\n\nDo you want to restart now?"), type = MessageBox.TYPE_YESNO)
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
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"), default = False)
		else:
			self.close()

class TunerMask():
	def __init__(self):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			res_mgr.frontendUseMaskChanged.get().append(self.tunerUseMaskChanged)

	def tunerUseMaskChanged(self, mask):
		config.hrtunerproxy.slotsinuse.setValue(mask)

def updateTunerInfo(value):
		HRTunerProxy_Setup.instance.populate()
if not config.hrtunerproxy.type.notifiers:
	config.hrtunerproxy.type.addNotifier(updateTunerInfo, initial_call = False)

def startssdp(dvbtype):
	discover = getdeviceinfo.discoverdata(dvbtype)
	device_uuid = discover['DeviceUUID']
	logger.info('Starting SSDP for %s, device_uuid: %s' % (dvbtype,device_uuid))
	local_ip_address = getIP()
	ssdp = SSDPServer()
	ssdp.register('local',
				  'uuid:{}::upnp:rootdevice'.format(device_uuid),
				  'upnp:rootdevice',
				  'http://{}:{}/device.xml'.format(local_ip_address,tunerports[dvbtype]))
	thread_ssdp = threading.Thread(target=ssdp.run, args=())
	thread_ssdp.daemon = True # Daemonize thread
	thread_ssdp.start()

def starthttpserver(dvbtype):
	logger.info('Starting HTTPServer for %s' % dvbtype)
	thread_http = threading.Thread(target=server.run, args=(dvbtype,))
	thread_http.daemon = True # Daemonize thread
	thread_http.start()

def HRTunerProxy_AutoStart(reason, session=None, **kwargs):
	if reason == 0:
		for type in tunerTypes:
			if path.exists('/etc/enigma2/%s.discover' % type):
				starthttpserver(type)
			if path.exists('/etc/enigma2/%s.device' % type):
				startssdp(type)
			if not path.exists('/etc/os-release'): # check if opendreambox image
				TunerMask()

def HRTunerProxy_SetupMain(session, **kwargs):
	session.open(HRTunerProxy_Setup)

def startHRTunerProxy_Setup(menuid):
	if menuid != "system":
		return []
	return [( _("HR-Tuner Proxy"), HRTunerProxy_SetupMain, "dvr_setup", None)]

def Plugins(**kwargs):
	screenwidth = getDesktop(0).size().width()
	if screenwidth and screenwidth == 1920:
		iconpic="plugin-hd.png"
	else:
		iconpic="plugin.png"
	return [PluginDescriptor(name = "HRTunerProxy",description = "Setup Enigma2 to act as HR Proxy Server", where = PluginDescriptor.WHERE_SESSIONSTART, fnc=HRTunerProxy_AutoStart, needsRestart=True),
			PluginDescriptor(name = "HRTunerProxy",description = "Setup Enigma2 to act as HR Proxy Server", icon=iconpic, where = PluginDescriptor.WHERE_PLUGINMENU, fnc=HRTunerProxy_SetupMain),
			PluginDescriptor(name = "HRTunerProxy",description = "Setup Enigma2 to act as HR Proxy Server", where = PluginDescriptor.WHERE_MENU,needsRestart = False, fnc=startHRTunerProxy_Setup)]
