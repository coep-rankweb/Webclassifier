import sys
from datasource import Datasource
from extractor import Extractor
import os

import requests
import traceback
import json


from unidecode import unidecode
import re
import urllib2

class Wikisource(Datasource):
	''' class defining the wikipedia data source '''
	def __init__(self, path, forced_categories = None):
		#Datasource.__init__(self, path, "WIKI", forced_categories = forced_categories)
		super(Datasource, self).__init__(path, "WIKI", forced_categories = forced_categories)

	def generateFeatures(self):
		'''
		Has been hardcoded for wikipedia
		For each category, fetch Wiki-pages from list.txt
		Store keywords (links in the specified section)in features.txt
		'''
		e = Extractor()
		print self.categories
		for name in self.categories:
			print name
			f = open("%s/%s/%s" % (self.config.get(self.section, "CLASSES_FILE"), name, self.config.get(self.section, "LIST_FILE")), "r")
			g = open("%s/%s/%s" % (self.config.get(self.section, "CLASSES_FILE"), name, self.config.get(self.section, "FEATURE_FILE")), "w")
			for page in f:
				print page
				pagetok = page.strip().split('\t')
				try: section = pagetok[1]
				except: section = 0
				links = e.getWikiLinks(pagetok[0], section = section)
				for feature in links:
					units = set(self.clean(feature).split('_'))
					for unit in units:
						unit = self.stemmer.stem(unit)
						if self.valid(unit):
							g.write("%s," % unit)
				g.write("\n")
			f.close()
			g.close()



class WikiExtractor:
	def __init__(self):
		self.base_url = 'http://en.wikipedia.org/w/api.php'
		self.util = WikiUtil()

	def getWikiBacklinks(self, topic, filter = "redirects"):
		topic_url = topic.replace(' ', '+')
		params = {'action': 'query', 'list': 'backlinks', 'bltitle': topic_url, 'bllimit': 'max', 'blfilterredir': filter, 'format': 'json'}
		backlink_set = set()
		try:
			backlink_json = json.loads(requests.get(self.base_url, params = params).content)
			backlink_set = set([self.util.clean(x['title']) for x in result_json['query']['backlinks'] if not self.util.blacklisted(x['title'])])
		except Exception as e:
			traceback.print_exc()
		return backlink_set
	
	def getWikiCategories(self, topic):
		topic_url = topic.replace(' ', '+')
		params = {'action': 'parse', 'page': topic_url, 'prop': 'categories', 'format': 'json', 'redirects': 1}
		category_set = set()
		try:
			category_json = json.loads(requests.get(self.base_url, params = params).content)
			category_set = set([self.util.clean(x['*']) for x in result_json['parse']['categories'] if not self.util.blacklisted(x['*'])])
		except Exception as e:
			traceback.print_exc()
		return category_set
	
	def getWikiLinks(self, topic, section = 0):
		topic_url = topic.replace(' ', '+')
		params = {'action': 'parse', 'page': topic_url, 'prop': 'links', 'section': section, 'format': 'json', 'redirects': 1}
		link_set = set()
		try:
			result_json = json.loads(requests.get(self.base_url, params = params).content)
			link_set = set([self.util.clean(x['*']) for x in result_json['parse']['links'] if not self.util.blacklisted(x['*'])])
		except Exception as e:
			traceback.print_exc()
		return link_set

	def getAllFromCategory(self, category):
		cat_url = category.replace(' ', '+')
		params = {'action': 'query', 'list': 'categorymembers', 'cmtitle': 'Category:%s' % cat_url, 'cmlimit': 'max', 'cmtype': 'page|subcat', 'format': 'json', 'redirects': 1}
		page_set = set()
		cat_set = set()
		try:
			result_json = json.loads(requests.get(self.base_url, params).content)
			for elem in result_json['query']['categorymembers']:
				if elem['title'].startswith('Category'):
					title = elem['title'].split(':')[1]
					if not self.util.blacklisted(title):
						cat_set.add(self.util.clean(elem['title'].split(':')[1]))
				else:
					if not self.util.blacklisted(elem['title']):
						page_set.add(self.util.clean(elem['title']))
		except Exception as e:
			traceback.print_exc()
		return {'pages': page_set, 'categories': cat_set}

	def extract(self, topic):
		TYPE = self.ARTICLE	#default
		if topic.startswith('Category'):
			TYPE = self.CATEGORY
			return {'type': TYPE, 'links': None, 'categories': None}
		else:
			cat = self.getWikiCategories(topic)
			if cat.intersection(set(['All_article_disambiguation_pages', 'All_disambiguation_pages', 'Disambiguation_pages'])):
				TYPE = self.DISAMBIGUATION
			links = self.getWikiLinks(topic)
			cat1 = [x for x in cat if not self.util.blacklisted(x)]
			links1 = [x for x in links if not self.util.blacklisted(x)]
			return {'type': TYPE, 'links': links1, 'categories': cat1}



class WikiUtil:
	blacklist = ['article', 'wikipedia', 'wiki', 'birth', 'people from', 'from', 'category', 'categories', 'pages', '.php', 'stubs', 'death', 'people', 'template', 'wiktio', 'en.', 'file', 'help', 'stub', 'list', 'disambiguation', 'by country', 'by area', 'by region', 'by continent', 'user:', 'portal:', 'talk', 'name']

	def blacklisted(self, s):
		return contains(s, blacklist)

	def contains(self, s, l):
		for i in l:
			if s.lower().rfind(i.lower()) >= 0:
				return True
		return False

	def clean(self, s):
		s = encode_str(s)
		s = urllib2.unquote(s)
		s = re.sub(r'/wiki/', '', s)
		s = re.sub(r' ', '_', s)
		s = re.sub(r'#.*', '', s)
		return s

	def encode_str(self, s):
		if type(s) == unicode:
			return unidecode(s)
		else:
			return unidecode(s.decode("utf-8", "ignore"))
