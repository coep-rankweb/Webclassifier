from distutils.core import setup

setup(
	name='webclassifier',
	version='0.1.0',
	author='coep-rankweb',
	packages=['webclassifier'],
	url='http://pypi.python.org/pypi/TowelStuff/',
	license='LICENSE.txt',
	description='A web page classifier to be trained using a data source.',
	long_description=open('README.txt').read(),
	install_requires=[ 
		"goose>=1.0.0",
		"redis>=2.7.5",
		"requests==2.1.0",
	],
)
