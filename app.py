import logging
from naverwebtoonfeeds import app

# Logging settings
loggers = [app.logger, logging.getLogger('sqlalchemy.engine')]
formatter = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
for logger in loggers:
    logger.setLevel(app.config['LOG_LEVEL'])
    logger.addHandler(stream_handler)
if app.config.get('SEND_EMAIL'):
    from logging.handlers import SMTPHandler
    mail_options = 'HOST FROMADDR TOADDRS SUBJECT CREDENTIALS SECURE'
    mail_config = (app.config['MAIL_' + x] for x in mail_options.split())
    smtp_handler = SMTPHandler(*mail_config)
    smtp_handler.setLevel(app.config['EMAIL_LEVEL'])
    smtp_handler.setFormatter(formatter)
    for logger in loggers:
        logger.addHandler(smtp_handler)

if __name__ == '__main__':
    try:
        import os
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except Exception:
        app.logger.critical('A critical error occurred', exc_info=True)
