import threading
import string
import random
import json
from os import path, remove, mkdir, rename, listdir, rmdir
from shutil import rmtree

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config, configfile, ConfigSubsection, ConfigSelection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from . import _, tunerTypes, tunerfolders, tunerports, getIP
from about import PlexDVRAPI_About
from enigma import getDesktop
from getLineup import getlineup, getBouquetsList
from getDeviceInfo import getdeviceinfo
from ssdp import SSDPServer
from server import server

config.plexdvrapi = ConfigSubsection()
config.plexdvrapi.bouquets_list = ConfigSelection(default = "all", choices = [('all', _('All'))] + getBouquetsList())

BaseURL = {}
FriendlyName = {}
TunerCount = {}
Source = {}
NoOfChannels = {}
choicelist = []

def TunerInfoDebug():
	for type in tunerTypes:
		print '[Plex DVR API] %s' % str(BaseURL[type]).replace('\n','')
		print '[Plex DVR API] %s' % str(FriendlyName[type]).replace('\n','')
		print '[Plex DVR API] %s' % str(Source[type]).replace('\n','')
		print '[Plex DVR API] %s' % str(TunerCount[type]).replace('\n','')
		print '[Plex DVR API] %s' % str(NoOfChannels[type]).replace('\n\n','')

def TunerInfo():
	global choicelist
	choicelist = []
	for type in tunerTypes:
		if path.exists('/www/%s/lineup_status.json' % tunerfolders[type]):
			remove('/www/%s/lineup_status.json' % tunerfolders[type])
		if path.exists('/www/%s/lineup.json' % tunerfolders[type]):
			remove('/www/%s/lineup.json' % tunerfolders[type])
		if path.exists('/www/%s/discover.json' % tunerfolders[type]):
			rename('/www/%s/discover.json' % tunerfolders[type], '/etc/enigma2/%s.discover' % type)
		if path.exists('/www/%s/device.xml' % tunerfolders[type]):
			rename('/www/%s/device.xml' % tunerfolders[type], '/etc/enigma2/%s.device' % type)
		if path.exists('/www/%s' % tunerfolders[type]) and not listdir('/www/%s' % tunerfolders[type]):
			rmdir('/www/%s' % tunerfolders[type])

		discover = getdeviceinfo.discoverdata(type)
		BaseURL[type] = 'BaseURL: %s\n' % str(discover["BaseURL"])
		FriendlyName[type] = 'FriendlyName: %s\n' % str(discover["FriendlyName"])
		TunerCount[type] = 'TunerCount: %s\n' % str(getdeviceinfo.tunercount(type))
		Source[type] = 'Source: %s\n' % str(tunerfolders[type]).title()
		NoOfChannels[type] = 'Channels: %s\n\n' % str(getlineup.noofchannels(type))

		if getdeviceinfo.tunercount(type) > 0 and getlineup.noofchannels(type) > 0:
			choicelist.append((type, str(tunerfolders[type]).title()))

TunerInfo()
TunerInfoDebug()
config.plexdvrapi.type = ConfigSelection(choices = choicelist)
print '[Plex DVR API] Using Tuner: %s' % str(config.plexdvrapi.type.value)

tunerTypes = []
for type in config.plexdvrapi.type.choices.choices:
	tunerTypes.append(type[0])

if path.exists('/www') and not listdir('/www'):
	rmdir('/www')

