import os
from random import choice
from datetime import datetime, timedelta
from pprint import pprint

from .extra.exceptions import TokenError, base_method
from .extra.logger import logger
from .db_handler import DBHandler
from .command_handler import CommandHandler
from .api_functions import get, post


class Bot:
	"""Main bot class. Interacts with user: operates with updates and sends reminders"""

	def __init__(self):
		with open('bot/phrases.txt', 'r') as f:
			self.PHRASES = f.readlines()
		self.logger = logger
		self.TOKEN = os.getenv('REMEMBERANCER_BOT_TOKEN')
		if self.TOKEN is None:
			raise TokenError
		self.DBHandler = DBHandler(self.logger)
		self.CommandHandler = CommandHandler(self.logger)
		self.update_last_id()

	@base_method
	def start(self):
		"""starts bot"""
		updates = get('getUpdates').json()['result']
		if len(updates) > 0:
			last_id = updates[-1]['update_id']
			get('getUpdates', data={'offset': last_id + 1})

		while True:
			updates = self.process_updates()
			self.update_last_id(updates)
			self.send_reminders()

	@base_method
	def process_updates(self):
		"""manages all new updates"""

		updates = get('getUpdates', data={'offset': self.last_id + 1}).json()['result']

		if len(updates) == 0:
			return updates

		for update in updates:
			self.process(update)

		return updates

	@base_method
	def process(self, update: dict):
		"""main function for processing updates"""
		if 'callback_query' in update:
			chat_id = update['callback_query']['message']['chat']['id']
			text = update['callback_query']['data']
			message_id = update['callback_query']['message']['message_id']
			print('last_id:', '{:>8}'.format(self.last_id), 'text:', '{:>15}'.format(text), 'id:', update['update_id'])
		else:
			chat_id = update['message']['chat']['id']

			# if sticker or image or smth else(not text)
			if 'text' not in update['message']:
				print('last_id:', '{:>8}'.format(self.last_id), 'text:', '{:>15}'.format('Not text'), 'id:', update['update_id'])
				post('sendMessage', data={'chat_id': update['message']['chat']['id'], 'text': choice(self.PHRASES)})
				return

			print('last_id:', '{:>8}'.format(self.last_id), 'text:', '{:>15}'.format(update['message']['text']), 'id:', update['update_id'])
			text = update['message']['text']
			message_id = None

		if text.startswith('/'):
			self.CommandHandler.process_command(chat_id, text)
		else:
			self.CommandHandler.process_text(chat_id, text, message_id)

	@base_method
	def send_reminders(self):
		"""sends reminders which time has come and delete it"""
		rems_to_send = self.DBHandler.get_reminders_to_send()
		for reminder in rems_to_send:
			success = self.send_reminder(reminder)
			if success:
				self.DBHandler.delete_reminder(reminder)

	@base_method
	def send_reminder(self, reminder: dict):
		"""sends one reminder with values in reminder dict"""
		try:
			date = reminder['reminder_date']
			chat_id = reminder['chat_id']
			text = '<b>You have a reminder</b>'
			if reminder['reminder_text'] != '':
				text += ':\n<i>' + reminder['reminder_text'] + '</i>'
		except KeyError as err:
			self.logger.error('promblem with reminder')
			raise err

		if datetime.utcnow() - date > timedelta(seconds=30):
			return True

		response = post('sendMessage', data={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'})

		if response.status_code != 200:
			return False
		else:
			return True

	@base_method
	def update_last_id(self, updates: list = None):

		if updates is None:
			updates = get('getUpdates').json()['result']

		if len(updates) > 0:
			self.last_id = updates[-1]['update_id']
		else:
			try:
				self.last_id
			except AttributeError:
				self.last_id = 0
