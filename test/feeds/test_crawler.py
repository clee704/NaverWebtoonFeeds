import pytest
from mock import Mock, patch
from netaddr import IPAddress

from naverwebtoonfeeds.feeds.crawler import AccessDenied, NaverBrowser

from ..conftest import mock_obj, read_fixture


@pytest.mark.parametrize('ip_addr', [
    '50.16.183.158',
    '50.17.104.181',
    '184.72.135.214',
    '184.73.32.85',
    '204.236.194.51',
])
@patch('naverwebtoonfeeds.feeds.crawler.get_public_ip')
def test_blacklisted_ip_addr(get_public_ip, ip_addr, app):
    with app.test_client():
        get_public_ip.return_value = IPAddress(ip_addr)
        browser = NaverBrowser()
        with pytest.raises(AccessDenied):
            browser.ensure_not_blacklisted()


@pytest.mark.parametrize('ip_addr', [
    '23.21.14.123',
    '23.22.101.166',
    '54.242.231.213',
    '54.242.243.101',
    '174.129.79.204',
])
@patch('naverwebtoonfeeds.feeds.crawler.get_public_ip')
def test_safe_ip_addr(get_public_ip, ip_addr, app):
    with app.test_client():
        get_public_ip.return_value = IPAddress(ip_addr)
        browser = NaverBrowser()
        browser.ensure_not_blacklisted()


def test_get_series_list(app):
    with app.test_client():
        browser = NaverBrowser()
        browser.session = Mock()
        browser.session.get.side_effect = lambda url, **kwargs: mock_obj(
            url=url, content=read_fixture('weekday.nhn.html'))
        assert (browser.get_series_list() ==
                read_fixture('weekday.nhn.parsed.yaml'))


@pytest.mark.parametrize('name', [
    '25455_325',
    '626938_1',
])
def test_get_series_info(name, app):
    with app.test_client():
        browser = NaverBrowser()
        browser.session = Mock()
        browser.session.get.side_effect = lambda url, **kwargs: mock_obj(
            url=url, content=read_fixture('{}.html'.format(name)))
        assert (browser.get_series_info(25455) ==
                read_fixture('{}.parsed.yaml'.format(name)))
