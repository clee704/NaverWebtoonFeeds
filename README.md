Naver Webtoon Feeds
===================

Provide feeds for Naver webtoons. Inspired by
[NaverComicFeed](https://bitbucket.org/dahlia/navercomicfeed). Unlike
NaverComicFeed, it embeds links in feeds, instead of actual comic images.

Before first using the app, the database should be filled by running the
command `python manage.py update`. It may take a few hours to complete this
task.

You can use the deployed app at
[naverwebtoonfeeds.herokuapp.com](http://naverwebtoonfeeds.herokuapp.com).

Dependencies
------------

You can install the required packages by running
`pip install -r requirements.txt`. Although ipython, MySQL-python, and redis
is included in the requirements file, you can replace them with other packages.
You can use packages such as psycopg2 and pymssql instead of MySQL-python and
python-memcached instead of redis. ipython is included for convenience and not
required at all.
