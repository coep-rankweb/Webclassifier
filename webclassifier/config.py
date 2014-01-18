from ConfigParser import ConfigParser
import os

class Conf:
	def __init__(self):
		self.conf = ConfigParser()
		self.config_file = open(os.path.join(os.path.expanduser("~", ".classifier.conf"), "r+")
		self.conf.readfp(self.config_file)

	def get(section, key):
		return self.conf.get(section, key)

	def set(section, key, val):
		self.conf.set(section, key, val)
		self.conf.write(self.config_file)
