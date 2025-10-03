import logging
import colorlog

class Logger:
    
    def __init__(self, name: str = __name__):
        self.logger = colorlog.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Colorful log format
        """
        if not self.logger.handlers:
            handler = colorlog.StreamHandler()
            formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red',
                }
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            # self.logger.setLevel(logging.DEBUG)
            self.logger.setLevel(logging.INFO)
    
    def debug(self, msg: str):
        self.logger.debug(msg)
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)
    
    def error(self, msg: str):
        self.logger.error(msg)
