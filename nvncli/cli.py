#!/usr/bin/env python3
"""
NoteVN.com CLI

Usage: 	
    nvnc options FILE LINK 

Example:
	nvnc -lo test.py testingthiscli

Options:

    -h, --help          Show this screen
    --version           Show version
    -g, --get           Copy the contents of pad to a file
    -l, --live-update   Enable live update on notevn
    -o, --overwrite     Overwrite notevn contents
    -w, --watch         Watch file for changes
    -d, --debug         Switch to debug host

Note: Watch mode will overwrite contents of the notevn

"""

import os
import time
import traceback

from docopt import docopt
from termcolor import cprint

from nvncli.update_content import Notevn
from nvncli.__init__ import __version__
from nvncli.multihost import MultiHost

WARNING = 'red'
MESSAGE = 'blue'
SUCCESS = 'green'

def start():

	arguments = docopt(__doc__, version='nvncli version '+'.'.join(str(i) for i in __version__))
	
	filename = arguments.get('FILE', None)
	curr_dir = os.getcwd()
	file_path = os.path.join(curr_dir, filename)

	live_update = arguments.get('--live-update', False)
	watch = arguments.get('--watch', False)

	get = arguments.get('--get', False)

	link = arguments.get('LINK', ' ')

	debugHost = arguments.get('--debug', False)

	multihost = MultiHost('debug' if debugHost else 'main_note')

	try: 
		cprint('Connecting to %s...' % (multihost.get_variable('host')), MESSAGE)

		notevn = Notevn(link, live_update=live_update, multihost=multihost)

	except Exception as e:
		print(traceback.format_exc())
		if hasattr(e, 'stacktrace'):
			print(e.stacktrace())
		else:
			print(e)

		cprint("\nError: Something went wrong...", WARNING)
		return -1

	if(get):
		notevn.save_to_file(filename, True)
		cprint("Saved contents of {} to {} succesfully".format(link, filename), SUCCESS)
		return 1;

	if(notevn.haspw):
		cprint('\nPASS: The given url is password protected', MESSAGE)
	else:
		cprint("Saving {} to {}..... \n".format(filename,link), SUCCESS)
		notevn.save_file(file_path, arguments['--overwrite'])

		try:
			if watch:
				cprint('Watching {} for changes'.format(filename),MESSAGE)

			while watch:
				time.sleep(5)
				if notevn.is_file_content_changed():
					cprint('\nChanges detected', MESSAGE)
					notevn.save_file(file_path, True)
					cprint('Changes saved',MESSAGE)

		except  KeyboardInterrupt:
			cprint('\nClosing nvncli', MESSAGE) 

if __name__ == '__main__':

    start()
	



