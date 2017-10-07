import string
import random
import json
from os import path, mkdir
from sys import modules

from . import tunerTypes, tunertypes

lineup_status = {}

class getLineupStatus:
	def __init__(self):
		pass

	def lineupstatusJSON(self, dvb_type):
		lineup_status = {}
		lineup_status['ScanInProgess']=0
		lineup_status['ScanPossible']=0
		lineup_status['Source']='%s' % tunertypes[dvb_type]
		lineup_status['SourceList']=["%s" % tunertypes[dvb_type]]
		return lineup_status

def lineupstatus(dvbtype):
	lineup_status = getLineupStatus()
	output = lineup_status.lineupstatusJSON(dvb_type=dvbtype)
	return output


getlineupstatus = modules[__name__]
