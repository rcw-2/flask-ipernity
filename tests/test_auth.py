"""
Tests cache functionality
"""

from __future__ import annotations

from logging import getLogger
from time import sleep
from typing import TYPE_CHECKING

from flask import Flask, jsonify
import pytest

from flask_ipernity import Ipernity, ipernity_auth_required, ipernity

if TYPE_CHECKING:
    from flask.testing import FlaskClient


log = getLogger(__name__)


@pytest.fixture
def app(base_app):
    app = base_app
    Ipernity(app)
    
    @app.route('/user')
    @ipernity_auth_required()
    def user():
        return jsonify(ipernity.api.user.get())
    
    @app.route('/albums')
    @ipernity_auth_required({'doc': 'read'})
    def albums():
        return jsonify(ipernity.api.albums.getList())
    
    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


def test_auth_required(client, browser, test_config):
    res = client.get('/user')
    assert res.location
    frob = browser.authorize(res.location)
    assert frob
    res = client.get('/ipernity/cb', query_string = {'frob': frob})
    assert res.location.endswith('/user')
    res = client.get('/user')
    assert res.json['user']['username'] == test_config['ipernity']['username']
    res = client.get('/get_perm')
    assert res.json['doc'] == 'none'
    res = client.get('/albums')
    assert res.location
    frob = browser.authorize(res.location)
    assert frob
    res = client.get('/ipernity/cb', query_string = {'frob': frob})
    assert res.location.endswith('/albums')
    res = client.get('/get_perm')
    assert res.json['doc'] == 'read'


