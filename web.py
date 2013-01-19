from naverwebtoonfeeds import app, cache

# Code that only executed when a web server starts, not
# for workers or management scripts.

# Purge the index page cache to generate assets.
cache.delete('feed_index')
