"""
Tests cache functionality
"""

from time import sleep

from flask import jsonify
import pytest

from flask_ipernity import Ipernity, ipernity


@pytest.fixture
def cached_app(base_app):
    app = base_app
    app.config['IPERNITY_CACHE_REQUESTS'] = True
    
    Ipernity(app)
    
    @app.route('/cache')
    def cache():
        return jsonify({
            key: ipernity.session_get(key, 0)
            for key in ['api_calls', 'returns_from_cache']
        })
    
    @app.route('/explore')
    def explore():
        return jsonify(ipernity.api.explore.docs.getPopular())
    
    return app


def test_cache(cached_app):
    cached_app.config['IPERNITY_CACHE_MAX_AGE'] = 900
    client = cached_app.test_client()
    client.get('/explore')
    res = client.get('/cache')
    api_calls = res.json['api_calls']
    cached_calls = res.json['returns_from_cache']
    client.get('/explore')
    res = client.get('/cache')
    assert res.json['api_calls'] == api_calls
    assert res.json['returns_from_cache'] > cached_calls


def test_cache_expire(cached_app):
    cached_app.config['IPERNITY_CACHE_MAX_AGE'] = 1
    client = cached_app.test_client()
    client.get('/explore')
    res = client.get('/cache')
    api_calls = res.json['api_calls']
    cached_calls = res.json['returns_from_cache']
    sleep(1)
    client.get('/explore')
    res = client.get('/cache')
    assert res.json['api_calls'] > api_calls
    assert res.json['returns_from_cache'] == cached_calls


