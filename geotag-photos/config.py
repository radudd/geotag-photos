from cache import DiskCache
import logger

loaded_cache = DiskCache('.cache.yml').load()
log = logger.generate_logger()
