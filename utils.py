import logging
import logging.handlers


def setup_logger(name: str = None, root_level=logging.INFO, console_level=logging.INFO, file_level=logging.INFO, file_name='file.log') -> logging.Logger:
    logger = logging.getLogger(name)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    logger.setLevel(root_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(console_level)
    stream_handler.setFormatter(formatter)

    file_handler = logging.handlers.TimedRotatingFileHandler(filename=file_name, when='midnight', backupCount=10)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(file_level)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
