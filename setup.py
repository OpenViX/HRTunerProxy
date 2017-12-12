from distutils.core import setup
import setup_translate

pkg = 'SystemPlugins.HRTunerProxy'
setup (name = 'enigma2-plugin-systemplugins-hrtunerproxy',
       version = '3.0',
       description = 'HRTunerProxy',
       package_dir = {pkg: 'plugin'},
       packages = [pkg],
       package_data = {pkg: 
           ['plugin.png', 'plugin-hd.png', 'locale/*/LC_MESSAGES/*.mo', 'locale/*/LC_MESSAGES/*.po']},
       cmdclass = setup_translate.cmdclass, # for translation
      )
