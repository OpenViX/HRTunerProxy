from . import _

from Screens.Screen import Screen

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText

PLUGIN_VERSION = '2.2'

class PlexDVRAPI_About(Screen):
	skin="""
	<screen position="center,center" size="600,500">
		<widget name="about" position="10,10" size="580,430" font="Regular;22"/>
		<widget name="key_red" position="0,460" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,460" size="140,40" alphatest="on"/>
	</screen>"""

	def __init__(self, session, menu_path=""):
		Screen.__init__(self, session)
		if hasattr(config.usage, 'show_menupath'):
			screentitle =  _("About Plex DRV API")
			if config.usage.show_menupath.value == 'large':
				menu_path += screentitle
				title = menu_path
				self["menu_path_compressed"] = StaticText("")
			elif config.usage.show_menupath.value == 'small':
				title = screentitle
				self["menu_path_compressed"] = StaticText(menu_path + " >" if not menu_path.endswith(' / ') else menu_path[:-3] + " >" or "")
			else:
				title = screentitle
				self["menu_path_compressed"] = StaticText("")
		else:
			title =  _("About Plex DRV API")
		Screen.setTitle(self, title)

		self["about"] = Label()
		self["actions"] = ActionMap(["SetupActions"],
		{
			"red": self.close,
			"cancel": self.close,
			"menu": self.close,
		}, -2)

		self["key_red"] = Button(_("Close"))

		credit = "Plex DVR API for Enigma2 %s (c) 2017 \nAndrew Blackburn & Rowland Huevos\n" % PLUGIN_VERSION
		credit += "http://github.com/openvix\n"
		credit += "Application credits:\n"
		credit += "- AndyBlac (main developer)\n"
		credit += "- Huevos (main developer)\n"
		credit += "- Rossi2000 (developer)\n\n"
		credit += "Sources credits:\n"
		credit += "- FidoFuz (helped us with JSON tags)\n\n"
		credit += "Translation credits:\n"
		credit += "- patrickf95 / captain (German)\n"
		credit += "- PiGeonCZ (Czech)\n"
		credit += "- Pakorro (Spanish)"
		self["about"].setText(credit)
