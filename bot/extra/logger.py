import logging
from logging import config


config_dict = {
	'version': 1,
	'formatters': {
		'simple': {
			'format': '%(levelname)s %(asctime)s in %(module)s.%(funcName)s: %(message)s',
			'datefmt': '%Y-%m-%d %H:%M:%S'
		},
	},
	'handlers': {
		'simple': {
			'class': 'logging.FileHandler',
			'filename': 'bot.log',
			'level': 'WARNING',
			'formatter': 'simple'
		}
	},
	'loggers': {
		'bot_logger': {
			'level': 'WARNING',
			'handlers': {
				'simple'
			}
		}
	}
}

# configure logger
config.dictConfig(config_dict)

# create logger
logger = logging.getLogger('bot_logger')
