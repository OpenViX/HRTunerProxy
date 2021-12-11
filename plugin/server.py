from __future__ import print_function
from __future__ import absolute_import

import posixpath
import argparse
import urllib
import os
import json
import six

from sys import modules
try:
	from http.server import SimpleHTTPRequestHandler, HTTPServer, BaseHTTPRequestHandler
except:
	from SimpleHTTPServer import SimpleHTTPRequestHandler
	from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from . import getIP, tunerports, porttypes, logger
from .getLineup import getlineup
from .getLineupStatus import getlineupstatus
from .getDeviceInfo import getdeviceinfo
from Components.config import config


class RootedBaseHTTPRequestHandler(BaseHTTPRequestHandler):
	def log_message(self, format, *args):
		if config.hrtunerproxy.debug.value:
			logger.info("%s %s" % (self.address_string(), format % args))


class RootedHTTPServer(HTTPServer):
	def __init__(self, *args, **kwargs):
		HTTPServer.__init__(self, *args, **kwargs)


class RootedHTTPRequestHandler(RootedBaseHTTPRequestHandler):
	def do_GET(self):
		try:
			for x in str(self.headers).split('\n'):
				x = x.strip()
				if x.startswith('Host:'):
					host = x
					break
			self.port = int(host.split(':')[2])
		except:
			if config.hrtunerproxy.debug.value:
				logger.info('USING DEFAULT PORT: 6081')
			self.port = 6081
		tunertype = porttypes[self.port]

		if self.path == '/':
			self.path = '/device.xml'

		if self.path.endswith(".html"):
			mimeType = 'text/html'
		elif self.path.endswith(".json"):
			mimeType = 'application/javascript'
		elif self.path.endswith(".xml"):
			mimeType = 'application/xml'
		elif self.path.endswith(".css"):
			mimeType = 'text/css'
		elif self.path.endswith(".ico"):
			mimeType = 'image/x-icon'

		if self.path.endswith("lineup_status.json"):
			self.send_response(200)
			self.send_header('Content-type', mimeType)
			self.end_headers()
			self.wfile.write(six.ensure_binary(json.dumps(getlineupstatus.lineupstatus(tunertype))))
		elif self.path.endswith("lineup.json"):
			self.send_response(200)
			self.send_header('Content-type', mimeType)
			self.end_headers()
			self.wfile.write(six.ensure_binary(json.dumps(getlineup.lineupdata(getIP(), tunertype, config.hrtunerproxy.bouquets_list[tunertype].value))))
		elif self.path.endswith("discover.json"):
			self.send_response(200)
			self.send_header('Content-type', mimeType)
			self.end_headers()
			self.wfile.write(six.ensure_binary(json.dumps(getdeviceinfo.discoverdata(tunertype))))
		elif self.path.endswith("device.xml"):
			self.send_response(200)
			self.send_header('Content-type', mimeType)
			self.end_headers()
			self.wfile.write(six.ensure_binary(getdeviceinfo.devicedata(tunertype)))
		elif self.path.endswith("tuners.html"):
			self.send_response(200)
			self.send_header('Content-type', mimeType)
			self.end_headers()
			self.wfile.write(six.ensure_binary(getdeviceinfo.tunerstatus(tunertype)))
		elif self.path.endswith("style.css"):
			self.send_response(200)
			self.send_header('Content-type', mimeType)
			self.end_headers()
			self.wfile.write(six.ensure_binary("""html { width:100%; height: 100%;}
body {background: #777 url(data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiA/PjxzdmcgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiB2aWV3Qm94PSIwIDAgMSAxIiBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJub25lIj48cmFkaWFsR3JhZGllbnQgaWQ9InJnIiBncmFkaWVudFVuaXRzPSJ1c2VyU3BhY2VPblVzZSIgY3g9IjUwJSIgY3k9IjUwJSIgcj0iNzUlIj48c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjNjA2Yzg4IiBzdG9wLW9wYWNpdHk9IjEiLz48c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiMxMzE3MjEiIHN0b3Atb3BhY2l0eT0iMSIvPjwvcmFkaWFsR3JhZGllbnQ+PHJlY3QgeD0iLTUwIiB5PSItNTAiIHdpZHRoPSIxMDEiIGhlaWdodD0iMTAxIiBmaWxsPSJ1cmwoI3JnKSIgLz48L3N2Zz4K) no-repeat center center fixed;background-size: cover;font-family: sans-serif;}
.B {background: #fff;margin: 9.5em;border: 3px solid #000;box-shadow: 10px 10px 50px #000;display: table}
.C, .W {margin: auto;margin-top: 1em;padding: 10px;}
.C {width: 21em;}
.W {width: 80em;}
.S, .T {color: #fff;margin: -10px -10px 10px -10px;}
.S {background: #393;padding: 2px 20px;font-size: 0.8em;}
.T {background: #000;padding-left: 20px;font-weight: 700;}
.TE {background: #a00;}
.BE {background: #f00;color: #fff;border-color:#a00;}
a {text-decoration: none;}
a:hover {text-decoration: underline;}
a,a:visited {color: #00f;}
table {width: inherit;}
td img {margin-right:5px;}
.L * {border-bottom: 1px solid black;}
td {white-space: nowrap;}
td:first-child {text-align: center;}
button { margin-top: 0.25em; }"""))
		else:
			self.send_error(404, '[HRTunerProxy] File not found!')
			if config.hrtunerproxy.debug.value:
				logger.info('file type not coded:', self.path)
			return


def run(dvbtype):
	ipaddress = getIP()
	ipport = '%d' % int(tunerports[dvbtype])
	startserver(ip_address=ipaddress, port=ipport)


def startserver(ip_address='', port=''):
	server_address = (ip_address, int(port))
	httpd = RootedHTTPServer(server_address, RootedHTTPRequestHandler)
	sa = httpd.socket.getsockname()
	if config.hrtunerproxy.debug.value:
		logger.info('Serving HTTP on %s port %s' % (str(sa[0]), str(sa[1])))
	httpd.serve_forever()


# For modules that do "from About import about"
server = modules[__name__]
