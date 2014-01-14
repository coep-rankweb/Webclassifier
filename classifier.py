from sklearn.naive_bayes import MultinomialNB
from scipy.sparse import csr_matrix, lil_matrix
from scipy.io import mmread, mmwrite
from nltk.stem import PorterStemmer
import sys
import os
import redis
import pickle
import time
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
		try: os.mkdir("data/classifier")
		except: pass

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
		X, shape = datasource.createTrainingMatrix()
		Y = datasource.createResultVector()
		self.metafl = ConfigParser()
		s = time.time()
		self.mnb.fit(X, Y)
		e = time.time()

		self.metafl.add_section("CLASSIFIER_STATS")
		self.metafl.set("CLASSIFIER_STATS", "classifier", str(self.mnb.__class__))
		self.metafl.set("CLASSIFIER_STATS", "data_source", datasource.section)
		self.metafl.set("CLASSIFIER_STATS", "document_count", shape[0])
		self.metafl.set("CLASSIFIER_STATS", "feature_count", shape[1])
		self.metafl.set("CLASSIFIER_STATS", "training_time", str(e - s))
		self.metafl.write(open("data/%s/%s" % ("classifier", self.config.get("CLASSIFIER", "META_FILE")), "wb"))
		pickle.dump(self.mnb, open("data/%s/%s" % ("classifier", self.config.get("CLASSIFIER", "PICKLE_FILE")), "w"))

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
			
		
	def __buildTestVector(self, dataset):
		'''
		Assumes dataset in a list of lists format where each list maybe of unequal length
		Converts raw dataset into standard matrix format for scikit classifier.
		Return list of lists in document vector format
		'''
		TEST = []
		self.metafl = ConfigParser()
		self.metafl.readfp(open("data/%s/%s" % ("classifier", self.config.get("CLASSIFIER", "META_FILE"))))
		feature_count = int(self.metafl.get("CLASSIFIER_STATS", "feature_count"))

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
		self.mnb = pickle.load(open("data/%s/%s" % ("classifier", self.config.get("CLASSIFIER", "PICKLE_FILE")), "r"))
		

	def test(self, dataset, load = False):
		'''
		Assumes raw datset: list of lists format(unequal length)
		'''
		if load:
			self.mnb = pickle.load(open("data/%s/%s" % ("classifier", self.config.get("CLASSIFIER", "PICKLE_FILE")), "r"))

		TEST = self.__buildTestVector(dataset)
	
		return {
			'predict': self.mnb.predict(TEST),
			'predict_proba': self.mnb.predict_proba(TEST)
		}
