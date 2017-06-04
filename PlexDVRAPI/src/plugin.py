import threading
import string
import random
import json
from os import path, remove

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from . import _, tunerTypes, tunerfolders, tunerports, getIP
from about import PlexDVRAPI_About
from getLineup import getlineup
from getDeviceInfo import getdeviceinfo
from getLineupStatus import getlineupstatus
# from ssdp import SSDPServer
from server import server


class PlexDVRAPI_Setup(Screen):
	skin="""
	<screen position="center,center" size="600,500">
		<widget name="InfoScrollLabel" position="10,10" size="580,430" font="Regular;22"/>
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,460" size="140,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/green.png" position="150,460" size="140,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="300,460" size="140,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/blue.png" position="450,460" size="140,40" alphatest="on"/>
		<widget name="key_red" position="0,460" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>
		<widget name="key_green" position="150,460" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1"/>
		<widget name="key_yellow" position="300,460" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1"/>
		<widget name="key_blue" position="450,460" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1"/>
	</screen>"""

	def __init__(self, session, menu_path=""):
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
		Screen.setTitle(self, title)

		self["InfoScrollLabel"] = ScrollLabel()
		self["actions"] = ActionMap(['ColorActions','OkCancelActions', 'DirectionActions'],
									{
									"cancel": self.close,
									"red": self.close,
									"green": self.save,
									"yellow": self.cleanfiles,
									"blue": self.about,
									"up": self["InfoScrollLabel"].pageUp,
									"down": self["InfoScrollLabel"].pageDown,
									}, -2)
		self["actions"].setEnabled(False)

		self["okaction"] = ActionMap(['OkCancelActions'],
									{
									"ok": self.ok,
									}, -2)
		self["okaction"].setEnabled(False)

		self["closeaction"] = ActionMap(['OkCancelActions'],
									{
									"ok": self.close,
									}, -2)
		self["closeaction"].setEnabled(False)

		self["key_red"] = Button(_("Close"))
		self["key_red"].hide()
		self["key_green"] = Button()
		self["key_green"].hide()
		self["key_yellow"] = Button()
		self["key_yellow"].hide()
		self["key_blue"] = Button(_("About"))

		self.onLayoutFinish.append(self.populate)

	def about(self):
		self.session.open(PlexDVRAPI_About, self.menu_path)

	def cleanfiles(self):
		self.session.openWithCallback(self.cleanconfirm, MessageBox,text = _("Do you really want to reset?,\n doing so will cause the DVR in plex to be none fuctional,\nyou will have to remove and re-add the DVR."), type = MessageBox.TYPE_YESNO)

	def cleanconfirm(self, answer):
		if answer is not None and answer:
			for type in tunerTypes:
				if path.exists('/www/%s/discover.json' % tunerfolders[type]):
					remove('/www/%s/discover.json' % tunerfolders[type])
				if path.exists('/www/%s/lineup_status.json' % tunerfolders[type]):
					remove('/www/%s/lineup_status.json' % tunerfolders[type])
				if path.exists('/www/%s/lineup.json' % tunerfolders[type]):
					remove('/www/%s/lineup.json' % tunerfolders[type])
			self.populate()

	def populate(self, answer=None):
		BaseURL = {}
		FriendlyName = {}
		TunerCount = {}
		Source = {}
		NoOfChannels = {}
		self.label = []

		for type in tunerTypes:
			self.discover = getdeviceinfo.deviceinfo(type)
			self.lineupstatus = getlineupstatus.lineupstatus(type)
			BaseURL[type] = 'BaseURL: %s\n' % str(self.discover[type]["BaseURL"])
			FriendlyName[type] = 'FriendlyName: %s\n' % str(self.discover[type]["FriendlyName"])
			TunerCount[type] = 'TunerCount: %s\n' % str(self.discover[type]["TunerCount"])
			Source[type] = 'Source: %s\n' % str(tunerfolders[type]).title()
			NoOfChannels[type] = 'Channels: %s\n\n' % str(self.discover[type]['NumChannels'])
			if self.discover[type]["TunerCount"] > 1 and self.discover[type]['NumChannels'] > 0 and type != "multi":
				self.label.append(BaseURL[type]+FriendlyName[type]+Source[type]+TunerCount[type]+NoOfChannels[type])
			print '[Plex DVR API] %s' % str(BaseURL[type]).replace('\n','')
			print '[Plex DVR API] %s' % str(FriendlyName[type]).replace('\n','')
			print '[Plex DVR API] %s' % str(Source[type]).replace('\n','')
			print '[Plex DVR API] %s' % str(TunerCount[type]).replace('\n','')
			print '[Plex DVR API] %s' % str(NoOfChannels[type]).replace('\n\n','\n')

			if not path.exists('/www/%s/discover.json' % tunerfolders[type]) or getIP() == '0.0.0.0' or self.discover[type]["TunerCount"] < 2:
				self["key_red"].hide()
				self["key_green"].hide()
				self["key_yellow"].hide()
				self["key_blue"].hide()
				if getIP() == '0.0.0.0':
					self["InfoScrollLabel"].setText(_('No IP address found, please make sure you are connected to your LAN via ethernet, wifi is not supported at this time.\n\nPress OK to close'))
					self["closeaction"].setEnabled(True)
				elif self.discover[type]["TunerCount"] < 2:
					self["InfoScrollLabel"].setText(_('WARNING: It seems you have a single tuner box, if the box is not left in Standby your Plex recordings WILL fail.\n\nPress OK to contine'))
					self["okaction"].setEnabled(True)
					self["key_green"].setText(_("Create"))
					self["key_yellow"].setText("")
				else:
					self["InfoScrollLabel"].setText(_('Please note: To use the DVR feature in Plex, you need to be a Plex Pass user.\nFor more information about Plex Pass see https://www.plex.tv/features/plex-pass\n\nPress OK to contine'))
					self["okaction"].setEnabled(True)
					self["key_green"].setText(_("Create"))
					self["key_yellow"].setText("")
			else:
				self["key_green"].setText(_('Update'))
				self["key_yellow"].setText(_("Reset DVR"))
				self.ok()

	def ok(self):
		self["okaction"].setEnabled(False)
		self["actions"].setEnabled(True)
		self["InfoScrollLabel"].setText(''.join(self.label))
		self["key_red"].show()
		self["key_green"].show()
		self["key_yellow"].show()
		self["key_blue"].show()

	def save(self):
		for type in tunerTypes:
			if self.discover[type]["TunerCount"] > 1 and self.discover[type]['NumChannels'] > 0:
				print '[Plex DVR API] Creating JSON files for %s' % type
				getdeviceinfo.write_discover(writefile='/www/%s/discover.json' % tunerfolders[type], dvbtype=type)
				getdeviceinfo.write_device_xml(writefile='/www/%s/device.xml' % tunerfolders[type], dvbtype=type)
				getlineupstatus.write_lineupstatus(writefile='/www/%s/lineup_status.json' % tunerfolders[type], dvbtype=type)
				getlineup.write_lineup(writefile='/www/%s/lineup.json' % tunerfolders[type], ipinput=getIP(), dvbtype=type)
		self.session.openWithCallback(self.rebootconfirm, MessageBox,text = _("Files created, Please reboot and then you should be able to add this STB to Plex DVR.\nDo you want to reboot now ?"), type = MessageBox.TYPE_YESNO)

	def rebootconfirm(self, answer):
		if answer is not None and answer:
			from enigma import quitMainloop
			quitMainloop(2)

