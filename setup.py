from distutils.core import setup
import setup_translate

pkg = 'SystemPlugins.HRTunerProxy'
setup(name='enigma2-plugin-systemplugins-hrtunerproxy',
       version='3.5',
       description='HRTunerProxy',
       long_description='Setup Enigma2 to act as HR-Tuner Proxy',
       author='AndyBlac & Huevos',
       url='https://github.com/OpenViX/HRTunerProxy',
       package_dir={pkg: 'plugin'},
       packages=[pkg],
       package_data={pkg:
           ['plugin.png', 'plugin-hd.png', 'skins/*.xml', 'locale/*/LC_MESSAGES/*.mo', 'locale/*/LC_MESSAGES/*.po']},
       cmdclass=setup_translate.cmdclass, # for translation
      )
