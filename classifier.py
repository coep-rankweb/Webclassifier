from sklearn.naive_bayes import MultinomialNB
from scipy.sparse import csr_matrix, lil_matrix
from scipy.io import mmread, mmwrite
from extractor import Extractor
from nltk.stem import PorterStemmer
import sys
import os
import redis
import pickle

class WebClassifier:
	def __init__(self):
		self.e = Extractor()
		self.r = redis.Redis()
		self.mnb = MultinomialNB()
		self.stemmer = PorterStemmer()

		self.BASE = os.path.abspath("./data/")
		self.META_FILE = os.path.join(self.BASE, "classifier.meta")
		self.MATRIX_FILE = os.path.join(self.BASE, "training_data.mtx")
		self.PICKLE_FILE = os.path.join(self.BASE, "classifier_dump.pickle")
		self.CLASSES_FILE = os.path.join(self.BASE, "classes")
		self.LIST_FILE = "list.txt"
		self.FEATURE_FILE = "features.txt"

		self.categories = os.listdir(self.CLASSES_FILE)

		self.FEATURE_COLUMN = "FEATURE_COL"
		self.KEYWORD_SET = "KEYWORD_SET"

		self.metafl = open(self.META_FILE, "r+")

	def clean(self, s):
		s = s.replace('(', '_').replace(')', '_')
		return s.lower()

	def valid(self, s):
		a = s.replace(' ', '').replace('\t', '').replace('\n', '')
		return a != ''

	def generateFeatures(self, forced_categories = None):
		'''
		Has been hardcoded for wikipedia
		For each category, fetch Wiki-pages from list.txt
		Store keywords (links in the specified section)in features.txt
		'''
		#TODO make independent of training data source

		self.categories = forced_categories or self.categories
		for name in self.categories:
			print name
			f = open("%s/%s/%s" % (self.CLASSES_FILE, name, self.LIST_FILE), "r")
			g = open("%s/%s/%s" % (self.CLASSES_FILE, name, self.FEATURE_FILE), "w")
			for page in f:
				pagetok = page.strip().split('\t')
				try: section = pagetok[1]
				except: section = 0
				links = self.e.getWikiLinks(pagetok[0], section = section)
				for feature in links:
					units = set(self.clean(feature).split('_'))
					for unit in units:
						unit = self.stemmer.stem(unit)
						if self.valid(unit):
							g.write("%s," % unit)
				g.write("\n")
			f.close()
			g.close()

	def buildDB(self):
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
		for category in self.categories:
			g = open("%s/%s/%s" % (self.CLASSES_FILE, category, self.FEATURE_FILE))
			for features_csv in g:
				# Line ends with ,
				# Hence remove last item
				toklist = features_csv.strip().split(',')[:-1]
				for tok in toklist:
					if self.r.sadd(self.KEYWORD_SET, tok) == 1:
						#tok is not yet present in set
						self.r.set("%s:%s" % (self.FEATURE_COLUMN, tok), feature_count + 1)
						feature_count += 1
					nnz += 1
				document_count += 1
			g.close()
		self.metafl.write("%ld\n" % document_count)
		self.metafl.write("%ld\n" % feature_count)
		self.metafl.write("%ld\n" % nnz)

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

		doc, feature, nnz = self.buildDB()

		mtxfl = open(self.MATRIX_FILE, "w")
		mtxfl.write("%%MatrixMarket matrix coordinate real general\n%\n")
		mtxfl.write("%d\t%d\t%d\n" % (doc, feature, nnz))

		document_number = 1
		for category in self.categories:
			g = open("%s/%s/%s" % (self.CLASSES_FILE, category, self.FEATURE_FILE))
			cat_count = 0
			for doc in g:
				toklist = doc.strip().split(',')[:-1]
				for tok in toklist:
					mtxfl.write("%d\t%d\t1\n" % (document_number, int(self.r.get(self.FEATURE_COLUMN + ":" + tok))))
				document_number += 1
				cat_count += 1
			self.metafl.write("%s:%d\n" % (category, cat_count))
		mtxfl.close()

	def createTrainingMatrix(self):
		'''
		Builds sparse matrix from Matrix Market file.
		'''
		return mmread(self.MATRIX_FILE).tolil()

	def train(self):
		'''
		Reads each line from meta file as <category>:<docs_per_category>
		Splits on : into toklist. toklist[0] = category name, toklist[1] = docs/category
		create empty list Y
		for each category X: append category number of X to Y 'docs/category' times
		Y = training document results vector
		len(Y) = number of documents

		Training data:
		X = no of documents X total number of features
		Y = no of documents
		'''
		X = self.createTrainingMatrix()
		Y = []

		# Skipping various counts
		self.metafl.seek(0)
		self.metafl.readline()
		self.metafl.readline()
		self.metafl.readline()
		for l in self.metafl:
			toklist = l.strip().split(':')
			for i in range(int(toklist[1])):
				Y.append(self.categories.index(toklist[0]) + 1)
		self.mnb.fit(X, Y)

		pickle.dump(self.mnb, open(self.PICKLE_FILE, "w"))

	def buildDataSetFromFile(self, test_file = "test.txt"):
		'''
		Assumes data source is a file.
		Reads data from file.
		'''
		t = open(test_file, "r")
		dataset = []
		for doc in t:
			toklist = doc.strip().split(',')[:-1]
			dataset.append(toklist)
		return dataset
			
		
	def buildTestVector(self, dataset):
		'''
		Assumes dataset in a list of lists format where each list maybe of unequal length
		Converts raw dataset into standard matrix format for scikit classifier.
		Return list of lists in document vector format
		'''
		TEST = []
		self.metafl.seek(0)
		self.metafl.readline() # Document Count skipped
		feature_count = int(self.metafl.readline())

		for l in dataset:
			vect = [0] * feature_count
			for tok in l:
				tok = self.clean(self.stemmer.stem(tok))
				try: vect[int(self.r.get(self.FEATURE_COLUMN + ":" + tok)) - 1] = 1
				except:
					print tok + " not found!"
			TEST.append(vect)
		return TEST

	
	def loadClassifier(self):
		self.mnb = pickle.load(open(self.PICKLE_FILE, "r"))
		

	def test(self, dataset, load = False):
		'''
		Assumes raw datset: list of lists format(unequal length)
		'''
		if load: self.mnb = pickle.load(open(self.PICKLE_FILE, "r"))

		TEST = self.buildTestVector(dataset)
	
		return {
			'predict': self.mnb.predict(TEST),
			'predict_proba': self.mnb.predict_proba(TEST)
		}
