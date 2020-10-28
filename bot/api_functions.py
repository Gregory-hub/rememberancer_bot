import os
import requests
from urllib.parse import urlencode

from .extra.exceptions import TokenError, base_method
from .extra.logger import logger


TOKEN = os.getenv('REMEMBERANCER_BOT_TOKEN')
if TOKEN is None:
	raise TokenError


@base_method
def get(command: str, data: dict = None):
	"""function for making get request to telegram server with command"""
	if data:
		response = requests.get('https://api.telegram.org/bot{token}/{command}?{data}'.format(token=TOKEN, command=command, data=urlencode(data)))
	else:
		response = requests.get('https://api.telegram.org/bot{token}/{command}'.format(token=TOKEN, command=command))
	if response.status_code != 200:
		logger.warning('status code is {}'.format(response.status_code))
	return response


@base_method
def post(command: str, data: dict):
	"""function for making post request to telegram server with command"""
	response = requests.post('https://api.telegram.org/bot{token}/{command}'.format(token=TOKEN, command=command), data=data)
	if response.status_code != 200:
		logger.warning('status code:', response.status_code)
	return response
