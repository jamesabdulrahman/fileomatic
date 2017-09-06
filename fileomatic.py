# coding: utf-8
import os
import sys
from datetime import datetime
from hashlib import sha256
from imaplib import IMAP4_SSL
from email.parser import BytesParser as EmailParser
from email.utils import parsedate_to_datetime as ParseDate
import re

class FileOMatic:

	def __init__(self, host, username, password, mailbox, file_root):
		"""
		Build a file-o-matic from the IMAP host and given credentials.
		"""
		self.file_root = file_root
		self.mailbox = mailbox
		os.chdir(self.file_root)
		self.server = IMAP4_SSL(host, port=993)
		self.server.login(username, password)

	def __del__(self):
		self.server.shutdown()

	def change_folder(self, folder):
		"""
		Change to the relevant folder on the server (e.g. Inbox).
		Returns number of messages in the folder.
		Throws self.error if folder does not exist.
		"""
		response = self.server.select(folder, readonly=True)
		return int(response[1][0])

	def get_messages(self, folder='Inbox', unread_only=False):
		"""
		Returns IDs of all messages in the folder.
		If unread_only is False, return only unseen messages.
		Throws self.error if folder does not exist.
		"""
		num_messages = self.change_folder(self.mailbox)
		if unread_only == False:
			return range(num_messages, 0, -1)
		else:
			messages = self.server.search(None, 'UNSEEN')
		return messages

	def get_header(self, message):
		"""
		Returns the envelope of the given message in RFC 822 format.
		The envelope contains the headers and other delivery information.
		"""
		envelope = self.server.fetch(str(message), '(RFC822.HEADER)')
		return envelope[1][0][1]

	def get_body(self, message):
		"""
		Returns the actual body of the message referred to
		by the given ID.
		"""
		body = self.server.fetch(str(message), '(BODY[TEXT])')
		return body[1][0][1]

	def get_mail(self, message):
		"""
		Return the whole email referred to by the given message ID,
		in RFC 822 format, as an instance of email.message.
		"""
		mail = self.server.fetch(str(message), '(BODY.PEEK[])')
		return EmailParser().parsebytes(mail[1][0][1])

	def sanitize(self, s):
		"""
		Sanitize potential filenames.
		Replace slashes and spaces with underscores,
		and truncate below 255 characters.
		"""
		bad_chars = r'[ /\\\\]' # those four slashes match a single literal one
		nice_string = re.sub(bad_chars, '_', s)
		return nice_string[:249]

	def make_file(self, sender, recipient, subject, body, datestamp, extension):
		"""
		Basic file writer.
		Generates a usable, sortable file name from the email’s envelope
		and writes it out. Knows nothing about encodings or types, this is
		handled in the caller function.
		"""
		folder = self.sanitize(sender)
		if os.path.isdir(folder) == False:
			os.mkdir(folder)
		os.chdir(folder)
		sensible_date = ParseDate(datestamp).timestamp() # unambiguous UNIX time-esque
		filestem = self.sanitize('{}_{}'.format(sensible_date, subject))
		filename = '{}.{}'.format(filestem, extension)
		with open(filename, 'w') as out:
			out.write(body)
		os.chdir(self.file_root)

	def decode_email(self, mail, sender, recipient, subject, body, datestamp):
		"""
		Parse and decode an email, then write it out as a file.
		"""
		charset = mail.get_content_charset()
		content_type = mail.get_content_type()
		if content_type == 'text/html' or content_type == 'text/plain':
			mail_str = mail.get_payload(decode=1)
			if charset == None:
				# the charset is not specified properly
				print("Couldn’t get encoding for {}, trying typical encodings in turn...".format(subject))
				body = self.brute_force_decode(mail_str)
			else:
				try:
					body = mail_str.decode(charset)
				except:
					# there are still instances where the wrong charset is
					# given, of course
					body = self.brute_force_decode(mail_str)
			if content_type == 'text/html':
				extension = 'html'
			if content_type == 'text/plain':
				extension = 'txt'
			self.make_file(sender, recipient, subject, body, datestamp, extension)
			print ("Filed {}".format(subject))

	def brute_force_decode(self, mail_str):
		"""
		For the (sadly, not infrequent) instances of bad headers
		or incorrectly specified charsets, just try UTF-8 and
		and if it fails try that awful legacy thing that we can’t
		seem to shake off.
		"""
		for encoding in ['UTF-8', 'ISO8859']:
			try:
				return mail_str.decode(encoding)
			except UnicodeDecodeError:
				continue

	def file_emails(self):
		messages = self.get_messages('Inbox')
		for message in messages:
			mail = self.get_mail(message)
			if mail['to']:
				recipient = mail['to'].replace('"', '')
			else:
				recipient = ''
			if mail['from']:
				sender = mail['from'].replace('"', '')
			else:
				sender = ''
			if mail['subject']:
				subject = mail['subject']
			else:
				subject = 'Unknown subject'
			datestamp = mail['date']
			body = ''
			for part in mail.walk():
				self.decode_email(part, sender, recipient, subject, body, datestamp)
