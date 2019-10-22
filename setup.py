#! /usr/bin/env python
import os
import sys
from setuptools.command.test import test
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from naverwebtoonfeeds import __version__


packages = [
    'naverwebtoonfeeds',
    'naverwebtoonfeeds.feeds',
]
install_requires = [
    'Flask==1.0',
    'Flask-Assets==0.9',
    'Flask-Cache==0.12',
    'Flask-gzip==0.1',
    'Flask-Script==0.6.7',
    'Flask-SQLAlchemy==1.0',
    'requests==2.2.1',
    'lxml==3.3.4',
    'BeautifulSoup==3.2.1',
    'PyYAML==3.11',
    'yuicompressor==2.4.8',
    'pytz==2013.8',
    'netaddr==0.7.11',
    'blinker==1.3',
]
test_requires = [
    'pytest == 2.5.2',
    'pytest-cov == 1.6',
    'pytest-pep8 == 1.0.5',
    'mock == 1.0.1',
    'fakeredis == 0.4.2',
    'redis == 2.9.1',
    'rq == 0.3.13',
    'cssselect == 0.9.1',
]
dependency_links = [
    'https://github.com/clee704/fakeredis/tarball/9d3f8acdd337f39f15e36cf333f23083c49cd9f4',
]


def readme():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
            return f.read()
    except Exception:
        return ''


def recursive_include(dirname, base=''):
    base = os.path.join('naverwebtoonfeeds', base)
    paths = []
    for dirpath, dirnames, filenames in os.walk(base, dirname):
        for name in filenames:
            paths.append(os.path.relpath(os.path.join(dirpath, name), base))
    return paths


class pytest(test):

    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        from pytest import main
        errno = main(self.test_args)
        raise SystemExit(errno)


# Hack to prevent stupid TypeError: 'NoneType' object is not callable error on
# exit of python setup.py test # in multiprocessing/util.py _exit_function when
# running python setup.py test (see
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html)
try:
    import multiprocessing
except ImportError:
    pass


package_data = {
    'naverwebtoonfeeds': (recursive_include('static') +
                          recursive_include('templates')),
    'naverwebtoonfeeds.feeds': recursive_include('templates', 'feeds'),
}


setup(
    name='naverwebtoonfeeds',
    version=__version__,
    url='https://github.com/clee704/NaverWebtoonFeeds',
    license='GNU AGPL v3',
    author='Choongmin Lee',
    author_email='choongmin@me.com',
    description='A web app for generating Atom feeds for Naver webtoons',
    long_description=readme(),
    packages=packages,
    package_data=package_data,
    install_requires=install_requires,
    tests_requires=test_requires,
    dependency_links=dependency_links,
    cmdclass={'test': pytest},
    entry_points={
        'console_scripts': [
            'nwf=naverwebtoonfeeds.commands:manager.run',
        ],
    },
    keywords='rss atom feed subscription naver webtoon webcomic',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
