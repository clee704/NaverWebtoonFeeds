web: gunicorn web:app -w 3 --access-logfile - --access-logformat '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
worker: python manage.py runworker --burst
