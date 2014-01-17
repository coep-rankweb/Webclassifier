from unidecode import unidecode
import re
import urllib2

blacklist = ['article', 'wikipedia', 'wiki', 'birth', 'people from', 'from', 'category', 'categories', 'pages', '.php', 'stubs', 'death', 'people', 'template', 'wiktio', 'en.', 'file', 'help', 'stub', 'list', 'disambiguation', 'by country', 'by area', 'by region', 'by continent', 'user:', 'portal:', 'talk', 'name']

def blacklisted(s):
	return contains(s, blacklist)

def contains(s, l):
	for i in l:
		if s.lower().rfind(i.lower()) >= 0:
			return True
	return False

def clean(s):
	s = encode_str(s)
	s = urllib2.unquote(s)
	s = re.sub(r'/wiki/', '', s)
	s = re.sub(r' ', '_', s)
	s = re.sub(r'#.*', '', s)
	return s

def encode_str(s):
	if type(s) == unicode:
		return unidecode(s)
	else:
		return unidecode(s.decode("utf-8", "ignore"))
