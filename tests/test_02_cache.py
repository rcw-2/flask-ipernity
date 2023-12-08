"""
Tests cache functionality
"""

from flask import jsonify

from flask_ipernity import Ipernity, ipernity


def test_cache(base_app):
    app = base_app
    app.config['IPERNITY_CACHE_REQUESTS'] = True
    app.config['IPERNITY_CACHE_MAX_AGE'] = 900
    
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
    
    client = app.test_client()
    client.get('/explore')
    res = client.get('/cache')
    api_calls = res.json['api_calls']
    cached_calls = res.json['returns_from_cache']
    client.get('/explore')
    res = client.get('/cache')
    assert res.json['api_calls'] == api_calls
    assert res.json['returns_from_cache'] > cached_calls


