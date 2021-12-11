from __future__ import print_function

import re
import json
try:
	from urllib.parse import unquote
except:
	from urllib import unquote
from os import path, mkdir
from sys import modules

from enigma import eServiceReference
from Components.config import config


class getLineup:
	def __init__(self, duplicates=False, bouquet=None, bouquet_names_only=False):
		self.duplicates = duplicates
		self.bouquet_names_only = bouquet_names_only
		self.refs_added = []
		if hasattr(eServiceReference, 'isNumberedMarker'):
			self.isNumberedMarker = eServiceReference.isNumberedMarker
		else:
			self.isNumberedMarker = 256
		if hasattr(eServiceReference, 'isInvisible'):
			self.isInvisible = eServiceReference.isInvisible
		else:
			self.isInvisible = 512
		self.path = "/etc/enigma2/"
		self.db = "lamedb"
		self.tv_index = "bouquets.tv"
		self.channelNames = {} # key SID:TSID:ONID:NAMESPACE in hex
		self.bouquets_filenames = []
		self.bouquets_flags = {}
		self.bouquets_names = [] # contains tuple pairs, e.g. [(filename1, bouquet_name1), (filename2, bouquet_name2)]
		self.channel_numbers_names_and_refs = []
		self.video_allowed_types = [1, 4, 5, 17, 22, 24, 25, 27, 31, 135]
		if not self.bouquet_names_only:
			self.read_services()
		if bouquet:
			if bouquet != 'all':
				self.bouquets_filenames.append(bouquet)
				self.bouquets_flags[bouquet] = (eServiceReference.isDirectory | eServiceReference.mustDescent | eServiceReference.canDescent) # default bouquet folder (7)
			else:
				self.read_tv_index()
			self.read_tv_bouquets()

	def read_services(self):
		try:
			db = open(self.path + self.db, "r")
		except Exception as e:
			return

		content = db.read()
		db.close()

		srv_start = content.find("services\n")
		srv_stop = content.rfind("end\n")

		srv_blocks = content[srv_start + 9:srv_stop].strip().split("\n")

		for i in range(0, len(srv_blocks) // 3):
			service_reference = srv_blocks[i * 3].strip().split(":")
			service_name = srv_blocks[(i * 3) + 1].strip()

			if len(service_reference) != 6 and len(service_reference) != 7:
				continue

			sid = int(service_reference[0], 16)
			namespace = int(service_reference[1], 16)
			tsid = int(service_reference[2], 16)
			onid = int(service_reference[3], 16)

			key = "%x:%x:%x:%x" % (sid, tsid, onid, namespace)
			self.channelNames[key] = service_name

	def read_tv_index(self):
		try:
			bouquets = open(self.path + self.tv_index, "r")
		except Exception as e:
			return

		content = bouquets.read()
		bouquets.close()

		for row in content.split("\n"):
			result = re.match("^.*FROM BOUQUET \"(.+)\" ORDER BY.*$", row) or re.match("[#]SERVICE[:] (?:[0-9a-f]+[:])+([^:]+[.](?:tv|radio))$", row, re.IGNORECASE)
			if result is None:
				continue
			self.bouquets_filenames.append(result.group(1))
			bouquet_flags = (eServiceReference.isDirectory | eServiceReference.mustDescent | eServiceReference.canDescent) # default bouquet folder (7)
			if result.group(0).startswith("#SERVICE "):
				service_ref = result.group(0)[9:].strip()
				service_ref_split = service_ref.split(":")
				if len(service_ref_split) > 9:
					bouquet_flags = int(service_ref_split[1])
			self.bouquets_flags[result.group(1)] = bouquet_flags

	def read_tv_bouquets(self):
		channel_number = 0
		for filename in self.bouquets_filenames:
			name = ''
			try:
				bouquet = open(self.path + filename, "r")
			except Exception as e:
				continue

			content = bouquet.read()
			bouquet.close()

			content_split = content.split("\n")
			content_len = len(content_split)
			for idx in range(content_len):
				row = content_split[idx]
				channel_name = ''
				if name == '' and row.startswith("#NAME "):
					if not (self.bouquets_flags[filename] & self.isInvisible): # not invisible bouquet
						name = row.strip()[6:]
						self.bouquets_names.append((filename, name))
						if self.bouquet_names_only:
							break
				elif row.startswith("#SERVICE "):
					if content_len > (idx + 1) and content_split[idx + 1].startswith("#DESCRIPTION "): # check if channel name exists in bouquets file
						channel_name = content_split[idx + 1].strip()[13:]
					service_ref = row[9:].strip()
					service_ref_split = service_ref.split(":")
					if len(service_ref_split) < 10:
						print("[HRTunerProxy] [read_tv_bouquets] Error in %s" % filename)
						continue
					service_flags = int(service_ref_split[1])
					if service_flags == (eServiceReference.mustDescent | eServiceReference.canDescent | eServiceReference.isGroup): # alternatives (134)
						alternative = self.alternatives(row)
						if alternative is None: # something must be wrong with alternatives group
							channel_number += 1
							continue
						service_ref = alternative["service_ref"]
						service_ref_split = alternative["service_ref_split"]
						service_flags = alternative["service_flags"]
					if service_flags == eServiceReference.isMarker: # standard marker (64), skip
						continue
					channel_number += 1 # everything below this point increments the channel number
					if (service_flags & self.isNumberedMarker): # numbered marker (256)
						continue
					if (self.bouquets_flags[filename] & self.isInvisible): # invisible bouquet (512)
						continue
					if int(service_ref_split[0]) not in (1, 4097): # not a regular service. Might be IPTV.
						continue
					if service_flags != 0: # not a normal service that can be fed directly into the "play"-handler.
						continue
					if int(service_ref_split[2], 16) not in self.video_allowed_types:
						continue
					if service_ref in self.refs_added and not self.duplicates:
						continue
					if "http" not in row: # not http stream
						self.refs_added.append(service_ref)
					sid = int(service_ref_split[3], 16)
					tsid = int(service_ref_split[4], 16)
					onid = int(service_ref_split[5], 16)
					namespace = int(service_ref_split[6], 16)
					key = "%x:%x:%x:%x" % (sid, tsid, onid, namespace)
					if key not in self.channelNames and ("http" not in row or ("http" in row and channel_name == "")):
						continue
					if channel_name == "":
						channel_name = self.channelNames[key]
					if len(service_ref_split) > 10 and "http" in service_ref_split[10]: # http stream
						http_link = unquote(service_ref_split[10].strip())
						self.channel_numbers_names_and_refs.append((str(channel_number), channel_name, http_link, "iptv"))
						continue
					service_ref_clean = ':'.join(service_ref_split[:10]) + ":"
					self.channel_numbers_names_and_refs.append((str(channel_number), channel_name, service_ref_clean, self.tunerType(namespace)))

	def tunerType(self, namespace):
		if (namespace >> 16) == 0xFFFF:
			return "DVB-C"
		if (namespace >> 16) == 0xEEEE:
			return "DVB-T"
		return "DVB-S"

	def alternatives(self, service_line):
		result = re.match("^.*FROM BOUQUET \"(.+)\" ORDER BY.*$", service_line)
		if result is not None:
			try:
				alternative = open(self.path + result.group(1), "r")
			except Exception as e:
				return
			content = alternative.read()
			alternative.close()

			for row in content.split("\n"):
				if row.startswith("#SERVICE "):
					if "http" in row:
						continue
					service_ref = row[9:].strip()
					service_ref_split = service_ref.split(":")
					if len(service_ref_split) < 10:
						print("[HRTunerProxy] [alternatives] Error in %s" % result.group(1))
						continue
					if int(service_ref_split[0], 16) != 1: # not a regular service. Might be IPTV.
						continue
					service_flags = int(service_ref_split[1])
					if service_flags == 0: # normal service that can be fed directly into the "play"-handler.
						return {"service_ref": service_ref, "service_ref_split": service_ref_split, "service_flags": service_flags}

	def output(self):
		return self.channel_numbers_names_and_refs

	def createJSON(self, ip="0.0.0.0", port=8001, dvb_type="DVB-S"):
		output = self.output()
		self.data_tmp = {}
		self.lineup = []

		for c_n_r in output:
			if dvb_type == "iptv" and "http" not in c_n_r[2]:
				continue
			if dvb_type in ('multi', 'iptv', c_n_r[3]):
				self.data_tmp = {}
				self.data_tmp['GuideNumber'] = '%s' % c_n_r[0]
				self.data_tmp['GuideName'] = '%s' % c_n_r[1]
				if "http" in c_n_r[2]:
					self.data_tmp['URL'] = c_n_r[2]
				else:
					self.data_tmp['URL'] = 'http://%s:%d/%s' % (ip, port, c_n_r[2])
				self.lineup.append(self.data_tmp)
		return self.lineup

	def getBouquetsList(self):
		return self.bouquets_names


def noofchannels(dvb_type, bouquet):
	return len(lineupdata(dvbtype=dvb_type, bouquet_name=bouquet))


def lineupdata(ipinput='0.0.0.0', dvbtype='', bouquet_name=''):
	channel_numbers = getLineup(bouquet=bouquet_name)
	return channel_numbers.createJSON(ip=ipinput, dvb_type=dvbtype)


def getBouquetsList():
	lineup = getLineup(bouquet_names_only=True, bouquet='all')
	return lineup.getBouquetsList()


getlineup = modules[__name__]
