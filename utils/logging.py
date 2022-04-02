import logging
from tqdm import tqdm


logging_format = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
logFormatter = logging.Formatter(logging_format)
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)


def logging_setup_file(file_path):
    fileHandler = logging.FileHandler(file_path)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)


def logging_setup_tqdm():
    tqdmHandler = TqdmLoggingHandler()
    tqdmHandler.setFormatter(logFormatter)
    rootLogger.addHandler(tqdmHandler)


def logging_setup_concole():
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
