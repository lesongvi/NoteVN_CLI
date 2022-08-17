from nvncli import __version__

import os
import sys

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup


dependencies = ['docopt', 'termcolor', 'socketio-client-nexus', 'brotli']


def publish():
	os.system("python3 setup.py sdist upload")



if sys.argv[-1] == "publish":
	publish()
	sys.exit()


setup(
	name='nvnc',
	version='.'.join(str(i) for i in __version__),
	description='A notevn.com command line interface',
	long_description="Notevn quick save text CLI, save your text quickly",
	url='https://github.com/lesongvi/notevn-cli',
	author='Le Song Vi',
	author_email='lesongvi@gmail.com',
	license="GPLv3+",
	install_requires=dependencies,
	packages=['nvncli'],
    py_modules=['nvncli'],
	entry_points={
		'console_scripts': [
			'nvnc=nvncli.cli:start'
		]
	},
	classifiers=[
		'Development Status :: 4 - Beta',
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Programming Language :: Python',
	]
)


