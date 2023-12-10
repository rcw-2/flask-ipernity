

from __future__ import annotations

from logging import getLogger
from typing import Any, TYPE_CHECKING

from flask_ipernity import Ipernity
import pytest

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient


log = getLogger(__name__)


@pytest.fixture
def app(base_app: Flask) -> Flask:
    from flask import jsonify, url_for, redirect
    from flask_login import LoginManager, login_required, current_user
    
    a = base_app
    a.config['IPERNITY_LOGIN'] = True
    LoginManager(a)
    Ipernity(a)
    
    @a.route('/user')
    def user():
        log.debug('Returning user info')
        return jsonify({
            'id':               current_user.get_id(),
            'is_active':        current_user.is_active,
            'is_anonymous':     current_user.is_anonymous,
            'is_authenticated': current_user.is_authenticated,
        })
    
    @a.route('/redir')
    def redir():
        return redirect(url_for(
            'ip_login.login'
        ))
    
    @a.route('/restricted')
    @login_required
    def restricted():
        return 'restricted'
    
    return a


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


def test_login_logout(browser, client, test_config):
    res = client.get('/ipernity/login')
    frob = browser.authorize(res.location)
    assert frob
    log.info('Calling callback with frob %s', frob)
    res = client.get('/ipernity/cb', query_string = {'frob': frob})
    log.info('Got result %d: %s', res.status_code, res.headers.get('content-type'))
    log.info('Checking token')
    res = client.get('/get_token')
    log.info(
        'Got result %d: %s (%s)',
        res.status_code,
        res.headers.get('content-type'),
        res.text
    )
    assert res.json['user']['username'] == test_config['ipernity']['username']
    log.info('Checking authentication status')
    res = client.get('/user')
    assert res.json['is_authenticated']
    log.info('Logging out')
    res = client.get('/ipernity/logout')
    log.info('Got result %d: %s', res.status_code, res.headers.get('content-type'))
    res = client.get('/get_token')
    assert res.json is None


def test_not_logged_in(client):
    log.info('Checking user status')
    res = client.get('/user')
    assert not res.json['is_active']
    assert not res.json['is_authenticated']
    assert res.json['is_anonymous']


def test_login_required(app, client):
    log.info('Getting login URL')
    res1 = client.get('/redir')
    log.info('Checking redirect of restricted view')
    res2 = client.get('/restricted')
    assert res2.location.startswith(res1.location + '?')

