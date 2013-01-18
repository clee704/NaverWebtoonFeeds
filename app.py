import logging
from naverwebtoonfeeds import app, logger

if __name__ == '__main__':
    try:
        import os
        port = int(app.config.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except:
        logger.critical('A critical error occurred', exc_info=True)
