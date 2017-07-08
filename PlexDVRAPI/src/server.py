import posixpath
import argparse
import urllib
import os
import json

from sys import modules
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer

from . import getIP, tunerports, porttypes
from getLineup import getlineup
from getLineupStatus import getlineupstatus
from getDeviceInfo import getdeviceinfo


class RootedHTTPServer(HTTPServer):
	def __init__(self, *args, **kwargs):
		HTTPServer.__init__(self, *args, **kwargs)

class RootedHTTPRequestHandler(SimpleHTTPRequestHandler):
	def do_GET(self):
		try:
			for x in str(self.headers).split('\r\n'):
				if x.startswith('Host:'):
					host = x
					break
			self.port = int(host.split(':')[2])
		except:
			print '[Plex DVR API] USING DEFAULT PORT'
			self.port = 6081
		tunertype = porttypes[self.port]

		if self.path == '/':
			self.path  = '/device.xml'

		if self.path.endswith(".html"):
			mimeType = 'text/html'
		elif self.path.endswith(".json"):
			mimeType = 'application/javascript'
		elif self.path.endswith(".xml"):
			mimeType = 'application/xml'
		elif self.path.endswith(".ico"):
			mimeType = 'image/x-icon'

		if self.path.endswith("lineup_status.json"):
			self.send_response(200)
			self.send_header('Content-type', mimeType)
			self.end_headers()
			self.wfile.write(json.dumps(getlineupstatus.lineupstatus(tunertype)))
		elif self.path.endswith("lineup.json"):
			self.send_response(200)
			self.send_header('Content-type', mimeType)
			self.end_headers()
			self.wfile.write(json.dumps(getlineup.lineupdata(getIP(), tunertype)))
		elif self.path.endswith("discover.json"):
			self.send_response(200)
			self.send_header('Content-type', mimeType)
			self.end_headers()
			self.wfile.write(json.dumps(getdeviceinfo.discoverdata(tunertype)))
		elif self.path.endswith("device.xml"):
			self.send_response(200)
			self.send_header('Content-type', mimeType)
			self.end_headers()
			self.wfile.write(getdeviceinfo.devicedata(tunertype))
		else:
			self.send_error(404,'[Plex DVR API] File not found!')
			print '[Plex DVR API] file type not coded:',self.path
			return

def run(dvbtype):
	ipaddress = getIP()
	ipport='%d' % int(tunerports[dvbtype])
	startserver(ip_address=ipaddress, port=ipport)

def startserver(ip_address='', port=''):
	server_address = (ip_address, int(port))
	httpd = RootedHTTPServer(server_address, RootedHTTPRequestHandler)
	sa = httpd.socket.getsockname()
	print "[Plex DVR API] Serving HTTP on %s port %s" % (str(sa[0]),str(sa[1]))
	httpd.serve_forever()


# For modules that do "from About import about"
server = modules[__name__]