# def startssdp(dvbtype):
# 	discover = getdeviceinfo.deviceinfo(dvbtype)
# 	device_uuid = discover[dvbtype]['DeviceUUID']
# 	print '[Plex DVR API] Starting SSDP for %s, device_uuid: %s' % (dvbtype,device_uuid)
# 	local_ip_address = getIP()
# 	ssdp = SSDPServer()
# 	ssdp.register('local',
# 				  'uuid:{}::upnp:rootdevice'.format(device_uuid),
# 				  'upnp:rootdevice',
# 				  'http://{}:{}/device.xml'.format(local_ip_address,tunerports[dvbtype]))
# 	thread_ssdp = threading.Thread(target=ssdp.run, args=())
# 	thread_ssdp.daemon = True # Daemonize thread
# 	thread_ssdp.start()

def starthttpserver(dvbtype):
	print '[Plex DVR API] Starting HTTPServer for %s' % dvbtype
	thread_http = threading.Thread(target=server.run, args=(dvbtype,))
	thread_http.daemon = True # Daemonize thread
	thread_http.start()


def PlexDVRAPI_AutoStart(reason, session=None, **kwargs):
	if reason == 0:
		for type in tunerTypes:
			discover = getdeviceinfo.deviceinfo(type)
			if discover[type]["TunerCount"] > 0 and discover[type]['NumChannels'] > 0:
				if path.exists('/www/%s/discover.json' % tunerfolders[type]):
					starthttpserver(type)
				# if path.exists('/www/%s/device.xml' % tunerfolders[type]):
				# 	startssdp(type)

def PlexDVRAPI_SetupMain(session, **kwargs):
	session.open(PlexDVRAPI_Setup)

def startPlexDVRAPI_Setup(menuid):
	if menuid != "system":
		return []
	return [( _("Plex DVR"), PlexDVRAPI_SetupMain, "plexdvr_setup", None)]

def Plugins(**kwargs):
	return [PluginDescriptor(name = "Plex DVR API for Enigma2",description = "Setup Enigma2 for link with Plex DVR API", where = PluginDescriptor.WHERE_SESSIONSTART, fnc=PlexDVRAPI_AutoStart, needsRestart=True),
			PluginDescriptor(name = "Plex DVR API for Enigma2",description = "Setup Enigma2 for link with Plex DVR API", icon="plugin.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=PlexDVRAPI_SetupMain),
			PluginDescriptor(name = "Plex DVR API for Enigma2",description = "Setup Enigma2 for link with Plex DVR API", where = PluginDescriptor.WHERE_MENU,needsRestart = False, fnc=startPlexDVRAPI_Setup)]
