

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
    a = base_app
    Ipernity(a)
    return a


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


def test_proxy_image(client):
    log.info('Checking image proxy')
    # Get a public photo by me
    res = client.get('/ipernity/doc/52222822/75x')
    assert res.content_type == 'image/jpeg'
    imgdata = res.data
    assert len(imgdata) == 1604


