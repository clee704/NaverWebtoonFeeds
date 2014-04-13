"""
    naverwebtoonfeeds.commands.base
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements a customized version of :class:`flask_script.Manager`.

"""
import logging.config
from subprocess import call

import yaml
from flask_script import Manager as ManagerBase
from flask_script.commands import Command, Option

from ..app import create_app


logging_config = yaml.load("""
version: 1
formatters:
    default:
        format: '%(asctime)s %(name)s [%(levelname)s] %(message)s'
        datefmt: '%Y-%m-%d %H:%M:%S'
handlers:
    console:
        level: DEBUG
        class: logging.StreamHandler
        formatter: default
root:
    level: DEBUG
    handlers: [console]
loggers:
    naverwebtoonfeeds:
        level: DEBUG
    sqlalchemy.engine:
        level: INFO
""")


def _create_app(log, log_sql):
    logging_config['root']['level'] = log.upper()
    logging_config['loggers']['sqlalchemy.engine']['level'] = log_sql.upper()
    logging.config.dictConfig(logging_config)
    return create_app()


class Manager(ManagerBase):

    log_option = Option('--log',
                        metavar='LEVEL',
                        default='DEBUG',
                        help='specify log level')
    log_sql_option = Option('--log-sql',
                            metavar='LEVEL',
                            default='WARNING',
                            help='specify log level for SQLAlchemy')

    def __init__(self, **kwargs):
        kwargs['with_default_commands'] = False
        super(Manager, self).__init__(_create_app, **kwargs)
        if not kwargs.get('help'):  # top-level manager
            self._options.append(self.log_option)
            self._options.append(self.log_sql_option)

    def add_external_command(self, name, command_line_args, help=None):
        def run(args):
            call(list(command_line_args) + list(args))
        command = Command()
        command.run = run
        command.capture_all_args = True
        command.__doc__ = help
        self.add_command(name, command)
