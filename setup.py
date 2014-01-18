#from distutils.core import setup
from setuptools import setup
import os

setup(
	name='webclassifier',
	version='0.1.0',
	author='coep-rankweb',
	packages=['webclassifier'],
	url='http://pypi.python.org/pypi/TowelStuff/',
	license='LICENSE.txt',
	description='A web page classifier to be trained using a data source.',
	long_description=open('README.md').read(),
	install_requires=[ 
		"goose>=1.0.0",
		"redis>=2.7.5",
		"requests==2.1.0",
	],
	data_files=[(os.path.expanduser("~"), ['.classifier.conf'])]
)
