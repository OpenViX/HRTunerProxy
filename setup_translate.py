# Language extension for distutils Python scripts. Based on this concept:
# http://wiki.maemo.org/Internationalize_a_Python_application
from distutils import cmd
from distutils.command.build import build as _build
import os

class build_trans(cmd.Command):
	description = 'Compile .po files into .mo files'
	def initialize_options(self):
		pass

	def finalize_options(self):
		pass

	def run(self):
		s = os.path.join('plugin', 'locale')
		for lang in os.listdir(s):
			lc = os.path.join(s, lang, 'LC_MESSAGES')
			if os.path.isdir(lc):
				for f in os.listdir(lc):
					if f.endswith('.po'):
						src = os.path.join(lc, f)
						dest = os.path.join(lc, f[:-2] + 'mo')
						print "Language compile %s -> %s" % (src, dest)
						if os.system("msgfmt '%s' -o '%s'" % (src, dest)) != 0:
							raise Exception, "Failed to compile: " + src

class build(_build):
	sub_commands = _build.sub_commands + [('build_trans', None)]
	def run(self):
		_build.run(self)

cmdclass = {
	'build': build,
	'build_trans': build_trans,
}

