import pytz

NAVER_TIMEZONE = pytz.timezone('Asia/Seoul')

BASE_URL = 'http://comic.naver.com/webtoon'
MOBILE_BASE_URL = 'http://m.comic.naver.com/webtoon'
URL = {
    'last_chapter': BASE_URL + '/detail.nhn?titleId={series_id}',
    'chapter': BASE_URL + '/detail.nhn?titleId={series_id}&no={chapter_id}',
    'mobile': MOBILE_BASE_URL + '/detail.nhn?titleId={series_id}&no={chapter_id}',
    'series': BASE_URL + '/list.nhn?titleId={series_id}',
    'series_by_day': BASE_URL + '/weekday.nhn',
    'completed_series': BASE_URL + '/finish.nhn',
}
