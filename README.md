Naver Webtoon Feeds
===================

Provide feeds for Naver webtoons. Inspired by
[NaverComicFeed](https://bitbucket.org/dahlia/navercomicfeed). Unlike
NaverComicFeed, it embeds links in feeds, instead of actual comic images.

You can use the deployed app at
[naverwebtoonfeeds.herokuapp.com](http://naverwebtoonfeeds.herokuapp.com).


Installation
------------

* Clone or download
  [this project from GitHub](https://github.com/clee704/NaverWebtoonFeeds).
* Create a virtual environment for the app (optional).
* Install required packages by running `pip install -r requirements.txt`.
  If you are going to use a database engine other than MySQL or a cache
  backend other than Redis, then you should install the packages for them
  yourself.
* Edit `env.template` and save it as `.env`.
* Set the environment variables from `.env`.
  You have several options here:
  * If you are using Heroku, prepend commands with `foreman run`.
  * If you are not using Heroku, prepend commands with `env $(cat .env | grep -v "^#")`.
  * If you are using virtualenvwrapper, go to `$VIRTUAL_ENV/bin` and
    edit `postactivate` and `postdeactivate` to set and unset variables.
* Run `python manage.py db create` to create database tables.
* Run `python manage.py db fill` to fill the database in.
  It may take a few hours.
* Run `gunicorn web:app` from the root directory of the project.

Sass and CoffeeScript binaries are required separately.

For development, set `NWF_MODE` to `development` and
change `naverwebtoonfeeds/config/development.py` to configure
the app. `.env` file is not needed in this case.


License
-------

Naver Webtoon Feeds is licensed under [GNU Affero General Public License, version 3](http://www.gnu.org/licenses/agpl-3.0.html).
See `GNU-AGPL-v3.txt` for more information.
