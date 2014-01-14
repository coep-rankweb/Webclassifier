from classifier import WebClassifier
from wiki_source import Wikisource
import sys

'''
Note:
WebClassifier and Wikisource must contain additional `path` arguments which specify the location of the `webclassifier` directory where all *.py, *.conf files are located
'''

opt = sys.argv[1]
w = WebClassifier("./")
if opt == "train":
	#BUILD DATASOURCE
	d = Wikisource("./", forced_categories = ['arts', 'sports'])
	d.generateFeatures()
	d.buildData()
	#TRAIN CLASSIFIER
	w.train(d)
elif opt == "test":
	#TEST CLASSIFIER
	d = w.buildDataSetFromFile(test_file = "test.txt")
	w.loadClassifier()
	print w.test(d)
