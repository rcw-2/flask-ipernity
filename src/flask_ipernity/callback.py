"""Auth Blueprint"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from flask import Blueprint, Response, redirect, session

from .ext import ipernity


log = getLogger(__name__)

callback = Blueprint('flask_ipernity_callback', __name__)


@callback.route('/')
def ipernity_callback() -> Response:
    log.debug('Ipernity callback called')
    ipernity.set_token()
    if ipernity.login:
        
        from .login import do_login
        do_login()
    next_url = session.pop('ipernity_next_url', '/')
    return redirect(next_url)


