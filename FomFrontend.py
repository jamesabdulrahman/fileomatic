# coding: utf-8
import os
import argparse
import json
import getpass
from fileomatic import FileOMatic

CONFIG_PATH = '~/.fomrc'
LOGO = """
      ___________   _____   _____   _______ ___________   _________
     /  __/__/  /  /  __/__/    /__/       /  __   /  /__/__/  ___/
    /  __/  /  /__/  __/__/ // /__/  / /  /  /_/  /   __/  /  /___
   /__/ /__/_____/____/  /____/  /__/_/__/__/ /__/_____/__/______/
                      For the staff of the AAC,
            in thanks for 2009-2012 and thereafter. -jb407
"""

def load_config():
	nice_path = os.path.expanduser(CONFIG_PATH)
	if os.path.isfile(nice_path) == True:
		try:
			rc_file = json.load(open(nice_path, 'r'))
			return rc_file
		except (ValueError, EOFError):
			return None

def run_fom():
	print(LOGO)
	config = load_config()
	if config != None:
		print('You are logging into {} as {}.'.format(config['server'], config['username']))
		print('You are going to file the mailbox "{}."'.format(config['mailbox']))
		print('Your emails will be filed to {}.'.format(config['file_root']))
		print('Please enter your email password (or CTRL-C to abort).')
		print('Your password will not show on-screen as you type.')
		password = getpass.getpass('Your email password: ')
		try:
			fom = FileOMatic(config['server'], config['username'], password, config['mailbox'], config['file_root'])
			fom.file_emails()
		except EOFError:
			print('Bye.')
			exit()
	else:
		print('You seem not to have a .fomrc file, or your .fomrc is invalid.')
		print('You need to create a configuration for the File-O-Matic to know what to do.')
		skeleton = open(os.path.expanduser(CONFIG_PATH), 'w')
		json.dump(dict(username='someone@example.net', server='imap.example.net', mailbox='Inbox', file_root='/emails'), skeleton, indent=4)
		print('I have created a skeleton file for you. Please edit it and add your details.')
		exit()

if __name__ == '__main__':
	run_fom()
