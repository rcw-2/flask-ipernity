"""
Authentication Flask Extensions
"""

from __future__ import annotations

from logging import getLogger
from typing import List, Mapping, TYPE_CHECKING

from flask import (
    Blueprint, Flask, Response,
    redirect,
    current_app, request, session
)
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    current_user, user_logged_out
)
from werkzeug.local import LocalProxy

from .ext import ipernity

if TYPE_CHECKING:
    from ipernity import IpernityAPI
    from .ext import Ipernity


log = getLogger(__name__)    


ip_login = Blueprint('flask_ipernity_login', __name__)


def init_app(app: Flask, ipernity: Ipernity):
    login: LoginManager = ipernity.login
    login.login_view = 'flask_ipernity_login.login'
    login.user_loader(load_user)
    user_logged_out.connect(on_logout)


@ip_login.route('/login')
def login() -> Response:
    log.debug('Login called')
    return ipernity.authorize(
        current_app.config['IPERNITY_PERMISSIONS'],
        request.args.get('next')
    )


@ip_login.route('/logout')
def logout() -> Response:
    """Logout"""
    log.debug('Logout called')
    logout_user()
    return redirect('/')


def do_login():
    login_user(User(ipernity.api))


def load_user(id_: str) -> User:
    """
    Loads a user from the session.
    """
    if not ipernity.api.token:
        return None
    if not ipernity.api.user_info:
        log.error('No user info for API token, dumping token')
        ipernity_logout()
        return None
    if ipernity.api.user_info['user_id'] != id_:
        log.error(
            'User mismatch (given %s, token %s), dumping token',
            id_,
            ipernity.api.user_info['user_id']
        )
        ipernity_logout()
        return None
    
    return User(ipernity.api)


def on_logout(sender: Flask, user: User):
    ipernity_logout()


def ipernity_logout():
    for var in ['ipernity_token', 'ipernity_cache']:
        if var in session:
            del session[var]
    ipernity.api.token = None


class User(UserMixin):
    """
    A user
    """
        
    def __init__(
        self,
        api: IpernityAPI
    ):
        log.debug('Creating Ipernity user')
        self._api = api
    
    def __repr__(self) -> str:
        return '<User({})>'.format(self.get_id())
    
    def get_id(self) -> str:
        return self._api.user_info['user_id']
    
    @property
    def is_authenticated(self) -> bool:
        if self._api.token is None:
            return False
        return True
    
    @property
    def username(self) -> str:
        if self.is_authenticated:
            return self._api.user_info['username']
        else:
            return ''
    
    @property
    def realname(self) -> str:
        if self.is_authenticated:
            return self._api.user_info['realname']
        else:
            return ''


