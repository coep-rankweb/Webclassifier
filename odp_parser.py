from lxml import etree as ET
import gzip
from unidecode import unidecode
import redis
import sys
import nltk
import os
import time


def clean(s):
	s = s.replace('-', ' ').replace('/', ' ').replace('\\', ' ')
	return s.lower()


r = redis.Redis()
stemmer = nltk.stem.PorterStemmer()
nsmap = {'d': 'http://purl.org/dc/elements/1.0/'}

file_dict = {'Arts' : 0, 'Games' : 0, 'Kids and Teens' : 0, 'Reference' : 0, 'Shopping' : 0, 'Business' : 0, 'Health' : 0, 'News' : 0, 'Regional' : 0, 'Society' : 0, 'Computers' : 0, 'Home' : 0, 'Recreation' : 0, 'Science' : 0, 'Sports' : 0, 'World' : 0}

cat_count = {'Arts' : 0, 'Games' : 0, 'Kids and Teens' : 0, 'Reference' : 0, 'Shopping' : 0, 'Business' : 0, 'Health' : 0, 'News' : 0, 'Regional' : 0, 'Society' : 0, 'Computers' : 0, 'Home' : 0, 'Recreation' : 0, 'Science' : 0, 'Sports' : 0, 'World' : 0}

flag= {'Arts' : 0, 'Games' : 0, 'Kids and Teens' : 0, 'Reference' : 0, 'Shopping' : 0, 'Business' : 0, 'Health' : 0, 'News' : 0, 'Regional' : 0, 'Society' : 0, 'Computers' : 0, 'Home' : 0, 'Recreation' : 0, 'Science' : 0, 'Sports' : 0, 'World' : 0}

with gzip.open('content.rdf.u8.gz', 'rb') as content:
	for event, element in ET.iterparse(content, tag='{http://dmoz.org/rdf/}ExternalPage'):
		elems = list(element)
		res = []
		for elem in elems:
			tag = elem.tag.split('}')[1]
			if tag in ['Title', 'Description', 'topic']:
				val = elem.xpath('text()')[0]
				try: val = unicode(val, encoding = "UTF-8")
				except: pass
				res.append(unidecode(val))

		# no longer need this, remove from memory again, as well as any preceding siblings
		element.clear()
		while element.getprevious() is not None:
		    del element.getparent()[0]

		res = dict(zip(['title', 'description', 'topic'], res))
		try:
			res['topic'] = res['topic'].split('/')[1]	#extract only the top category
		except IndexError as e:
			print res

		if flag[res['topic']]: continue

		words = nltk.wordpunct_tokenize(res['title'] + " . " + res['description'])
		pos = nltk.pos_tag(words)
		res['keywords'] = set([x[0] for x in pos if x[1] in ['NN', 'NNS', 'NNPS', 'NNP']])


		try:
			os.mkdir(os.path.join("classes", res['topic']))
			print res['topic']
			f = open(os.path.join("classes", res['topic'], "features.txt"), "w")
			file_dict[res['topic']] = f
		except OSError:
			f = file_dict[res['topic']]

		cat_count[res['topic']] += 1
		if cat_count[res['topic']] >= 20000:
			flag[res['topic']] = 1

		for k in res['keywords']:
			k = stemmer.stem(clean(k))
			if k: f.write("%s," % k)
		f.write("\n")
		del res

for f in file_dict.values():
	f.close()



