import logging
import os

class Logger:
    """Wrapper class for logging"""
    
    def __init__(self, name="zerotrace", log_file=None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            # Console handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
            
            # Optional file handler
            if log_file:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                fh = logging.FileHandler(log_file)
                fh.setLevel(logging.DEBUG)
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)
    
    def log_info(self, msg):
        self.logger.info(msg)
    
    def log_warning(self, msg):
        self.logger.warning(msg)
    
    def log_error(self, msg):
        self.logger.error(msg)
