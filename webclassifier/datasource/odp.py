import sys
from lxml import etree as ET
from datasource import _Datasource
import os
import gzip
import redis

class ODPsource(_Datasource):
	''' class defining the wikipedia data source '''
	def __init__(self, path):
		#Datasource.__init__(self, path, "ODP")
		super(Datasource, self).__init__(path, "ODP")
		self.r = redis.Redis()
		self.r.flushdb()
		self.DMOZ = 'content.rdf.u8.gz'

	def __populateRedis(self, forced_categories = None):
		with gzip.open(self.DMOZ, 'rb') as content:
			for event, element in ET.iterparse(content, tag='{http://dmoz.org/rdf/}ExternalPage'):
				elems = list(element)
				res = {}
				for elem in elems:
					tag = elem.tag.split('}')[1]
					try:
						if tag in ['Title', 'Description', 'topic']:
							val = elem.xpath('text()')[0]
							res[tag] = val
					except:
						print elem.tag
						continue
				# no longer need this, remove from memory again, as well as any preceding siblings
				element.clear()
				while element.getprevious() is not None:
					del element.getparent()[0]

				if not res['topic']: continue
				try:
					key = res['topic'].split('/')[1]
					if forced_categories and key in forced_categories:
						memb = res['Title'] + ' . ' + res['Description']
						r.sadd(key, memb)
				except: continue

	def POS(self, val):
		try: val = unicode(val, encoding = "UTF-8")
		except: pass
		val = unidecode(val)
		val = val.lower()

		val = re.sub("[!@#$%^&*()_\-=+><\\\/\"'{}:;\[\]]", ' ', val)

		words = nltk.wordpunct_tokenize(val)
		pos = nltk.pos_tag(words)
		return set([x[0] for x in pos if x[1] in ['NN', 'NNS', 'NNPS', 'NNP']])

	def generateFeatures(self, forced_categories = None, docs_per_category = 20000):
		self.__populateRedis(forced_cateories)

		categories = forced_categories or self.r.keys()
		for category in categories:
			l = r.srandmember(category, docs_per_category)
			os.mkdir(os.path.join(self.config.get(self.section, "CLASSES_FILE"), category))
			f = open("%s/%s/%s" % (self.config.get(self.section, "CLASSES_FILE"), name, self.config.get(self.section, "FEATURE_FILE")), "w")
			for doc in l:
				features = POS(doc)
				for j in features:
					if j: f.write("%s," % j)
				f.write("\n")
			print category
			f.close()
