import os
import psycopg2
from logging import Logger
from datetime import datetime

from .extra.exceptions import TokenError, base_method
from .api_functions import post


@base_method
def connect_to_db(logger: Logger, dbname: str = 'rememberancer', user: str = 'postgres', password: str = 'postgres', host: str = 'localhost', chat_id: int = None):
	"""connects to database. returns None if fails"""
	try:
		con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
		return con
	except psycopg2.OperationalError:
		logger.error("database doesn't exist")
		if chat_id is not None:
			post('sendMessage', data={'chat_id': chat_id, 'text': "Error with connection to database. It's bad. Trying again won't help. I'm useless piece of garbage. Try something else. Sorry for this"})
		return


class DBHandler:
	"""Class for interacting with database"""

	def __init__(self, logger: Logger):
		# all code uses one logger
		self.logger = logger
		self.TOKEN = os.getenv('REMEMBERANCER_BOT_TOKEN')
		if self.TOKEN is None:
			raise TokenError
		self.mode_list = ['normal', 'reminder', 'timezone', 'delete']
		self.awaits_for_list = ['date', 'time', 'text']

	@base_method
	def set_reminder(self, chat_id: int, dt: datetime, reminder_text: str):
		"""adds reminder to database"""
		if reminder_text == '-':
			reminder_text = ''

		con = connect_to_db(
			logger=self.logger,
			chat_id=chat_id
		)
		if con is None:
			return False

		cur = con.cursor()

		try:
			cur.execute("INSERT INTO reminder(chat_id, reminder_date, reminder_text) VALUES({chat_id}, '{dt}', '{text}')".format(chat_id=chat_id, dt=dt.strftime("%Y-%m-%d %H:%M:%S"), text=reminder_text))
		except psycopg2.errors.UniqueViolation:
			post('sendMessage', data={'chat_id': chat_id, 'text': 'Error. You already have reminder with the same time'})
			return False

		con.commit()
		cur.close()
		con.close()

		return True

	@base_method
	def get_chat_reminder_by_dt(self, chat_id: int, dt: datetime):
		"""queries db using chat_id and datetime and returns reminder dict"""
		con = connect_to_db(
			logger=self.logger,
		)
		if con is None:
			return None

		cur = con.cursor()

		cur.execute("SELECT chat_id, reminder_date, reminder_text FROM reminder WHERE chat_id = {chat_id} and reminder_date = TIMESTAMP '{dt.year}-{dt.month}-{dt.day} {dt.hour}:{dt.minute}'".format(chat_id=chat_id, dt=dt))
		result = cur.fetchall()
		if result == []:
			reminder = None
		else:
			reminder = result[0]

		cur.close()
		con.close()

		keys = ['chat_id', 'reminder_date', 'reminder_text']
		if reminder:
			return dict(zip(keys, reminder))
		else:
			return None

	@base_method
	def get_reminders_to_send(self):
		"""returns list of dicts for every reminder"""

		con = connect_to_db(
			logger=self.logger,
		)
		if con is None:
			return None

		cur = con.cursor()

		cur.execute("SELECT chat_id, reminder_date, reminder_text FROM reminder WHERE reminder_date - NOW() AT TIME ZONE 'UTC' < INTERVAL '1 second'")
		reminders = cur.fetchall()

		cur.close()
		con.close()

		keys = ['chat_id', 'reminder_date', 'reminder_text']
		return list(map(lambda rem: dict(zip(keys, rem)), reminders))

	@base_method
	def delete_reminder(self, reminder: dict):
		"""deletes reminder"""
		chat_id = reminder['chat_id']
		con = connect_to_db(
			logger=self.logger,
			chat_id=chat_id
		)
		if con is None:
			return

		cur = con.cursor()

		del_chat_id = reminder['chat_id']
		del_dt = reminder['reminder_date']

		cur.execute("DELETE FROM reminder WHERE reminder_date = TIMESTAMP '{del_dt}' AND chat_id = {del_chat_id}".format(del_dt=del_dt, del_chat_id=del_chat_id))

		con.commit()
		cur.close()
		con.close()

	@base_method
	def set_chat_mode(self, chat_id: int, mode: str, awaits_for: str = None):
		"""Changes chat mode in chat_mode table"""

		if mode not in self.mode_list:
			raise ValueError
		if mode == 'normal' and awaits_for is not None:
			raise ValueError
		if mode == 'reminder' and awaits_for is None:
			raise ValueError
		if mode == 'reminder' and awaits_for not in self.awaits_for_list:
			raise ValueError
		if mode == 'timezone' and awaits_for is not None:
			raise ValueError
		if mode == 'delete' and awaits_for is not None:
			raise ValueError

		if awaits_for is None:
			awaits_for = ''

		con = connect_to_db(
			logger=self.logger,
			chat_id=chat_id
		)
		if con is None:
			return
		cur = con.cursor()

		cur.execute("INSERT INTO chat(chat_id, chat_mode, awaits_for) VALUES({chat_id}, '{mode}', '{awaits_for}') ON CONFLICT(chat_id) DO UPDATE SET chat_mode = '{mode}', awaits_for = '{awaits_for}'".format(chat_id=chat_id, mode=mode, awaits_for=awaits_for))

		con.commit()
		cur.close()
		con.close()

	@base_method
	def get_chat_mode(self, chat_id):
		"""returns chat_mode and awaits_for from chat_status table"""
		con = connect_to_db(
			logger=self.logger,
			chat_id=chat_id
		)
		if con is None:
			return
		cur = con.cursor()

		cur.execute("SELECT chat_mode, awaits_for FROM chat WHERE chat_id = {chat_id}".format(chat_id=chat_id))

		result = cur.fetchall()
		if len(result) > 0:
			chat_mode, awaits_for = result[0]
		else:
			chat_mode, awaits_for = None, None

		cur.close()
		con.close()

		return chat_mode, awaits_for

	@base_method
	def save_temp_date(self, chat_id: int, date: str):
		"""saves date to temp_datetime table"""
		con = connect_to_db(
			logger=self.logger,
			chat_id=chat_id
		)
		if con is None:
			return
		cur = con.cursor()

		cur.execute("INSERT INTO temp_datetime(chat_id, reminder_date) VALUES({chat_id}, '{date}') ON CONFLICT(chat_id) DO UPDATE SET reminder_date = '{date}'".format(chat_id=chat_id, date=date))

		con.commit()
		cur.close()
		con.close()

	@base_method
	def save_temp_time(self, chat_id: int, time: str):
		"""saves time to temp_dateitme table"""
		con = connect_to_db(
			logger=self.logger,
			chat_id=chat_id
		)
		if con is None:
			return
		cur = con.cursor()

		cur.execute("INSERT INTO temp_datetime(chat_id, reminder_time) VALUES({chat_id}, '{time}') ON CONFLICT(chat_id) DO UPDATE SET reminder_time = '{time}'".format(chat_id=chat_id, time=time))

		con.commit()
		cur.close()
		con.close()

	@base_method
	def get_temp_date(self, chat_id: int):
		"""returns date from temp_datetime"""
		con = connect_to_db(
			logger=self.logger,
			chat_id=chat_id
		)
		if con is None:
			return
		cur = con.cursor()

		cur.execute("SELECT reminder_date FROM temp_datetime WHERE chat_id = {chat_id}".format(chat_id=chat_id))

		date = cur.fetchall()[0][0]

		con.commit()
		cur.close()
		con.close()

		return date

	@base_method
	def get_temp_time(self, chat_id: int):
		"""returns time from temp_datetime"""
		con = connect_to_db(
			logger=self.logger,
			chat_id=chat_id
		)
		if con is None:
			return
		cur = con.cursor()

		cur.execute("SELECT reminder_time FROM temp_datetime WHERE chat_id = {chat_id}".format(chat_id=chat_id))

		time = cur.fetchall()[0][0]

		con.commit()
		cur.close()
		con.close()

		return time

	@base_method
	def get_user_reminders(self, chat_id: int):
		"""returns chat reminders from database"""
		con = connect_to_db(
			logger=self.logger,
			chat_id=chat_id
		)
		if con is None:
			return
		cur = con.cursor()

		cur.execute("SELECT chat_id, reminder_date, reminder_text FROM reminder WHERE chat_id = {chat_id}".format(chat_id=chat_id))
		reminders = cur.fetchall()

		cur.close()
		con.close()

		keys = ['chat_id', 'reminder_date', 'reminder_text']
		return list(map(lambda rem: dict(zip(keys, rem)), reminders))

	@base_method
	def set_timezone(self, chat_id: int, tz: int):
		"""sets chat timezone"""
		con = connect_to_db(
			logger=self.logger,
			chat_id=chat_id
		)
		if con is None:
			return
		cur = con.cursor()

		cur.execute("INSERT INTO chat(chat_id, chat_mode, timezone) VALUES({chat_id}, 'normal', {tz}) ON CONFLICT(chat_id) DO UPDATE SET timezone={tz}".format(chat_id=chat_id, tz=tz))

		con.commit()
		cur.close()
		con.close()

	@base_method
	def get_timezone(self, chat_id: int):
		"""returns timezone of chat.
		tz is difference between utc time and local user time in hours"""
		con = connect_to_db(
			logger=self.logger,
			chat_id=chat_id
		)
		if con is None:
			return
		cur = con.cursor()

		cur.execute("SELECT timezone FROM chat WHERE chat_id = {chat_id}".format(chat_id=chat_id))
		result = cur.fetchall()
		if result == []:
			tz = None
		else:
			tz = result[0][0]

		cur.close()
		con.close()

		return tz
