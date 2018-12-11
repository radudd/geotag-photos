from cache import DiskCache
import logger

disk_cache = DiskCache('.cache.yml')
loaded_cache = disk_cache.load()

log = logger.generate_logger()