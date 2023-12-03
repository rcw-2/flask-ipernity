
from logging import getLogger

import pytest


log = getLogger(__name__)


def test_login_logout(browser, client, test_config):
    res = client.get('/flask_ipernity_login/login')
    frob = browser.authorize(res.location)
    assert frob
    log.info('Calling callback with frob %s', frob)
    res = client.get('/flask_ipernity_callback/', query_string = {'frob': frob})
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
    res = client.get('flask_ipernity_login/logout')
    log.info('Got result %d: %s', res.status_code, res.headers.get('content-type'))
    with pytest.raises(KeyError):
        client.get('/get_token')


