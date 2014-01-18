from ConfigParser import ConfigParser
from scipy.io import mmread, mmwrite
from nltk.stem import PorterStemmer
import redis
import os

class _Datasource:
	'''
	general interface to be implemented by each data source
	'''
	def __init__(self, path, section, config_file = "classifier.conf", forced_categories = None):
		self.config = ConfigParser()
		self.config_file = config_file
		self.config.readfp(open(self.config_file))
		self.section = section
		os.chdir(os.path.abspath(path))
		try: os.mkdir("data/%s" % self.section)
		except: pass
		self.metafl = ConfigParser()
		self.categories = forced_categories or os.listdir(self.config.get(self.section, "CLASSES_FILE"))
		self.r = redis.Redis()
		self.stemmer = PorterStemmer()

	def generateFeatures(self, forced_categories = None):
		''' depends on the data source '''
		pass

	def __buildDB(self):
		'''
		Creates set of unique features(keywords).
		Assigns each feature a column id (feature_count) in Redis.
		Builds meta file as:
		1. document count
		2. feature count
		3. Number of non zero entries

		'''
		self.r.flushdb()
		feature_count = 0
		document_count = 0
		nnz = 0
		self.metafl.add_section("TRAINING_DATA_STATS")
		for category in self.categories:
			g = open("%s/%s/%s" % (self.config.get(self.section, "CLASSES_FILE"), category, self.config.get(self.section, "FEATURE_FILE")))
			for features_csv in g:
				# Line ends with ,
				# Hence remove last item
				toklist = features_csv.strip().split(',')[:-1]
				for tok in toklist:
					if self.r.sadd(self.config.get(self.section, "KEYWORD_SET"), tok) == 1:
						#tok is not yet present in set
						self.r.set("%s:%s" % (self.config.get(self.section, "FEATURE_COLUMN"), tok), feature_count + 1)
						feature_count += 1
					nnz += 1
				document_count += 1
			g.close()
		self.metafl.set("TRAINING_DATA_STATS", "DOCUMENT_COUNT", document_count)
		self.metafl.set("TRAINING_DATA_STATS", "FEATURE_COUNT", feature_count)
		self.metafl.set("TRAINING_DATA_STATS", "NNZ", nnz)

		return document_count, feature_count, nnz


	def buildData(self):
		'''
		By iterating through each features.txt,
		it creates a Matrix Market format file.

		document_number: id for each document
		cat_count: number of training documents in each category

		Adds following to meta file:
		1. no of training docs per category
		'''

		doc, feature, nnz = self.__buildDB()

		mtxfl = open("data/%s/%s" % (self.section, self.config.get(self.section, "MATRIX_FILE")), "w")
		mtxfl.write("%%MatrixMarket matrix coordinate real general\n%\n")
		mtxfl.write("%d\t%d\t%d\n" % (doc, feature, nnz))
		self.metafl.add_section("CATEGORY_STATS")
		document_number = 1
		for category in self.categories:
			g = open("%s/%s/%s" % (self.config.get(self.section, "CLASSES_FILE"), category, self.config.get(self.section, "FEATURE_FILE")))
			cat_count = 0
			for doc in g:
				toklist = doc.strip().split(',')[:-1]
				for tok in toklist:
					mtxfl.write("%d\t%d\t1\n" % (document_number, int(self.r.get(self.config.get(self.section, "FEATURE_COLUMN") + ":" + tok))))
				document_number += 1
				cat_count += 1
			self.metafl.set("CATEGORY_STATS", category, cat_count)
		self.metafl.write(open("data/%s/%s" % (self.section, self.config.get(self.section, "META_FILE")), "wb"))
		mtxfl.close()

	def createTrainingMatrix(self):
		'''
		Builds sparse matrix from Matrix Market file.
		'''
		self.metafl.readfp(open("data/%s/%s" % (self.section, self.config.get(self.section, "META_FILE"))))
		return mmread("data/%s/%s" % (self.section, self.config.get(self.section, "MATRIX_FILE"))).tolil(), (self.metafl.get("TRAINING_DATA_STATS", "document_count"), self.metafl.get("TRAINING_DATA_STATS", "feature_count"))


	def createResultVector(self):
		self.metafl.readfp(open(self.config_file))
		Y = []
		for category, cat_count in self.metafl.items("CATEGORY_STATS"):
			for i in range(int(cat_count)):
				Y.append(self.categories.index(category) + 1)
		return Y
	
	def getFeatureCount(self):
		self.metafl.readfp(self.config_file)
		return int(self.metafl.get("TRAINING_DATA_STATS", "feature_count"))

	def clean(self, s):
		s = s.replace('-', ' ').replace('/', ' ').replace('\\', ' ')
		return s.lower()
		pass

	def valid(self, s):
		a = s.replace(' ', '').replace('\t', '').replace('\n', '')
		return a != ''
