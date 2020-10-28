from bot.bot import Bot
from bot.extra.logger import logger


bot = Bot()

print('start')
while True:
	try:
		bot.start()
	except Exception as e:
		print(e)
		logger.error('something went wrong')
