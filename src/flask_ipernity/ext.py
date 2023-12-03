"""
"""

from __future__ import annotations

from logging import getLogger
from typing import Callable, Dict, Mapping, TYPE_CHECKING

from flask import Flask, redirect, current_app, g, request, session
from ipernity import IpernityAPI
from werkzeug.local import LocalProxy

from .cache import CachedIpernityAPI

if TYPE_CHECKING:
    from flask import Response
    from flask_login import LoginManager


log = getLogger(__name__)


class Ipernity():
    """
    """
    
    def __init__(self, app: Flask|None = None, login: LoginManager|None = None):
        self.login = login
        # Initialize app
        if app is not None:
            self.init_app(app)
    
    
    def init_app(self, app: Flask):
        log.debug('Initializing Ipernity with app %s', app.name)
        app.extensions['ipernity'] = self
        
        # Default configuration
        app.config.setdefault('IPERNITY_CACHE_REQUESTS', False)
        app.config.setdefault('IPERNITY_CACHE_MAX_AGE', 300)
        app.config.setdefault('IPERNITY_CALLBACK', False)
        app.config.setdefault('IPERNITY_CALLBACK_URL_PREFIX', '/flask_ipernity_callback')
        app.config.setdefault('IPERNITY_LOGIN', False)
        app.config.setdefault('IPERNITY_LOGIN_URL_PREFIX', '/flask_ipernity_login')
        app.config.setdefault('IPERNITY_PERMISSIONS', {})
        app.config.setdefault('IPERNITY_LOGIN_RULE', '/login')
        
        if app.config['IPERNITY_CALLBACK']:
            log.debug('Preparing callback blueprint')
            from .callback import callback
            app.register_blueprint(
                callback,
                url_prefix = app.config['IPERNITY_CALLBACK_URL_PREFIX']
            )
        
        if self.login is not None:
            log.debug('Preparing login manager blueprint')
            from .login import ip_login, init_app as init_login
            app.register_blueprint(
                ip_login,
                url_prefix = app.config['IPERNITY_LOGIN_URL_PREFIX']
            )
            init_login(app, self)
        
        # 
        app.context_processor(_context_processor)
    
    
    def authorize(self, permissions: Mapping, next_url: str|None = None) -> Response:
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
        session['ipernity_token'] = self.api.auth.getToken(frob)['auth']
    
    
    @property
    def api(self) -> IpernityAPI:
        """The current Ipernity API"""
        if 'ipernity_api' not in g:
            log.debug('Creating IpernityAPI object')
            kwargs = {
                'api_key':      current_app.config['IPERNITY_APP_KEY'],
                'api_secret':   current_app.config['IPERNITY_APP_SECRET'],
                'token':        session.get('ipernity_token'),
                'auth':         'web',
            }

            if current_app.config['IPERNITY_CACHE_REQUESTS']:
                g.ipernity_api = CachedIpernityAPI(
                    current_app.config['IPERNITY_CACHE_MAX_AGE'],
                    **kwargs
                )
            else:
                g.ipernity_api = IpernityAPI(**kwargs)
        
        return g.ipernity_api


def _context_processor() -> Dict:
    return {
        'ipernity': ipernity,
    }


def _get_ipernity() -> Ipernity:
    if 'ipernity_object' not in g:
        g.ipernity_object = current_app.extensions['ipernity']
    return g.ipernity_object


ipernity: Ipernity = LocalProxy(_get_ipernity)


