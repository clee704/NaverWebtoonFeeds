import pytz

NAVER_TIMEZONE = pytz.timezone('Asia/Seoul')

BASE_URL = 'http://comic.naver.com/webtoon'
MOBILE_BASE_URL = 'http://m.comic.naver.com/webtoon'
SUBPATHS = {
    'last_chapter': '/detail.nhn?titleId={series_id}',
    'chapter': '/detail.nhn?titleId={series_id}&no={chapter_id}',
    'series': '/list.nhn?titleId={series_id}',
    'series_by_day': '/weekday.nhn',
    'completed_series': '/finish.nhn',
}
URLS = dict((key, BASE_URL + SUBPATHS[key]) for key in SUBPATHS)
MOBILE_URLS = dict((key, MOBILE_BASE_URL + SUBPATHS[key]) for key in SUBPATHS)
