import string
import random
import json
from os import path, mkdir
from sys import modules

from . import tunerTypes, tunertypes, tunerfolders

lineup_status = {}

class getLineupStatus:
	def __init__(self):
		pass

	def lineupstatusJSON(self, dvb_type):
		if path.exists('/www/%s/lineup_status.json' % tunerfolders[dvb_type]):
			with open('/www/%s/lineup_status.json' % tunerfolders[dvb_type]) as data_file:
				lineup_status[dvb_type] = json.load(data_file)
		else:
			lineup_status[dvb_type] = {}
			lineup_status[dvb_type]['ScanInProgess']=0
			lineup_status[dvb_type]['ScanPossible']=0
			lineup_status[dvb_type]['Source']='%s' % tunertypes[dvb_type]
			lineup_status[dvb_type]['SourceList']=["%s" % tunertypes[dvb_type]]
		return lineup_status

def lineupstatus(dvbtype):
	lineup_status = getLineupStatus()
	output = lineup_status.lineupstatusJSON(dvb_type=dvbtype)
	return output

def write_lineupstatus(writefile = "/tmp/lineup_status.json", dvbtype="DVB-S"):
	lineup_status = getLineupStatus()
	output = lineup_status.lineupstatusJSON(dvb_type=dvbtype)
	if not path.exists('/www/%s' % tunerfolders[dvbtype]):
		mkdir('/www/%s' % tunerfolders[dvbtype])
	try:
		with open(writefile, 'w') as outfile:
			json.dump(output[dvbtype], outfile)
		outfile.close()
	except Exception, e:
		print "Error opening %s for writing" % writefile
		return

getlineupstatus = modules[__name__]
