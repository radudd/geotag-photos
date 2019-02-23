import logging
import yaml
import sys


def load_config():
    try:
        with open('config.yaml', 'r') as fh:
            config = yaml.load(fh)
            return config
    except FileNotFoundError:
        sys.exit(1)


def generate_logger():
    config = load_config()
    level = 'logging.' + config['log_level']
    filename = config['log_filename'] or None

    logger = logging.getLogger(__name__)
    # https://stackoverflow.com/questions/3467524/python-logger-logging-same-entry-numerous-times
    if logger.handlers:
        logger.handlers = []
    if filename:
        hdlr = logging.FileHandler(filename)
    else:
        hdlr = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr) 
    logger.setLevel(eval(level))
    return logger
