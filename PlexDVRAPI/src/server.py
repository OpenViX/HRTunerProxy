import posixpath
import argparse
import urllib
import os

from . import getIP, portfolders, tunerports
from sys import modules
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer


class RootedHTTPServer(HTTPServer):
	def __init__(self, *args, **kwargs):
		HTTPServer.__init__(self, *args, **kwargs)
		# self.RequestHandlerClass.base_path = base_path


class RootedHTTPRequestHandler(SimpleHTTPRequestHandler):
	def do_GET(self):
		print("[Plex DVR API] ----- Request Start ----->")
		try:
			print '[Plex DVR API] PARSING PORT'
			for x in str(self.headers).split('\r\n'):
				print '[Plex DVR API] X:',x
				if x.startswith('Host:'):
					host = x
					break
			print '[Plex DVR API] HOST1:',host.split(':')
			print '[Plex DVR API] HOST2:',host.split(':')[2]
			self.port = int(host.split(':')[2])
		except:
			print '[Plex DVR API] USING DEFAULT PORT'
			self.port = 6081
		print '[Plex DVR API] DEBUG1:',self.port
		self.base_path = portfolders[self.port]
		print '[Plex DVR API] DEBUG2:',self.base_path
		print("[Plex DVR API] <----- Request End -----")

		if self.path == '/':
			self.path  = '/device.xml'
		print '[Plex DVR API] PATH:',self.path
		try:
			sendReply = False
			if self.path.endswith(".html"):
				mimeType = 'text/html'
				sendReply = True
			elif self.path.endswith(".json"):
				mimeType = 'application/javascript'
				sendReply = True
			elif self.path.endswith(".xml"):
				mimeType = 'application/xml'
				sendReply = True
			elif self.path.endswith(".ico"):
				mimeType = 'image/x-icon'
				sendReply = True

			if sendReply == True:
				f = open(self.base_path + os.sep + self.path)
				self.send_response(200)
				self.send_header('Content-type', mimeType)
				self.end_headers()
				self.wfile.write(f.read())
				f.close()
			else:
				print '[Plex DVR API] file type not coded:',self.path
			return
		except IOError:
			self.send_error(404,'[Plex DVR API] File not found!')

	def translate_path(self, path):
		path = posixpath.normpath(urllib.unquote(path))
		words = path.split('/')
		words = filter(None, words)
		path = self.base_path
		for word in words:
			drive, word = os.path.splitdrive(word)
			head, word = os.path.split(word)
			if word in (os.curdir, os.pardir):
				continue
			path = os.path.join(path, word)
		return path

def run(dvbtype):
	ipaddress = getIP()
	ipport='%d' % int(tunerports[dvbtype])
	startserver(ip_address=ipaddress, port=ipport)

def startserver(ip_address='', port=''):
	server_address = (ip_address, int(port))
	httpd = RootedHTTPServer(server_address, RootedHTTPRequestHandler)
	sa = httpd.socket.getsockname()
	print "[Plex DVR API] Serving HTTP on %s port %s basefolder %s" % (str(sa[0]),str(sa[1]), portfolders[int(port)])
	httpd.serve_forever()


# For modules that do "from About import about"
server = modules[__name__]
