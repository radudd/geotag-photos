from cache import DiskCache
import logger
import yaml
import mongo


def load_config():
    try:
        with open('config.yaml', 'r') as fh:
            config = yaml.load(fh)
            return config
    except FileNotFoundError:
        sys.exit(1)


def check_db():
    try:
        with mongo.MongoConnector() as db:
            if db.find_one():
                return True
    except (errors.ConnectionFailure, errors.ConfigurationError) as e:
        return False


mongo = check_db()
config = load_config()
log = logger.generate_logger()
cache = DiskCache(config['cache_file'])
