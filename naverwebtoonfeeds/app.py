"""
    naverwebtoonfeeds.app
    ~~~~~~~~~~~~~~~~~~~~~

    Functions for creating and configuring the Flask app.

"""
import os

from flask import Flask, g, redirect, request, send_from_directory

from ._compat import string_types, urlparse, urlunparse
from .config import DefaultConfig, instance_path, resolve_instance_path
from .ext import assets_env, cache, db, gzip
from .feeds import worker  # Necessary for signals
from .feeds.views import feeds
from .filters import register_filters


default_blueprints = [feeds]


def create_app(config_pyfile_or_dict=None, blueprints=None):
    """Creates a Flask app. If *blueprints* is None, the default blueprints in
    :data:`default_blueprints` will be used.

    """
    app = Flask(__name__.rsplit('.', 1)[0],
                instance_path=instance_path,
                instance_relative_config=True)
    configure_app(app, config_pyfile_or_dict)
    register_blueprints(app, blueprints or default_blueprints)
    register_extensions(app)
    register_request_handlers(app)
    configure_jinja(app)
    configure_assets(app)
    return app


def configure_app(app, config_pyfile_or_dict=None):
    """Configures the app. Configuration is applied in the following order:

    1. :class:`naverwebtoonfeeds.config.DefaultConfig`
    2. From *NWF_SETTINGS* environment variable if it is set.
    3. From *config_pyfile_or_dict*. It can be a path to the Python file or
       a dictionary.

    Note that if the path to the configuration file can be absolute or relative
    to the instance folder.

    """
    app.config.from_object(resolve_instance_path(DefaultConfig))
    if os.environ.get('NWF_SETTINGS'):
        app.config.from_envvar('NWF_SETTINGS', silent=False)
    if isinstance(config_pyfile_or_dict, string_types):
        app.config.from_pyfile(config_pyfile_or_dict)
    elif config_pyfile_or_dict is not None:
        app.config.update(config_pyfile_or_dict)


def register_blueprints(app, blueprints):
    """Registers blueprints to the app."""
    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def register_extensions(app):
    """Registers extensions for the app."""
    assets_env.init_app(app)
    db.init_app(app)
    cache.init_app(app)
    if app.config.get('GZIP'):
        gzip.init_app(app)


def register_request_handlers(app):

    if app.config['REDIRECT_TO_CANONICAL_URL']:
        @app.before_request
        def redirect_to_canonical_url():
            urlparts = urlparse(request.url)
            if urlparts.netloc != app.config['SERVER_NAME']:
                urlparts_list = list(urlparts)
                urlparts_list[1] = app.config['SERVER_NAME']
                return redirect(urlunparse(urlparts_list), 301)


def configure_jinja(app):
    """Registers template filters and context processors."""
    register_filters(app)


def configure_assets(app):
    """Adds a URL rule for generated assets."""

    def send_static_file(filename):
        cache_timeout = app.get_send_file_max_age(filename)
        return send_from_directory(app.config['ASSETS_DIRECTORY'], filename,
                                   cache_timeout=cache_timeout)

    app.add_url_rule(app.config['ASSETS_URL'] + '/<path:filename>',
                     endpoint='assets',
                     view_func=send_static_file)
