"""Auth Blueprint"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from flask import Blueprint, Response, redirect, current_app

from .ext import ipernity


log = getLogger(__name__)

callback = Blueprint('ip_callback', __name__)


@callback.route('/cb')
def ipernity_callback() -> Response:
    log.debug('Ipernity callback called')
    ipernity.set_token()
    if current_app.config['IPERNITY_LOGIN']:
        from .login import do_login
        do_login()
    next_url = ipernity.session_pop('next_url', '/')
    return redirect(next_url)


