from classifier import WebClassifier
from wiki_source import Wikisource
import sys

'''
Note:
WebClassifier and Wikisource must contain additional `path` arguments which specify the location of the `webclassifier` directory where all *.py, *.conf files are located
'''

w = WebClassifier()
d = Wikisource(forced_categories = ['arts'])
d.generateFeatures()
d.buildData()
w.train(d)
#w.test(sys.argv[3])
