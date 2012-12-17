Naver Webtoon Feeds
===================

Provide feeds for Naver webtoons. Inspired by
[NaverComicFeed](https://bitbucket.org/dahlia/navercomicfeed). Unlike
NaverComicFeed, it embeds links in feeds, instead of actual comic images.

Before starting the app, it is recommended to seed the database using the
manager script. Run `python manage.py update` (with `-d` option to enable
progress). Response time could be large until the app is viewed many times.

When using SQLite3, make sure `db` and `db/naverwebtoonfeeds.db` are both
readable and writable by the server process.
