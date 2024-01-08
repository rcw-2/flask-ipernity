"""
This module defines the Flask extension. 
"""

from __future__ import annotations

from functools import wraps
from logging import getLogger
from typing import Any, Callable, Dict, Mapping, TYPE_CHECKING

from flask import Flask, Response, redirect, current_app, g, request, session
from ipernity import IpernityAPI
from werkzeug.local import LocalProxy

# if TYPE_CHECKING:


log = getLogger(__name__)


default_flask_options = {
    'IPERNITY_API_KEY': None,
    'IPERNITY_API_SECRET': None,
    'IPERNITY_CACHE_REQUESTS': False,
    'IPERNITY_CACHE_MAX_AGE': 300,
    'IPERNITY_CALLBACK': True,
    'IPERNITY_CALLBACK_URL_PREFIX': '/ipernity',
    'IPERNITY_LOGIN': False,
    'IPERNITY_LOGIN_URL_PREFIX': '/ipernity',
    'IPERNITY_PERMISSIONS': {},
    'IPERNITY_PROXY_DOCS': True,
    'IPERNITY_PROXY_URL_PREFIX': '/ipernity',
    'IPERNITY_SESSION_PREFIX': 'ipernity_',
}


class Ipernity():
    """
    Class for the Flask Extension.
    
    Args:
        app:            The Flask application
    """
    
    def __init__(
        self,
        app: Flask|None = None,
    ):
        # Initialize app
        if app is not None:
            self.init_app(app)
    
    
    def init_app(self, app: Flask):
        """
        Initializes ``app`` for Flask-Ipernity.
        
        This is called from the constructor if you pass an app to it.
        See :external+flask:doc:`extensiondev` for more information.
        
        .. note::
            If you are using the
            :ref:`Flask-Login integration <flask-login-integration>`, make
            sure 
        
        Args:
            app:    `Flask`_ application
        """
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
        
        if app.config['IPERNITY_PROXY_DOCS']:
            log.debug('Preparing document proxy blueprint')
            from .proxy import proxy
            app.register_blueprint(
                proxy,
                url_prefix = app.config['IPERNITY_PROXY_URL_PREFIX']
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
        permissions: Mapping[str, str]|None = None,
        next_url: str|None = None
    ) -> Response:
        """
        Returns a redirect to the authorization URL.
        
        Creates an authorization URL on `www.ipernity.com` for the requested
        permissions with :attr:`~ipernity.auth.WebAuthHandler.auth_url` and
        redirects there. Ipernity then checks if these permissions have already
        been authorized and asks the user if not. After authorization, the user
        is redirected back to the application's callback.
        
        Args:
            permissions:    Contains the permissions to request. If ``None``,
                            the configuration value :data:`IPERNITY_PERMISSIONS`
                            is used. See there for data format.
            next_url:       URL to redirect to after returning from Ipernity.
        Returns:
            Redirect to the Ipernity authorization URL.
        """
        if permissions is None:
            permissions = current_app.config['IPERNITY_PERMISSIONS']
        log.debug('Authorizing for %s', permissions)
        if next_url is None:
            next_url = request.url
        self.session_set('next_url', next_url)
        return redirect(self.api.auth.auth_url(permissions))
    
    
    def set_token(self, frob: str|None = None):
        """
        Sets the API token from ``frob``.
        
        Args:
            frob:   See 
                `Ipernity Authentication <http://www.ipernity.com/help/api/auth.web.html>`_
        """
        log.debug('Setting token')
        if frob is None:
            log.debug('Getting frob from request')
            frob = request.args.get('frob')
        log.debug('Got frob %s', frob)
        
        # Get token and save it to session and API
        self.session_set('token', self.api.auth.getToken(frob)['auth'])
    
    
    def logout(self):
        """
        Logs out of Ipernity.
        
        Deletes all session variables starting with :data:`IPERNITY_SESSION_PREFIX`
        and removes the API token.
        """
        for key in list(session):
            if key.startswith(current_app.config['IPERNITY_SESSION_PREFIX']):
                del session[key]
        self.api.token = None

    
    @property
    def api(self) -> IpernityAPI:
        """
        The current Ipernity API.
        
        Depending on :data:`IPERNITY_CACHE_REQUESTS`, the type is
        :class:`~ipernity.api.IpernityAPI` or
        :class:`~flask_ipernity.cache.CachedIpernityAPI`.
        """
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
        
        :data:`IPERNITY_SESSION_PREFIX` is automatically prepended to ``key``.
        
        Args:
            key:        Name of the session variable.
            default:    Default value if variable is not present.
        Returns:
            The session variable.
        """
        return session.get(current_app.config['IPERNITY_SESSION_PREFIX'] + key, default)
    
    
    def session_set(self, key: str, value: Any):
        """
        Sets a session variable.
        
        :data:`IPERNITY_SESSION_PREFIX` is automatically prepended to ``key``.
        
        Args:
            key:    Name of the session variable.
            value:  New value for variable.
        """
        session[current_app.config['IPERNITY_SESSION_PREFIX'] + key] = value
    
    
    def session_pop(self, key: str, default: Any = None) -> Any:
        """
        Removes a session variable and returns it.
        
        :data:`IPERNITY_SESSION_PREFIX` is automatically prepended to ``key``.
        
        Args:
            key:        Name of the session variable.
            default:    Default value if variable is not present.
        Returns:
            The session variable.
        """
        return session.pop(current_app.config['IPERNITY_SESSION_PREFIX'] + key, default)


def _context_processor() -> Dict:
    return {
        'ipernity': ipernity,
    }


def _get_ipernity() -> Ipernity:
    return current_app.extensions['ipernity']


# Proxy for the current :class:`Ipernity` instance.
ipernity: Ipernity = LocalProxy(_get_ipernity)


def ipernity_auth_required(permissions: Mapping[str,str]|None = None) -> Callable:
    """
    Decorator for a view that requires Ipernity authentication.
    
    Args:
        permissions:    Contains the permissions required for the view. If
                        ``None``, the configuration value
                        :data:`IPERNITY_PERMISSIONS` is used. See
                        there for data format.
    """
    def decorate(f: Callable) -> Callable:
        nonlocal permissions
        
        @wraps(f)
        def view(*args, **kwargs):
            nonlocal permissions
            if permissions is None:
                permissions = current_app.config['IPERNITY_PERMISSIONS']
            if not ipernity.api.has_permissions(permissions):
                return ipernity.authorize(permissions)
            return f(*args, **kwargs)
        
        return view
    
    return decorate


