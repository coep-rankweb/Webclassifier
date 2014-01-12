from classifier import WebClassifier
import sys

'''
following are the command line arguments:

1. dir name containing category files
2. name for training dataset
3. name of the test file
'''

w = WebClassifier()
#w.generateFeatures()
w.buildData()
w.train()
#w.test(sys.argv[3])
