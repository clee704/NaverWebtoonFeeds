#! /usr/bin/env python
import os
import sys

execfile("naverwebtoonfeeds/version.py")

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = [
    "naverwebtoonfeeds",
    "naverwebtoonfeeds.config",
    "naverwebtoonfeeds.feeds",
]

package_dir = 'naverwebtoonfeeds'

def recursive_include(dirname, base=''):
    base = os.path.join(package_dir, base)
    paths = []
    for dirpath, dirnames, filenames in os.walk(base, dirname):
        for name in filenames:
            paths.append(os.path.relpath(os.path.join(dirpath, name), base))
    return paths

package_data = {
    "naverwebtoonfeeds": recursive_include('static') + recursive_include('templates'),
    "naverwebtoonfeeds.feeds": recursive_include('templates', 'feeds'),
}

requires = [
    "Flask==0.10.1",
    "Flask-SQLAlchemy==1.0",
    "Flask-Cache==0.12",
    "Flask-Script==0.6.3",
    "Flask-Assets==0.8",
    "Flask-gzip==0.1",
    "requests==2.0.1",
    "lxml==3.2.4",
    "BeautifulSoup==3.2.1",
    "netaddr==0.7.10",
    "pytz==2013.8",
    "yuicompressor==2.4.8",
    "pyScss==1.2.0.post3",
    "PyYAML==3.10",
]

setup(
    name = "naverwebtoonfeeds",
    version = __version__,
    description = "Feeds for Naver webtoons",
    long_description = open("README.rst").read(),
    author = "Choongmin Lee",
    author_email = "choongmin@me.com",
    url = "https://github.com/clee704/NaverWebtoonFeeds",
    packages = packages,
    package_data = package_data,
    install_requires = requires,
    entry_points = {
        "console_scripts": [
            "manage.py = naverwebtoonfeeds.manage:main",
        ],
    },
    license = "GNU AGPL v3",
    keywords = "rss atom feed naver webtoons webcomics",
    classifiers = [
        # Full list is here: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
