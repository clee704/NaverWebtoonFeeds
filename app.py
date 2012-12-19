import logging
from naverwebtoonfeeds import app

# Logging settings
app.logger.setLevel(app.config['LOG_LEVEL'])
formatter = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
app.logger.addHandler(stream_handler)
if app.config.get('SEND_EMAIL'):
    from logging.handlers import SMTPHandler
    smtp_handler = SMTPHandler(app.config['MAIL_HOST'],
                               app.config['MAIL_FROMADDR'],
                               app.config['MAIL_TOADDRS'],
                               app.config['MAIL_SUBJECT'],
                               app.config['MAIL_CREDENTIALS'],
                               app.config['MAIL_SECURE'])
    smtp_handler.setLevel(app.config['EMAIL_LEVEL'])
    smtp_handler.setFormatter(formatter)
    app.logger.addHandler(smtp_handler)

if __name__ == '__main__':
    try:
        import os
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except Exception:
        app.logger.critical('A critical error occurred', exc_info=True)
