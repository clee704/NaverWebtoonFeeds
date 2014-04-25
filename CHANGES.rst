0.3.dev1 (current)
------------------
- Cache is now required, not optional
- Change configuration

  - URL_ROOT is replaced by SERVER_NAME and PREFERRED_URL_SCHEME
  - FORCE_REDIRECT is renamed to REDIRECT_TO_CANONICAL_URL
  - REDIS_QUEUE_BURST_MODE_IN_HEROKU is renamed to
    START_HEROKU_WORKER_ON_REQUEST
  - IMGPROXY_URL_PATTERN now interpolates *v* instead of *variable*.
  - ENABLE_CACHE_COMPRESSION is removed. Use
    ``naverwebtoonfeeds.cache.compressedredis`` for CACHE_TYPE instead.

- Merge the ``updateseries`` command into the ``update`` command.
- Use bower for web libraries
- Use Less instead of pyScss
- Remove Heroku-specific files
- Miscellaneous improvements and refactorings


0.2 (Sep 24, 2013)
------------------
- Fix problems with redis queue workers (cde73a12_)

  - Failed jobs does not linger in redis anymore
  - Shutdown the worker early when it has an blocked IP address

- Improve robustness when scaling heroku (4d9060e6_)
- Fix parsing errors caused by markup changes (f1598b4e_)
- Fix admin emails are not registered from environment variable MAIL_TOADDRS
  (23b83f42_)
- Remove dependency on Ruby (a2b9e067_)

.. _cde73a12: https://github.com/clee704/NaverWebtoonFeeds/commit/cde73a123f0a6c47617f8c75132bbb7c45030fe1
.. _4d9060e6: https://github.com/clee704/NaverWebtoonFeeds/commit/4d9060e63a2cbb1051f16472a13e3de9084452d6
.. _f1598b4e: https://github.com/clee704/NaverWebtoonFeeds/commit/f1598b4e132ca4b63d06dd3233d78deccf3ae8c9
.. _23b83f42: https://github.com/clee704/NaverWebtoonFeeds/commit/23b83f422d206ddea810c4792542157d2ab7b711
.. _a2b9e067: https://github.com/clee704/NaverWebtoonFeeds/commit/a2b9e067a22ba2cde6bafc71222bb843d04878e5


0.1.0 (Mar 23, 2013)
--------------------
- First release
