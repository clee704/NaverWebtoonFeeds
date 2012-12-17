Naver Webtoon Feeds
===================

Provide feeds for Naver webtoons. Inspired by
[NaverComicFeed](https://bitbucket.org/dahlia/navercomicfeed). Unlike
NaverComicFeed, it embeds links in feeds, instead of actual comic images.

Before starting the app, it is recommended to create and update the database
using the manager script. Run `python manage.py update`, or if you want to get
the progress, run `python manage.py update -d`. Without this, response time
would be large until the app is used many times.

When you use the default settings, make sure `db` and `db/naverwebtoonfeeds.db`
are both readable and writable by the server process.