class PlexDVRAPI_Setup(ConfigListScreen, Screen):
	skin="""
	<screen position="center,center" size="600,325">
		<widget name="config" position="10,10" size="580,50" scrollbarMode="showOnDemand" />
		<widget name="information" position="10,70" size="580,185" font="Regular;22"/>
		<widget name="description" position="10,200" size="580,75" font="Regular;22" valign="bottom"/>
		<widget name="button_red" pixmap="skin_default/buttons/red.png" position="0,285" size="140,40" alphatest="on"/>
		<widget name="button_green" pixmap="skin_default/buttons/green.png" position="150,285" size="140,40" alphatest="on"/>
		<widget name="button_yellow" pixmap="skin_default/buttons/yellow.png" position="300,285" size="140,40" alphatest="on"/>
		<widget name="button_blue" pixmap="skin_default/buttons/blue.png" position="450,285" size="140,40" alphatest="on"/>
		<widget name="key_red" position="0,285" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>
		<widget name="key_green" position="150,285" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1"/>
		<widget name="key_yellow" position="300,285" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1"/>
		<widget name="key_blue" position="450,285" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1"/>
	</screen>"""

	def __init__(self, session, menu_path=""):
		instance = None
		Screen.__init__(self, session)
		if hasattr(config.usage, 'show_menupath'):
			screentitle =  _("Plex DVR API for Enigma2")
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
			title =  _("Plex DVR API for Enigma2")
			self.menu_path = ""
		Screen.setTitle(self, title)
		TunerInfo()
		TunerInfoDebug()

		self.savedval = config.plexdvrapi.type.value
		config.plexdvrapi.bouquets_list.setChoices([('all', _('All'))] + getBouquetsList())

		self.onChangedEntry = [ ]
		self.list = []
		self.list.append(getConfigListEntry(_('Tuner type to use'), config.plexdvrapi.type))
		self.list.append(getConfigListEntry(_('Bouquet to use'), config.plexdvrapi.bouquets_list))
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.populate)
		self["config"].list = self.list
		self["config"].l.setList(self.list)

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

		assert PlexDVRAPI_Setup.instance is None, "class InfoBar is a singleton class and just one instance of this class is allowed!"
		PlexDVRAPI_Setup.instance = self

		self.onLayoutFinish.append(self.populate)
		self.onClose.append(self.__onClose)

		if not self.populate in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.populate)

	def __onClose(self):
		PlexDVRAPI_Setup.instance = None

	def about(self):
		self.session.open(PlexDVRAPI_About, self.menu_path)

	def populate(self, answer=None):
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

		if getIP() == '0.0.0.0' or not config.plexdvrapi.type.value:
			if getIP() == '0.0.0.0':
				self["information"].setText(_('WARNING: No IP address found. Please make sure you are connected to your LAN via ethernet as Wi-Fi is not supported at this time.\n\nPress OK to exit.'))
			else:
				self["information"].setText(_('WARNING: It seems you have no tuners with channels setup on this device. Please perform a channels scan or run ABM.\n\nPress OK to exit.'))
			self["description"].hide()
			self["closeaction"].setEnabled(True)

		elif self["config"].getCurrent() is not None:
			type = config.plexdvrapi.type.value
			currentconfig = self["config"].getCurrent()[0]
			TunerInfo()
			self.label = (BaseURL[type]+FriendlyName[type]+Source[type]+TunerCount[type]+NoOfChannels[type])

			for types in tunerTypes:
				if path.exists('/etc/enigma2/%s.discover' % types):
					setup_exists = True

			if not path.exists('/etc/enigma2/%s.discover' % type):
				if getdeviceinfo.tunercount(type) < 2:
					self["information"].setText(_('WARNING: It seems you have a single tuner box. If the box is not left in Standby your Plex Server recordings WILL fail.'))
					self["description"].setText(_('Press OK to continue setting up this tuner.'))
					self.hinttext = _('Press GREEN to save your configuration files.')
					self["okaction"].setEnabled(True)
					self["key_green"].setText(_("Save"))
					self["key_yellow"].setText("")
				else:
					if not setup_exists:
						self["information"].setText(_('Please note: To use the DVR feature in Plex Server you need to be a Plex Pass user. For more information about Plex Pass see https://www.plex.tv/features/plex-pass'))
					else:
						self["information"].setText(_('Please note: To use another tuner type you need to setup/have another Plex Server. Are you sure you want to continue?'))
					if currentconfig == _('Tuner type to use'):
						self["description"].setText(_('Press OK to continue setting up this tuner or press LEFT / RIGHT to select a different tuner type.'))
						self.hinttext = _('Press LEFT / RIGHT to select a different tuner type.')
					else:
						self["description"].setText(_('Press OK to continue setting up this tuner or select a different tuner type.'))
						self.hinttext = _('Press LEFT / RIGHT to select a different bouquet.')
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
		type = config.plexdvrapi.type.value
		if path.exists('/etc/enigma2/%s.discover' % type):
			self.session.openWithCallback(self.cleanconfirm, MessageBox,text = _("Do you really want to remove the files for this tuner type? Doing so will cause the DVR in plex to be none functional."), type = MessageBox.TYPE_YESNO)

	def cleanconfirm(self, answer):
		if answer is not None and answer and self["config"].getCurrent() is not None:
			type = config.plexdvrapi.type.value
			print '[Plex DVR API] Deleting files for %s' % type
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
		if self.savedval != config.plexdvrapi.type.value and path.exists('/etc/enigma2/%s.device' % self.savedval):
			self.session.openWithCallback(self.saveconfirm, MessageBox,text = _("It seems you have already set up another tuner. Plex Server can only support one tuner type. To use this additional tuner type you will need to setup another Plex Server. Do you want to continue creating the files?"), type = MessageBox.TYPE_YESNO)
		else:
			self.saveconfirm(True)

	def saveconfirm(self, answer):
		if answer is not None and answer and self["config"].getCurrent() is not None:
			type = config.plexdvrapi.type.value
			newsetup = False
			if not path.exists('/etc/enigma2/%s.discover' % type):
				newsetup = True
			print '[Plex DVR API] Creating files for %s' % type
			if not path.exists('/etc/enigma2/%s.device' % self.savedval):
				getdeviceinfo.write_device_xml(dvbtype=type)
				config.plexdvrapi.type.save()
			config.plexdvrapi.bouquets_list.save()
			configfile.save()
			getdeviceinfo.write_discover(dvbtype=type)
			if self.savedval != config.plexdvrapi.type.value and path.exists('/etc/enigma2/%s.device' % self.savedval) or newsetup:
				self.session.openWithCallback(self.rebootconfirm, MessageBox,text = _("Files created. Please restart enigma2 and then you should be able to add this STB to Plex Server.\n\nDo you want to restart now?"), type = MessageBox.TYPE_YESNO)
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

