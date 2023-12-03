
from __future__ import annotations

import os
from html.parser import HTMLParser
from logging import getLogger
from urllib.parse import parse_qs, urlparse
from typing import Dict, Mapping, TYPE_CHECKING

import pytest
import requests
import yaml
from flask import Flask, jsonify, session
from flask_ipernity import Ipernity

if TYPE_CHECKING:
    from flask.testing import FlaskClient


log = getLogger(__name__)


@pytest.fixture(scope='session')
def test_config() -> Dict:
    cfgfile = os.path.join(os.path.dirname(__file__), '.test-config.yaml')
    with open(cfgfile, 'r') as cfg:
        return yaml.load(cfg, Loader=yaml.SafeLoader)


@pytest.fixture
def base_app(test_config: Mapping) -> Flask:
    a = Flask(__name__)
    a.config.from_mapping(test_config['flask'])
    a.testing = True
    
    @a.route('/get_token')
    def get_token():
        log.debug('Returning Ipernity token')
        return jsonify(session['ipernity_token'])
    
    return a


@pytest.fixture
def app(base_app: Flask) -> Flask:
    from flask_login import LoginManager
    a = base_app
    a.config['IPERNITY_CALLBACK'] = True
    login = LoginManager(a)
    Ipernity(a, login)
    
    return a


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def browser(test_config: Mapping) -> IpernitySession:
    session = IpernitySession()
    for domain, paths in test_config['ipernity']['cookies'].items():
        for path, cookies in paths.items():
            for name, value in cookies.items():
                session.cookies.set(name, value, domain=domain, path=path)
    return session


class IpernitySession(requests.Session):
    def authorize(self, auth_url: str) -> str:
        log.info('Authorizing via %s', auth_url)
        res = self.get(auth_url, allow_redirects=False)
        mimetype = res.headers.get('Content-Type')
        log.info('Got result %d: %s', res.status_code, mimetype)
        
        if res.status_code == 200 and mimetype.startswith('text/html'):
            log.debug('Text: %s', res.text)
            html = IpernityParser()
            html.feed(res.text)
            url = urlparse(auth_url)
            params = parse_qs(url.query)
            #html.params.update({
            #    # 'app[api_key]': params['api_key'],
            #    'app[api_sig]': params['api_sig'],
            #})
            log.info('Posting authorization %s', html.params)
            res = self.request(
                html.method,
                auth_url,
                data = html.params,
                allow_redirects = False
            )
            mimetype = res.headers.get('Content-Type')
            log.info('Got result %d: %s', res.status_code, mimetype)
        
        if res.status_code == 302:
            url = res.headers.get('location')
            log.info('Got redirect to %s', url)
            if url.startswith('http://127.0.0.1'):
                frob = parse_qs(urlparse(url).query)['frob'][0]
                log.info('Returning frob %s', frob)
                return frob
        
        if mimetype.startswith('text/html'):
            log.debug('Text: %s', res.text)
        
        log.error('No frob')
        return None


class IpernityParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parsing_form = False
        self.params = {}
    
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag == 'form':
            if self.get_attr(attrs, 'name') == 'fa':
                self.method = self.get_attr(attrs, 'method')
                self.parsing_form = True
        
        elif (
            self.parsing_form and
            tag == 'input' and
            self.get_attr(attrs, 'type') == 'hidden'
        ):
            self.params[self.get_attr(attrs, 'name')] = self.get_attr(attrs, 'value')
    
    def handle_endtag(self, tag: str):
        if tag == 'form' and self.parsing_form:
            self.parsing_form = False
    
    @staticmethod
    def get_attr(attrs: list, key: str) -> str|None:
        for k, v in attrs:
            if k == key:
                return v
        return None


