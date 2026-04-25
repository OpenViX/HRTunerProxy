from sys import argv
from os import listdir
from os.path import isdir, join
from re import compile
from xml.sax import make_parser
from xml.sax.handler import ContentHandler, LexicalHandler, property_lexical_handler


class parseXML(ContentHandler, LexicalHandler):
	def __init__(self, attrlist):
		self.attrlist = attrlist
		self.last_comment = None
		self.ishex = compile(r'#[0-9a-fA-F]+\Z')

	def comment(self, comment):
		if "TRANSLATORS:" in comment:
			self.last_comment = comment

	def startElement(self, name, attrs):
		for texttoTranslate in ["text", "title", "menuTitle", "value", "caption", "description"]:
			try:
				key = str(attrs[texttoTranslate])
				if key.strip() != "" and not self.ishex.match(key):
					attrlist.add((key, self.last_comment))
					self.last_comment = None
			except KeyError:
				pass


parser = make_parser()
attrlist = set()
contentHandler = parseXML(attrlist)
parser.setContentHandler(contentHandler)
parser.setProperty(property_lexical_handler, contentHandler)

for arg in argv[1:]:
	if "../.git" in arg:  # skip /.git/ and /.github/
		continue
	if isdir(arg):
		for file in listdir(arg):
			if file.endswith(".xml"):
				parser.parse(join(arg, file))
	else:
		parser.parse(arg)

	attrlist = list(attrlist)
	attrlist.sort(key=lambda a: a[0])

	for (key, transText) in attrlist:
		print()
		print('#: ' + arg)
		key.replace("\\n", "\"\n\"")
		if transText:
			for line in transText.split('\n'):  # noqa: E741
				print("#. ", line)
		print('msgid "' + key + '"')
		print('msgstr ""')

	attrlist = set()
