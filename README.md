Naver Webtoon Feeds
===================

Provide feeds for Naver webtoons. Inspired by
[NaverComicFeed](https://bitbucket.org/dahlia/navercomicfeed). Unlike
NaverComicFeed, it embeds links in feeds, instead of actual comic images.

You can use the deployed app at
[naverwebtoonfeeds.herokuapp.com](http://naverwebtoonfeeds.herokuapp.com).


Installation
------------


### Your Server

* Clone this repository or download this project from
  [GitHub](https://github.com/clee704/NaverWebtoonFeeds).
* Create a virtual environment for the app (optional).
* Edit `requirements.txt` and save it as `requirements.local.txt` (optional;
  see Dependencies).
* Run `pip install -r requirements.txt`.
* Edit `naverwebtoonfeeds/default_settings.py` and save it as
  `naverwebtoonfeeds/default_settings.local.py`.
* Set an environment variable `NAVERWEBTOONFEEDS_SETTINGS` to the path to your
  settings file
  (`/path/to/the/app/naverwebtoonfeeds/default_settings.local.py`).
* Run `python manage.py update` to fill the database in. It may take a few
  hours.
* Run `gunicorn app:app` from the root directory of the project.


### Heroku

* Clone this repository or download this project from
  [GitHub](https://github.com/clee704/NaverWebtoonFeeds).
* Follow steps as described in
  [Deploying with Git](https://devcenter.heroku.com/articles/git#creating-a-heroku-remote)
  at the Heroku Dev Center.

You need to set a few config variables in your Heroku application. First,
set `NAVERWEBTOONFEEDS_SETTINGS` to `heroku_settings.py`. You can do this by
running `heroku config:set NAVERWEBTOONFEEDS_SETTINGS=heroku_settings.py`.

For other variables, see the comments in
`naverwebtoonfeeds/default_settings.py`.


Dependencies
------------

You can install the required packages by running
`pip install -r requirements.txt`. It will also install ipython, which is
optional, and MySQL-python and redis which can be replaced by other packages.

To use a database engine other than MySQL, replace the line starting with
`MySQL-python` with the following:

* PostgreSQL: psycopg2
* Oracle: cx\_oracle
* Microsoft SQL Server: pyodbc
* SQLite (not recommended for production): no required packages

For more information, see [the SQLAlchemy documentation on database URLs]
(http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls).

To use Memcached instead of Redis, change the line starting with `redis` to
`python-memcached`.
