import multiprocessing

bind = 'unix:/tmp/naverwebtoonfeeds.sock'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'
user = 'www-data'
group = 'nogroup'
umask = '0007'
log_file = '/tmp/gunicorn_errors.log'
