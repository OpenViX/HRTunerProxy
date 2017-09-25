import re
import json
from os import path, mkdir
from sys import modules

from enigma import eServiceReference
from Components.config import config

from . import tunerfolders

class getLineup:
	def __init__(self, duplicates = False, single_bouquet = 'all'):
		self.duplicates = duplicates
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
		self.bouquets_names = [] # contains tuple pairs, e.g. [(filename1, bouquet_name1), (filename1, bouquet_name1)]
		self.channel_numbers_names_and_refs = []
		self.video_allowed_types = [1, 4, 5, 17, 22, 24, 25, 27, 135]
		self.read_services()
		if single_bouquet != 'all':
			self.bouquets_filenames.append(single_bouquet)
			self.bouquets_flags[single_bouquet] = (eServiceReference.isDirectory|eServiceReference.mustDescent|eServiceReference.canDescent) # default bouquet folder (7)
		else:
			self.read_tv_index()
		self.read_tv_bouquets()

	def read_services(self):
		try:
			db = open(self.path + self.db, "r")
		except Exception, e:
			return

		content = db.read()
		db.close()

		srv_start = content.find("services\n")
		srv_stop = content.rfind("end\n")

		srv_blocks = content[srv_start + 9:srv_stop].strip().split("\n")

		for i in range(0, len(srv_blocks)/3):
			service_reference = srv_blocks[i*3].strip().split(":")
			service_name = srv_blocks[(i*3)+1].strip()

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
		except Exception, e:
			return

		content = bouquets.read()
		bouquets.close()

		for row in content.split("\n"):
			result = re.match("^.*FROM BOUQUET \"(.+)\" ORDER BY.*$", row) or re.match("[#]SERVICE[:] (?:[0-9a-f]+[:])+([^:]+[.](?:tv|radio))$", row, re.IGNORECASE)
			if result is None:
				continue
			self.bouquets_filenames.append(result.group(1))
			bouquet_flags = (eServiceReference.isDirectory|eServiceReference.mustDescent|eServiceReference.canDescent) # default bouquet folder (7)
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
			except Exception, e:
				continue

			content = bouquet.read()
			bouquet.close()

			for row in content.split("\n"):
				if name == '' and row.startswith("#NAME "):
					if not (self.bouquets_flags[filename] & self.isInvisible): # not invisible bouquet
						name = row.strip()[6:]
						self.bouquets_names.append((filename, name))
				elif row.startswith("#SERVICE "):
					if "http" in row:
						channel_number += 1
						continue
					service_ref = row[9:].strip()
					service_ref_split = service_ref.split(":")
					if len(service_ref_split) < 10:
						print "[Plex DVR API] [read_tv_bouquets] Error in %s" % filename
						continue
					service_flags = int(service_ref_split[1])
					if service_flags == (eServiceReference.mustDescent|eServiceReference.canDescent|eServiceReference.isGroup): # alternatives (134)
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
					if int(service_ref_split[0], 16) != 1: # not a regular service. Might be IPTV.
						continue
					if service_flags != 0: # not a normal service that can be fed directly into the "play"-handler.
						continue
					if int(service_ref_split[2], 16) not in self.video_allowed_types:
						continue
					if service_ref in self.refs_added and not self.duplicates:
						continue
					self.refs_added.append(service_ref)
					sid = int(service_ref_split[3], 16)
					tsid = int(service_ref_split[4], 16)
					onid = int(service_ref_split[5], 16)
					namespace = int(service_ref_split[6], 16)
					key = "%x:%x:%x:%x" % (sid, tsid, onid, namespace)
					if key not in self.channelNames:
						continue
					self.channel_numbers_names_and_refs.append((str(channel_number), self.channelNames[key], service_ref, self.tunerType(namespace)))

	def tunerType(self, namespace):
		if (namespace / (16**4)) == 0xFFFF:
			return "DVB-C"
		if (namespace / (16**4)) == 0xEEEE:
			return "DVB-T"
		return "DVB-S"

	def alternatives(self, service_line):
		result = re.match("^.*FROM BOUQUET \"(.+)\" ORDER BY.*$", service_line)
		if result is not None:
			try:
				alternative = open(self.path + result.group(1), "r")
			except Exception, e:
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
						print "[Plex DVR API] [alternatives] Error in %s" % result.group(1)
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
			if dvb_type == 'multi' or c_n_r[3] == dvb_type:
				self.data_tmp = {}
				self.data_tmp['GuideNumber']='%s' % c_n_r[0]
				self.data_tmp['GuideName']='%s' % c_n_r[1]
				self.data_tmp['URL']='http://%s:%d/%s' % (ip, port, c_n_r[2])
				self.lineup.append(self.data_tmp)
		return self.lineup

	def getBouquetsList(self):
		return self.bouquets_names

def noofchannels(dvb_type):
	return len(lineupdata(dvbtype=dvb_type))

def lineupdata(ipinput='0.0.0.0', dvbtype=''):
	channel_numbers = getLineup(single_bouquet=config.plexdvrapi.bouquets_list.value)
	return channel_numbers.createJSON(ip=ipinput, dvb_type=dvbtype)

def getBouquetsList():
	lineup = getLineup()
	return lineup.getBouquetsList()

getlineup = modules[__name__]
