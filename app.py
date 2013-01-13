from naverwebtoonfeeds import app

try:
    from naverwebtoonfeeds.lib.naver import get_public_ip
    app.logger.warning('Current IP: %s', get_public_ip())
except:
    pass

if __name__ == '__main__':
    try:
        import os
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except:
        app.logger.critical('A critical error occurred', exc_info=True)
