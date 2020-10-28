import functools
import traceback

from .logger import logger


class BotError(Exception):
	pass


class TokenError(BotError):

	def __init__(self):
		self.message = 'Token is missing or incorrect'
		super().__init__(self.message)


def base_method(fun):
	"""wrapper for all methods and functions. handles exceptions occured in fun"""
	@functools.wraps(fun)
	def inner(*args, **kwargs):
		try:
			return fun(*args, **kwargs)
		except Exception as e:
			print(traceback.format_exc())
			logger.error(e)
			raise e
	return inner
