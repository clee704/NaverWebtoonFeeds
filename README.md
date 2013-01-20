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

* Clone this repository or download
  [this project from GitHub](https://github.com/clee704/NaverWebtoonFeeds).
* Create a virtual environment for the app (optional).
* Install required packages by running `pip install -r requirements.txt`.
  If you are going to use a database engine other than MySQL or a cache backend
  other than Redis, then you should install the packages for them yourself.
* Configure the app in `naverwebtoonfeeds/default_settings.local.py`.
  You can copy config options from `naverwebtoonfeeds/default_settings.py`.
* Set an environment variable `NAVERWEBTOONFEEDS_SETTINGS` to the path to your
  settings file
  (`/path/to/the/app/naverwebtoonfeeds/default_settings.local.py`).
* Run `python manage.py db create` to create database tables.
* Run `python manage.py db fill` to fill the database in. It may take a few
  hours.
* Run `gunicorn web:app` from the root directory of the project.

Sass and CoffeeScript binaries are required separately.


### Heroku

* Clone this repository or download
  [this project from GitHub](https://github.com/clee704/NaverWebtoonFeeds).
* Follow steps as described in
  [Deploying with Git](https://devcenter.heroku.com/articles/git#creating-a-heroku-remote)
  at the Heroku Dev Center.

You need to set a few config variables in your Heroku application. First,
set `NAVERWEBTOONFEEDS_SETTINGS` to `heroku_settings.py`. You can do this by
running `heroku config:set NAVERWEBTOONFEEDS_SETTINGS=heroku_settings.py`.

For other variables, see the comments in
`naverwebtoonfeeds/default_settings.py`.


License
-------

Naver Webtoon Feeds is licensed under [GNU Affero General Public License, version 3](http://www.gnu.org/licenses/agpl-3.0.html).
See `GNU-AGPL-v3.txt` for more information.
