import cache
import pytest
import os

def test_cache_miss():

    cache_file = '.test1.yml'
    cache_obj = cache.DiskCache(cache_file)
    loaded_cache = cache_obj.load()

    @cache.Cache(cache=loaded_cache)
    def func(*args):
        test = ''.join([str(i) for i in args]) 
        print (test)
        return test

    func(1,2)
    assert cache.Cache.load_from_cache == False

def test_use_cache_from_disk():
    cache_file = '.test1.yml'
    cache_obj = cache.DiskCache(cache_file)
    loaded_cache = cache_obj.load()

    @cache.Cache(cache=loaded_cache)
    def func(*args):
        return ''.join([str(i) for i in args]) 

    func(1,2)
    cache_obj.persist(loaded_cache)

    func(1,2)
    assert cache.Cache.load_from_cache == True

    os.remove(cache_file)


if __name__ == "__main__":
     test_cache_miss()