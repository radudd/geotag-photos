import yaml
from collections import deque
import os.path
import time
import logger

log = logger.generate_logger()

"""
Simple cache implementation: takes as an argument function
and returns a wrapped function - wrapper
The cache will store the return values of the function(based on the arguments)
in a dict serialized as yaml with a max. capacity. The dict will have the
function arguments as key, and the result as value. An addional key for the
dictionary - 'indexes' will be used to hold information about the order of
items in the dictionary. The value of this key will be a dequeue.
The first class will be used just to load or persist cache from/to the disk.
"""


class DiskCache(object):
    def __init__(self, cache_file, enabled=True):
        self._cache_file = cache_file
        self._enabled = enabled

    def load(self):
        try:
            with open(self._cache_file, 'r') as f:
                self._cache = yaml.load(f)
        except FileNotFoundError:
            self._cache = {}
            self._cache['indexes'] = deque()
        finally:
            return self._cache

    def persist(self):
        with open(self._cache_file, 'w') as f:
            yaml.dump(self._cache, f)


class Cache(object):
    # Default load_from_cache to false.
    # In case, cache is hit, will be set to true
    load_from_cache = False

    def __init__(self, cache={}, maxsize=1024):
        self._cache = cache
        self._maxsize = maxsize

    def _update_cache(self, key, value):
        self._cache['indexes'].append(key)
        self._cache[key] = value

    def _evict_cache(self):
        if len(self._cache) >= self._maxsize:
            key = self._cache['indexes'].popleft()
            del self._cache[key]

    def __call__(self, function, *args):
        def wrapper(*args):
            # if args in cache dict -> return
            if args in self._cache:
                Cache.load_from_cache = True
                log.info("Hit cache for key: {}".format(args))
                return self._cache[args]
            # if not continue. Call the function to get the result
            # Add the result in the cache
            time.sleep(1)
            self._update_cache(args, function(*args))
            # Evict cache if max limit is reached
            self._evict_cache()
            return self._cache[args]
        return wrapper
