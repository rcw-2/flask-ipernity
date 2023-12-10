"""
This test must be run before any other test that uses Flask-Login.
Be careful when renaming files.
"""

import sys
from logging import getLogger

from flask_ipernity import Ipernity, ipernity

log = getLogger(__name__)


def test_no_login_no_cache(base_app, browser, test_config):
    app = base_app
    Ipernity(app)
    
    @app.route('/login')
    def login():
        return ipernity.authorize({})
    
    client = app.test_client()
    res = client.get('/login')
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
    assert 'flask_login' not in sys.modules
    assert 'flask_ipernity.login' not in sys.modules
    assert 'flask_ipernity.cache' not in sys.modules




