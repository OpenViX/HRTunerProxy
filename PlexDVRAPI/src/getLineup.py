import re
import json
from os import path, mkdir
from sys import modules

from . import tunerfolders

class getLineup:
	def __init__(self, duplicates = False):
		self.duplicates = duplicates
		self.refs_added = []
		self.path = "/etc/enigma2/"
		self.db = "lamedb"
		self.tv_index = "bouquets.tv"
		self.channelNames = {} # key SID:TSID:ONID:NAMESPACE in hex
		self.bouquets_filenames = []
		self.channel_numbers_names_and_refs = []
		self.video_allowed_types = [1, 4, 5, 17, 22, 24, 25, 27, 135]
		self.read_services()
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

	def read_tv_bouquets(self):
		channel_number = 0
		for filename in self.bouquets_filenames:
			try:
				bouquet = open(self.path + filename, "r")
			except Exception, e:
				continue

			content = bouquet.read()
			bouquet.close()

			for row in content.split("\n"):
				if row.startswith("#SERVICE "):
					if "http" in row:
						channel_number += 1
						continue
					service_ref = row[9:].strip()
					service_ref_split = service_ref.split(":")
					if len(service_ref_split) < 10:
						print "[Plex DVR API] [read_tv_bouquets] Error in %s" % filename
						continue
					if service_ref_split[1] == "64":
						continue
					if service_ref_split[1] == "832":
						channel_number += 1
						continue
					channel_number += 1
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

def noofchannels(dvbtype):
	channel_numbers = getLineup()
	output = channel_numbers.createJSON(dvb_type=dvbtype)
	return len(output)

def write_lineup(writefile = "/tmp/lineup.json", ipinput="0.0.0.0", dvbtype="DVB-S"):
	channel_numbers = getLineup()
	output = channel_numbers.createJSON(ip=ipinput, dvb_type=dvbtype)
	if not path.exists('/www/%s' % tunerfolders[dvbtype].lower()):
		mkdir('/www/%s' % tunerfolders[dvbtype].lower())
	if not path.exists('/www/%s/auto' % tunerfolders[dvbtype].lower()):
		mkdir('/www/%s/auto' % tunerfolders[dvbtype].lower())
	try:
		with open(writefile, 'w') as outfile:
			json.dump(output, outfile)
		outfile.close()
	except Exception, e:
		print "Error opening %s for writing" % writefile
		return

getlineup = modules[__name__]
