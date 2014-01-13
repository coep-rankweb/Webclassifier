from datasource import Datasource
from extractor import Extractor
import sys
import os

class Wikisource(Datasource):
	''' class defining the wikipedia data source '''
	def __init__(self, path, forced_categories = None):
		Datasource.__init__(self, path, "WIKI", forced_categories = forced_categories)

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
