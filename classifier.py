from sklearn.naive_bayes import MultinomialNB
from scipy.sparse import csr_matrix, lil_matrix
from scipy.io import mmread, mmwrite
from nltk.stem import PorterStemmer
import sys
import os
import redis
import pickle
from ConfigParser import ConfigParser

class WebClassifier:
	def __init__(self, path):
		'''
		path specifies the path to the directory where the module is located.
		'''
		self.r = redis.Redis()
		self.mnb = MultinomialNB()
		self.stemmer = PorterStemmer()
		self.config = ConfigParser()
		os.chdir(os.path.abspath(path))
		self.config.readfp(open("classifier.conf"))
		try: os.mkdir("data/%s" % self.config.get("CLASSIFIER", "BASE"))
		except: pass
		self.metafl = open("data/%s/%s" % (self.config.get("CLASSIFIER", "BASE"), self.config.get("CLASSIFIER", "META_FILE")), "w+")

	def clean(self, s):
		s = s.replace('(', '_').replace(')', '_')
		return s.lower()

	def valid(self, s):
		a = s.replace(' ', '').replace('\t', '').replace('\n', '')
		return a != ''


	def train(self, datasource):
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
		X = datasource.createTrainingMatrix()
		Y = datasource.createResultVector()
		self.mnb.fit(X, Y)
		pickle.dump(self.mnb, open("data/%s/%s" % (self.config.get("CLASSIFIER", "BASE"), self.config.get("CLASSIFIER", "PICKLE_FILE")), "w"))

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
				try: vect[int(self.r.get(self.config.get("CLASSIFIER", "FEATURE_COLUMN") + ":" + tok)) - 1] = 1
				except:
					print tok + " not found!"
			TEST.append(vect)
		return TEST

	
	def loadClassifier(self):
		self.mnb = pickle.load(open("data/%s/%s" % (self.config.get("CLASSIFIER", "BASE"), self.config.get("CLASSIFIER", "PICKLE_FILE")), "r"))
		

	def test(self, dataset, load = False):
		'''
		Assumes raw datset: list of lists format(unequal length)
		'''
		if load:
			self.mnb = pickle.load(open("data/%s/%s" % (self.config.get("CLASSIFIER", "BASE"), self.config.get("CLASSIFIER", "PICKLE_FILE")), "r"))

		TEST = self.buildTestVector(dataset)
	
		return {
			'predict': self.mnb.predict(TEST),
			'predict_proba': self.mnb.predict_proba(TEST)
		}
