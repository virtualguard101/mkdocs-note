import logging
import colorlog


class Logger:
	def __init__(self, name: str = "mkdocs.plugins", level: str = "INFO"):
		self.logger = colorlog.getLogger(name)
		self._setup_logger(level)

	def _setup_logger(self, level: str = "INFO"):
		"""Colorful log format"""
		if not self.logger.handlers:
			# formatter = colorlog.ColoredFormatter(
			#     '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
			#     log_colors={
			#         'DEBUG': 'cyan',
			#         'INFO': 'green',
			#         'WARNING': 'yellow',
			#         'ERROR': 'red',
			#         'CRITICAL': 'bold_red',
			#     }
			# )
			# handler = colorlog.StreamHandler()
			# handler.setFormatter(formatter)
			# self.logger.addHandler(handler)

			# Set log level dynamically based on configuration, use INFO if `level` is not valid
			log_level = getattr(logging, level.upper(), logging.INFO)
			self.logger.setLevel(log_level)

	def debug(self, msg: str):
		self.logger.debug(msg)

	def info(self, msg: str):
		self.logger.info(msg)

	def warning(self, msg: str):
		self.logger.warning(msg)

	def error(self, msg: str):
		self.logger.error(msg)

	def set_level(self, level: str):
		"""Dynamically update the logging level.

		Args:
		    level (str): The logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'), use INFO if not valid
		"""
		log_level = getattr(logging, level.upper(), logging.INFO)
		self.logger.setLevel(log_level)
