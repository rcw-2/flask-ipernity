
from logging import getLogger

import pytest


log = getLogger(__name__)


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
    with pytest.raises(KeyError):
        client.get('/get_token')


def test_not_logged_in(client):
    log.info('Checking user status')
    res = client.get('/user')
    assert not res.json['is_active']
    assert not res.json['is_authenticated']
    assert res.json['is_anonymous']


def test_login_required(app, client):
    from flask import url_for, redirect
    from flask_login import login_required
    
    @app.route('/redir')
    def redir():
        return redirect(url_for('flask_ipernity_login.login'))
    
    @app.route('/restricted')
    @login_required
    def restricted():
        return 'restricted'
    
    log.info('Getting login URL')
    res1 = client.get('/redir')
    log.info('Checking redirect of restricted view')
    res2 = client.get('/restricted')
    assert res2.location.startswith(res1.location + '?')

