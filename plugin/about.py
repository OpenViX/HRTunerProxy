from os import path
from sys import modules

from . import _, getVersion, isDreamOS
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen


class HRTunerProxy_About(Screen):
	if isDreamOS: # check if DreamOS image
		skin = "%s/skins/dreamos_about.xml" % (path.dirname(modules[__name__].__file__))
	else:
		skin = "%s/skins/about.xml" % (path.dirname(modules[__name__].__file__))
	f = open(skin, "r")
	skin = f.read()
	f.close()

	def __init__(self, session, menu_path=""):
		Screen.__init__(self, session)
		if hasattr(config.usage, 'show_menupath'):
			screentitle = _("About HR-Tuner Proxy")
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
			title = _("About HR-Tuner Proxy")
		Screen.setTitle(self, title)

		self["about"] = Label()
		self["actions"] = ActionMap(["SetupActions"],
		{
			"red": self.close,
			"cancel": self.close,
			"menu": self.close,
		}, -2)

		self["key_red"] = Button(_("Close"))
		self["button_red"] = Pixmap()

		credit = _("HR-Tuner Proxy for Enigma2 %s(c) 2018\n") % getVersion()
		credit += "Andrew Blackburn & Rowland Huevos\n"
		credit += "https://github.com/OpenViX/HRTunerProxy\n\n"
		credit += _("Application credits:\n")
		credit += "- AndyBlac (main developer)\n"
		credit += "- Huevos (main developer)\n"
		credit += "- rossi2000 (developer)\n\n"
		credit += _("Sources credits:\n")
		credit += "- FidoFuz (helped us with JSON tags)\n"
		credit += "- PiGeon(CZ) (helped us with debugging OpenDreamBox)\n\n"
		credit += _("Translation credits:\n")
		credit += "- patrickf95 / captain (German)\n"
		credit += "- PiGeon(CZ) (Czech)\n"
		credit += "- Rob van der Does(NL) (Dutch)\n"
		credit += "- Pakorro (Spanish)"
		self["about"].setText(credit)
