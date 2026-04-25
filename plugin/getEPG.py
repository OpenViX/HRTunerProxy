from __future__ import print_function
from __future__ import absolute_import

import time
import six
try:
	from xml.sax.saxutils import escape
except:
	def escape(text):
		return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
from sys import modules

from enigma import eEPGCache
from Components.config import config

from . import tunerports, getHost
from .getLineup import getLineup


def _xml(text):
	if text is None:
		return ""
	return escape(six.text_type(text), {'"': "&quot;", "'": "&apos;"})


def _xmltv_time(timestamp):
	try:
		return time.strftime("%Y%m%d%H%M%S %z", time.localtime(int(timestamp)))
	except:
		return ""


class getEPG:
	def __init__(self, dvbtype, bouquet_name):
		self.dvbtype = dvbtype
		self.bouquet_name = bouquet_name
		self.channels = getLineup(bouquet=bouquet_name).output()
		self.epgcache = eEPGCache.getInstance()

	def _filtered_channels(self):
		output = []
		for channel in self.channels:
			if self.dvbtype == "iptv" and "http" not in channel[2]:
				continue
			if self.dvbtype in ("multi", "iptv", channel[3]):
				output.append(channel)
		return output

	def _events(self, service_ref):
		if not self.epgcache:
			return []
		try:
			return self.epgcache.lookupEvent(['IBDTSERN', (service_ref, 0, -1, -1)])
		except Exception as e:
			if config.hrtunerproxy.debug.value:
				print("[HRTunerProxy] EPG lookup failed for %s: %s" % (service_ref, e))
			return []

	def xmltv(self):
		host = getHost()
		url = "http://%s:%s/epg.xml" % (host, tunerports[self.dvbtype])
		lines = [
			'<?xml version="1.0" encoding="UTF-8"?>',
			'<tv generator-info-name="HRTunerProxy" generator-info-url="%s">' % _xml(url)
		]

		channels = self._filtered_channels()
		for channel_number, channel_name, service_ref, channel_type in channels:
			lines.append('  <channel id="%s">' % _xml(channel_number))
			lines.append('    <display-name>%s</display-name>' % _xml(channel_name))
			lines.append('    <display-name>%s</display-name>' % _xml(channel_number))
			lines.append('  </channel>')

		for channel_number, channel_name, service_ref, channel_type in channels:
			if "http" in service_ref:
				continue
			for event in self._events(service_ref):
				if not event or len(event) < 5:
					continue
				begin = int(event[1])
				duration = int(event[2])
				stop = begin + duration
				title = event[3] or ""
				short_description = event[4] if len(event) > 4 else ""
				extended_description = event[5] if len(event) > 5 else ""

				if not title or duration <= 0:
					continue

				lines.append('  <programme start="%s" stop="%s" channel="%s">' % (_xmltv_time(begin), _xmltv_time(stop), _xml(channel_number)))
				lines.append('    <title>%s</title>' % _xml(title))
				if short_description:
					lines.append('    <sub-title>%s</sub-title>' % _xml(short_description))
				if extended_description:
					lines.append('    <desc>%s</desc>' % _xml(extended_description))
				lines.append('  </programme>')

		lines.append('</tv>')
		return "\n".join(lines)


def epgdata(dvbtype='', bouquet_name=''):
	epg = getEPG(dvbtype, bouquet_name)
	return epg.xmltv()


getepg = modules[__name__]
