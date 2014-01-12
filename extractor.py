# -*- coding: utf-8 -*-
import requests
import traceback
import util
import json


class Extractor:
	def __init__(self):
		self.base_url = 'http://en.wikipedia.org/w/api.php'

	def getWikiBacklinks(self, topic, filter = "redirects"):
		topic_url = topic.replace(' ', '+')
		params = {'action': 'query', 'list': 'backlinks', 'bltitle': topic_url, 'bllimit': 'max', 'blfilterredir': filter, 'format': 'json'}
		backlink_set = set()
		try:
			backlink_json = json.loads(requests.get(self.base_url, params = params).content)
			backlink_set = set([util.clean(x['title']) for x in result_json['query']['backlinks'] if not util.blacklisted(x['title'])])
		except Exception as e:
			traceback.print_exc()
		return backlink_set
	
	def getWikiCategories(self, topic):
		topic_url = topic.replace(' ', '+')
		params = {'action': 'parse', 'page': topic_url, 'prop': 'categories', 'format': 'json', 'redirects': 1}
		category_set = set()
		try:
			category_json = json.loads(requests.get(self.base_url, params = params).content)
			category_set = set([util.clean(x['*']) for x in result_json['parse']['categories'] if not util.blacklisted(x['*'])])
		except Exception as e:
			traceback.print_exc()
		return category_set
	
	def getWikiLinks(self, topic, section = 0):
		topic_url = topic.replace(' ', '+')
		params = {'action': 'parse', 'page': topic_url, 'prop': 'links', 'section': section, 'format': 'json', 'redirects': 1}
		link_set = set()
		try:
			result_json = json.loads(requests.get(self.base_url, params = params).content)
			link_set = set([util.clean(x['*']) for x in result_json['parse']['links'] if not util.blacklisted(x['*'])])
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
					if not util.blacklisted(title):
						cat_set.add(util.clean(elem['title'].split(':')[1]))
				else:
					if not util.blacklisted(elem['title']):
						page_set.add(util.clean(elem['title']))
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
			cat1 = [x for x in cat if not util.blacklisted(x)]
			links1 = [x for x in links if not util.blacklisted(x)]
			return {'type': TYPE, 'links': links1, 'categories': cat1}
