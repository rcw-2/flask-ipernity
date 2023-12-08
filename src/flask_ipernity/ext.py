"""
"""

from __future__ import annotations

from logging import getLogger
from typing import Callable, Dict, Mapping, TYPE_CHECKING

from flask import Flask, redirect, current_app, g, request, session
from ipernity import IpernityAPI
from werkzeug.local import LocalProxy

if TYPE_CHECKING:
    from flask import Response
    from flask_login import LoginManager


log = getLogger(__name__)


default_flask_options = {
    'IPERNITY_CACHE_MAX_AGE': 300,
    'IPERNITY_CALLBACK': False,
    'IPERNITY_CALLBACK_URL_PREFIX': '/ipernity',
    'IPERNITY_LOGIN': False,
    'IPERNITY_LOGIN_URL_PREFIX': '/ipernity',
    'IPERNITY_PERMISSIONS': {},
    'IPERNITY_CACHE_REQUESTS': False,
    'IPERNITY_SESSION_PREFIX': 'ipernity_',
}


class Ipernity():
    """
    
    Args:
        app:            The Flask application
        add_callback:   Add Ipernity callback
        login:          If given, use Ipernity as backend for Flask-Login
    """
    
    def __init__(
        self,
        app: Flask|None = None,
    ):
        # Initialize app
        if app is not None:
            self.init_app(app)
    
    
    def init_app(self, app: Flask):
        log.debug('Initializing Ipernity with app %s', app.name)
        app.extensions['ipernity'] = self
        
        # Default configuration
        for option, value in default_flask_options.items():
            app.config.setdefault(option, value)
        
        if app.config['IPERNITY_CALLBACK']:
            log.debug('Preparing callback blueprint')
            from .callback import callback
            app.register_blueprint(
                callback,
                url_prefix = app.config['IPERNITY_CALLBACK_URL_PREFIX']
            )
        
        if app.config['IPERNITY_LOGIN']:
            log.debug('Preparing login manager blueprint')
            from .login import ip_login, init_app as init_login
            app.register_blueprint(
                ip_login,
                url_prefix = app.config['IPERNITY_LOGIN_URL_PREFIX']
            )
            init_login(app)
        
        # 
        app.context_processor(_context_processor)
    
    
    def authorize(
        self,
        permissions: Mapping|None = None,
        next_url: str|None = None
    ) -> Response:
        if permissions is None:
            permissions = current_app.config['IPERNITY_PERMISSIONS']
        log.debug('Authorizing for %s', permissions)
        if next_url is None:
            next_url = request.url
        session['ipernity_next_url'] = next_url
        return redirect(self.api.auth.auth_url(permissions))
    
    
    def set_token(self, frob: str|None = None):
        log.debug('Setting token')
        if frob is None:
            log.debug('Getting frob from request')
            frob = request.args.get('frob')
        log.debug('Got frob %s', frob)
        
        # Get token and save it to session and API
        self.session_set('token', self.api.auth.getToken(frob)['auth'])
    
    
    def logout(self):
        for key in list(session):
            if key.startswith(current_app.config['IPERNITY_SESSION_PREFIX']):
                del session[key]
        self.api.token = None

    
    @property
    def api(self) -> IpernityAPI:
        """The current Ipernity API"""
        if 'ipernity_api' not in g:
            log.debug('Creating IpernityAPI object')
            kwargs = {
                'api_key':      current_app.config['IPERNITY_APP_KEY'],
                'api_secret':   current_app.config['IPERNITY_APP_SECRET'],
                'token':        self.session_get('token'),
                'auth':         'web',
            }

            if current_app.config['IPERNITY_CACHE_REQUESTS']:
                from .cache import CachedIpernityAPI
                g.ipernity_api = CachedIpernityAPI(
                    current_app.config['IPERNITY_CACHE_MAX_AGE'],
                    **kwargs
                )
            else:
                g.ipernity_api = IpernityAPI(**kwargs)
        
        return g.ipernity_api
    
    
    def session_get(self, key: str, default: Any = None) -> Any:
        """
        Returns a session variable.
        """
        return session.get(current_app.config['IPERNITY_SESSION_PREFIX'] + key, default)
    
    
    def session_set(self, key: str, value: Any):
        """Sets a session variable."""
        session[current_app.config['IPERNITY_SESSION_PREFIX'] + key] = value
    
    
    def session_pop(self, key: str, default: Any = None) -> Any:
        """
        Removes a session variable and returns it.
        """
        return session.pop(current_app.config['IPERNITY_SESSION_PREFIX'] + key, default)


def _context_processor() -> Dict:
    return {
        'ipernity': ipernity,
    }


def _get_ipernity() -> Ipernity:
    if 'ipernity_object' not in g:
        g.ipernity_object = current_app.extensions['ipernity']
    return g.ipernity_object


ipernity: Ipernity = LocalProxy(_get_ipernity)


