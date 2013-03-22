#! /usr/bin/env python
import os
import re
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


__dir__ = os.path.dirname(__file__)


# Parse version since we can't import the package
# due to dependencies
def getversion():
    with open(os.path.join(__dir__, 'naverwebtoonfeeds', 'version.py')) as f:
        text = f.read()
        m = re.match("^__version__ = '(.*)'$", text)
        return m.group(1)


# Utility function to read the README file.
def read(fname):
    return open(os.path.join(__dir__, fname)).read()


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name = "naverwebtoonfeeds",
    version = getversion(),
    author = "Choongmin Lee",
    author_email = "choongmin@me.com",
    description = "Feeds for Naver webtoons",
    long_description = read("README.rst"),
    keywords = "rss atom feed naver webtoons webcomics",
    license = "GNU AGPL v3",
    url = "https://github.com/clee704/NaverWebtoonFeeds",
    packages = find_packages(),
    install_requires = [
        "Flask==0.9",
        "Flask-SQLAlchemy==0.16",
        "Flask-Cache==0.10.1",
        "Flask-Script==0.5.3",
        "Flask-Assets==0.8",
        "Flask-gzip==0.1",
        "requests==1.1.0",
        "lxml==3.1beta1",
        "BeautifulSoup==3.2.1",
        "netaddr==0.7.10",
        "pytz==2012j",
        "yuicompressor==2.4.7",
        "decorator==3.4.0",
    ],
    tests_require = [
        "pytest==2.3.4",
        "Flask-Testing==0.4",
        "mock==1.0.1",
        "PyYAML==3.10",
    ],
    extras_require = {
        "docs": ["Sphinx==1.1.3"],
    },
    cmdclass = {"test": PyTest},
    classifiers = [
        # Full list is here: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
