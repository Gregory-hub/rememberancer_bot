from datetime import datetime, timedelta
from random import choice
import calendar
import json

from .api_functions import post
from .db_handler import DBHandler
from .extra.exceptions import base_method


class CommandHandler:
	"""Class for executing bot commands"""

	def __init__(self, logger):
		# all code uses one logger
		self.COMMAND_LIST = ['/start', '/help', '/commands', '/reminder', '/format', '/cancel', '/list', '/timezone', '/delete']
		self.logger = logger
		self.DBHandler = DBHandler(logger)
		with open('bot/phrases.txt', 'r') as f:
			self.PHRASES = f.readlines()

	@base_method
	def process_command(self, chat_id: int, text: str):
		"""processes one command"""
		mode, _ = self.DBHandler.get_chat_mode(chat_id)
		command = text.split(' ')[0]
		if mode != 'normal' and command != '/cancel' and command != '/format' and mode is not None:
			post('sendMessage', data={'chat_id': chat_id, 'text': "You can't do this in {mode} mode".format(mode=mode)})
			return
		if command in self.COMMAND_LIST:

			if command == '/start':
				self.start_command(chat_id)
			elif command == '/help':
				self.help_command(chat_id)
			elif command == '/commands':
				self.commands_command(chat_id)
			elif command == '/reminder':
				self.reminder_command(chat_id)
			elif command == '/format':
				self.format_command(chat_id)
			elif command == '/cancel':
				self.cancel_command(chat_id)
			elif command == '/list':
				self.list_command(chat_id)
			elif command == '/timezone':
				self.timezone_command(chat_id)
			elif command == '/delete':
				self.delete_command(chat_id)

		else:
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Command {} not found'.format(command)})

	@base_method
	def start_command(self, chat_id: int):
		text = """
Hi! My name is Remembrancer
I am bot for reminding you important things

To start enjoying the world of reminders type /reminder
But first better check /format

To get help /help
"""
		post('sendMessage', data={'chat_id': chat_id, 'text': text})

	@base_method
	def help_command(self, chat_id: int):
		text = """
Do not worry. I'll help you to navigate

Set a reminder /reminder
At specified time I will send you specified text

Check your reminders /list
List all your reminders which aren't sent yet

Change or set timezone /timezone
I need this to be able to record date and time in right form

Exit if there is something to exit /cancel

If you do not understand what is the format of all this messages check /format
"""
		post('sendMessage', data={'chat_id': chat_id, 'text': text})

	@base_method
	def commands_command(self, chat_id: int):
		"""sends list of commands"""
		post('sendMessage', data={'chat_id': chat_id, 'text': '<b>Available commands</b>:\n' + '\n'.join(self.COMMAND_LIST), 'parse_mode': 'HTML'})

	@base_method
	def reminder_command(self, chat_id: int):
		"""enters reminder mode
		commands: /format, /cancel"""
		chat_mode, _ = self.DBHandler.get_chat_mode(chat_id)
		tz = self.DBHandler.get_timezone(chat_id)
		if tz is None:
			post('sendMessage', data={'chat_id': chat_id, 'text': "Wait. I don't know your timezone. Let me record it"})
			self.timezone_command(chat_id)
			return
		if chat_mode != 'reminder':
			self.DBHandler.set_chat_mode(chat_id, 'reminder', 'date')
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Enter date'})
		else:
			post('sendMessage', data={'chat_id': chat_id, 'text': 'You are already in reminder mode'})

	@base_method
	def cancel_command(self, chat_id: int):
		"""goes to normal mode"""
		mode, awaits_for = self.DBHandler.get_chat_mode(chat_id)
		if mode == 'normal':
			post('sendMessage', data={'chat_id': chat_id, 'text': 'You are already in normal mode'})
		else:
			self.DBHandler.set_chat_mode(chat_id, 'normal')
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Now you are in normal mode'})

	@base_method
	def format_command(self, chat_id: int):
		"""gives user info about date and time formats"""
		dt = datetime.today()
		tz = self.DBHandler.get_timezone(chat_id)
		if tz is None:
			tz = 12
		else:
			tz = abs(tz)

		reply = 'Date format: {d}/{mon} or {d}/{mon}/{y}\n'.format(d=dt.day, mon=dt.month, y=dt.year)
		reply += 'Time format: {h:0>2}:{m:0>2}\n'.format(h=dt.hour, m=dt.minute)
		reply += 'Timezone format: {tz} or -{tz}'.format(tz=tz)
		post('sendMessage', data={'chat_id': chat_id, 'text': reply})

	@base_method
	def list_command(self, chat_id: int):
		"""sends to user list of his reminders"""
		reminders = self.DBHandler.get_user_reminders(chat_id)
		if reminders == []:
			post('sendMessage', data={'chat_id': chat_id, 'text': 'You have no reminders'})
		else:
			reminders_str = ''
			for i in range(len(reminders)):
				dt = self.dt_with_tz(chat_id, reminders[i]['reminder_date'])
				if dt is None:
					post('sendMessage', data={'chat_id': chat_id, 'text': "Wait. I don't know your timezone. Let me record it"})
					self.timezone_command(chat_id)
					return
				text = reminders[i]['reminder_text']
				reminders_str += '\n{i}. {dt.day:0>2}/{dt.month:0>2}/{dt.year} {dt.hour:0>2}:{dt.minute:0>2} <i>{text}</i>'.format(i=i + 1, dt=dt, text=text)
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Your reminders:' + reminders_str, 'parse_mode': 'HTML'})

	@base_method
	def timezone_command(self, chat_id: int):
		"""enters temezone mode"""
		self.DBHandler.set_chat_mode(chat_id, 'timezone')

		tz = self.DBHandler.get_timezone(chat_id)
		if tz is None:
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Enter timezone'})
		else:
			if tz > 0:
				tz = '+' + str(tz)
			else:
				tz = str(tz)
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Your timezone is {tz}. Enter timezone to change it or /cancel to keep it'.format(tz=tz)})

	@base_method
	def delete_command(self, chat_id: int):
		"""enters delete mode"""
		mode = self.DBHandler.get_chat_mode(chat_id)
		if mode == 'delete':
			post('sendMessage', data={'chat_id': chat_id, 'text': 'You are already in delete mode'})
		else:
			reminders = self.DBHandler.get_user_reminders(chat_id)
			if reminders == []:
				post('sendMessage', data={'chat_id': chat_id, 'text': 'You have no reminders'})
				return
			self.DBHandler.set_chat_mode(chat_id, 'delete')
			reply_markup = json.dumps({
				"inline_keyboard": [[{'text': '{dt.day:0>2}/{dt.month:0>2}/{dt.year} {dt.hour:0>2}:{dt.minute:0>2}'.format(dt=self.dt_with_tz(chat_id, rem['reminder_date'])), 'callback_data': '{dt.day:0>2}/{dt.month:0>2}/{dt.year} {dt.hour:0>2}:{dt.minute:0>2}'.format(dt=self.dt_with_tz(chat_id, rem['reminder_date']))}] for rem in reminders]
			})
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Select reminder to delete', 'reply_markup': reply_markup})

	@base_method
	def process_text(self, chat_id: int, text: str, message_id: int = None):
		"""processes all text except commands"""
		mode, awaits_for = self.DBHandler.get_chat_mode(chat_id)
		if mode == 'normal':
			post('sendMessage', data={'chat_id': chat_id, 'text': choice(self.PHRASES)})
		elif mode == 'reminder':
			self.process_reminder_text(chat_id, awaits_for, text)
		elif mode == 'timezone':
			self.process_timezone_text(chat_id, text)
		elif mode == 'delete':
			self.process_delete_text(chat_id, text, message_id)

	@base_method
	def process_reminder_text(self, chat_id: int, awaits_for: str, text: str):
		"""processes text in reminder mode, sets reminder date, time and text"""
		if awaits_for == 'date':
			if not self.date_is_valid(text):
				post('sendMessage', data={'chat_id': chat_id, 'text': 'Date is invalid(/format)'})
				return

			self.DBHandler.save_temp_date(chat_id, text)
			self.DBHandler.set_chat_mode(chat_id, 'reminder', 'time')
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Enter time'})

		elif awaits_for == 'time':
			if not self.time_is_valid(text):
				post('sendMessage', data={'chat_id': chat_id, 'text': 'Time is invalid(/format)'})
				return

			temp_date = self.DBHandler.get_temp_date(chat_id)
			if temp_date:
				dt = self.get_datetime(chat_id, temp_date, text)
				dt = self.dt_utc(chat_id, dt)
			else:
				post('sendMessage', data={'chat_id': chat_id, 'text': 'Something went wrong'})
				self.DBHandler.set_chat_mode(chat_id, 'normal')
				return

			if not self.is_future(dt):
				post('sendMessage', data={'chat_id': chat_id, 'text': "You are trying to set reminder in the past. I can't do that"})
				self.DBHandler.set_chat_mode(chat_id, 'normal')
				return

			self.DBHandler.save_temp_time(chat_id, text)
			self.DBHandler.set_chat_mode(chat_id, 'reminder', 'text')
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Enter reminder text (- to make remidner without text)'})

		elif awaits_for == 'text':
			date = self.DBHandler.get_temp_date(chat_id)
			time = self.DBHandler.get_temp_time(chat_id)
			if time is None or date is None:
				post('sendMessage', data={'chat_id': chat_id, 'text': 'Something went wrong'})
				self.DBHandler.set_chat_mode(chat_id, 'normal')
				return

			dt = self.get_datetime(chat_id, date, time)
			dt = self.dt_utc(chat_id, dt)
			success = self.DBHandler.set_reminder(chat_id, dt, text)

			if success:
				dt = self.dt_with_tz(chat_id, dt)
				post('sendMessage', data={'chat_id': chat_id, 'text': 'Reminder is set on {day} {month} {year}, {hour:0>2}:{minute:0>2}'.format(day=dt.day, month=calendar.month_name[dt.month], year=dt.year, hour=dt.hour, minute=dt.minute)})
			else:
				post('sendMessage', data={'chat_id': chat_id, 'text': 'Something went wrong. Reminder is not set'})

			self.DBHandler.set_chat_mode(chat_id, 'normal')

	@base_method
	def process_timezone_text(self, chat_id: int, text: str):
		"""sets chat timezone"""
		try:
			tz = int(text)
			if tz < -24 or tz > 24:
				raise ValueError
		except ValueError:
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Wrong format. Check /format'})
			return

		self.DBHandler.set_timezone(chat_id, tz)
		post('sendMessage', data={'chat_id': chat_id, 'text': 'Timezone is set'})
		self.DBHandler.set_chat_mode(chat_id, 'normal')

	@base_method
	def process_delete_text(self, chat_id: int, text: str, message_id: int):
		"""deletes reminder with specified date and time"""
		date_and_time = text.split()
		if len(date_and_time) != 2:
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Wrong format. Check /format'})
			return
		date, time = date_and_time
		if not self.date_is_valid(date) or not self.time_is_valid(time):
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Wrong format. Check /format'})
			return
		dt = datetime.strptime(date + ' ' + time, '%d/%m/%Y %H:%M')
		dt = self.dt_utc(chat_id, dt)
		reminder = self.DBHandler.get_chat_reminder_by_dt(chat_id, dt)
		if reminder is None:
			post('sendMessage', data={'chat_id': chat_id, 'text': 'There is no reminders at this time'})
			return
		self.DBHandler.delete_reminder(reminder)
		post('sendMessage', data={'chat_id': chat_id, 'text': 'Reminder deleted'})
		self.DBHandler.set_chat_mode(chat_id, 'normal')
		post('editMessageReplyMarkup', data={'chat_id': chat_id, 'message_id': message_id, 'reply_markup': ""})

	@base_method
	def date_is_valid(self, text: str):
		# checks if text is date in format dd/mm or dd/mm/yyyy
		if text.count('/') == 1:
			try:
				datetime.strptime(text, '%d/%m')
			except ValueError:
				return False
			return True
		elif text.count('/') == 2:
			try:
				datetime.strptime(text, '%d/%m/%Y')
			except ValueError:
				return False
			return True
		else:
			return False

	@base_method
	def time_is_valid(self, text: str):
		# checks if text is time in format hh:mm
		if text.count(':') == 1:
			try:
				datetime.strptime(text, '%H:%M')
			except ValueError:
				return False
			return True

		else:
			return False

	@base_method
	def is_future(self, dt: datetime):
		"""checks if datetime is future(input dt must be in utc)"""
		return dt > datetime.utcnow()

	@base_method
	def get_date(self, chat_id: int, text: str):
		"""adds a year to date if date is not future. returns date in format d/m/year"""

		if text.count('/') == 1:
			text += '/' + str(datetime.now().year)
			if not self.is_future(self.dt_utc(chat_id, datetime.strptime(text + ' 23:59', '%d/%m/%Y %H:%M'))):
				text = text[:-4] + str(datetime.now().year + 1)

		return text

	@base_method
	def get_datetime(self, chat_id: int, date: str, time: str):
		"""combines date and time considering timezone"""
		date = self.get_date(chat_id, date)
		return datetime.strptime(date + ' ' + time, '%d/%m/%Y %H:%M')

	@base_method
	def dt_with_tz(self, chat_id: int, dt: datetime):
		"""datetime with timezone"""
		tz = self.DBHandler.get_timezone(chat_id)
		if tz is None:
			return

		return dt + timedelta(hours=tz)

	@base_method
	def dt_utc(self, chat_id: int, dt: datetime):
		"""returns datetime in utc(unput dt must be in user local tz)"""
		tz = self.DBHandler.get_timezone(chat_id)
		if tz is None:
			return
		return dt - timedelta(hours=tz)