def updateTunerInfo(value):
		PlexDVRAPI_Setup.instance.populate()
if not config.plexdvrapi.type.notifiers:
	config.plexdvrapi.type.addNotifier(updateTunerInfo, initial_call = False)

def startssdp(dvbtype):
	discover = getdeviceinfo.discoverdata(dvbtype)
	device_uuid = discover['DeviceUUID']
	print '[Plex DVR API] Starting SSDP for %s, device_uuid: %s' % (dvbtype,device_uuid)
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
	print '[Plex DVR API] Starting HTTPServer for %s' % dvbtype
	thread_http = threading.Thread(target=server.run, args=(dvbtype,))
	thread_http.daemon = True # Daemonize thread
	thread_http.start()

def PlexDVRAPI_AutoStart(reason, session=None, **kwargs):
	if reason == 0:
		for type in tunerTypes:
			if path.exists('/etc/enigma2/%s.discover' % type):
				starthttpserver(type)
			if path.exists('/etc/enigma2/%s.device' % type):
				startssdp(type)

def PlexDVRAPI_SetupMain(session, **kwargs):
	session.open(PlexDVRAPI_Setup)

def startPlexDVRAPI_Setup(menuid):
	if menuid != "system":
		return []
	return [( _("Plex DVR API"), PlexDVRAPI_SetupMain, "plexdvr_setup", None)]

def Plugins(**kwargs):
	screenwidth = getDesktop(0).size().width()
	if screenwidth and screenwidth == 1920:
		iconpic="plugin-hd.png"
	else:
		iconpic="plugin.png"
	return [PluginDescriptor(name = "Plex DVR API",description = "Setup Enigma2 to link with a Plex Server DVR", where = PluginDescriptor.WHERE_SESSIONSTART, fnc=PlexDVRAPI_AutoStart, needsRestart=True),
			PluginDescriptor(name = "Plex DVR API",description = "Setup Enigma2 to link with a Plex Server DVR", icon=iconpic, where = PluginDescriptor.WHERE_PLUGINMENU, fnc=PlexDVRAPI_SetupMain),
			PluginDescriptor(name = "Plex DVR API",description = "Setup Enigma2 to link with a Plex Server DVR", where = PluginDescriptor.WHERE_MENU,needsRestart = False, fnc=startPlexDVRAPI_Setup)]
