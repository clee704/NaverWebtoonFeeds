from fakeredis import FakeRedis

from naverwebtoonfeeds.cache import CompressedRedisCache


def test_compressed_redis_cache():
    CompressedRedisCache.redis_class = FakeRedis
    cache = CompressedRedisCache()
    cache.set('foo', 'bar', timeout=100)
    assert cache.get('foo') == 'bar'
    cache.delete('foo')
    assert cache.get('foo') == None
