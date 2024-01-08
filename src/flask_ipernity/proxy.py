"""Proxy Blueprint"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import requests
from flask import Blueprint, Response, abort, stream_with_context
from ipernity import APIRequestError

from .ext import ipernity


log = getLogger(__name__)

proxy = Blueprint('ip_proxy', __name__)


@proxy.route('/doc/<doc_id>/<label>')
def doc(doc_id: str, label: str) -> Response:
    """
    Loads and serves documents from Ipernity.
    """
    log.debug('Proxying doc %s size %s', doc_id, label)
    try:
        d = ipernity.api.doc.getMedias(doc_id = doc_id)
    except APIRequestError as e:
        if e.code == 1:
            abort(404, 'Document not found.')
        else:
            abort(502, e.message)
    
    if (label == 'original'):
        if 'original' not in d:
            abort(404, 'Media not found')
        url = d['original']['url']
        filename = d['original']['filename']
    else:
        for thumb in d['thumbs']['thumb']:
            if thumb['label'] == label:
                url = thumb['url']
                filename = f"{doc_id}.{label}{thumb['ext']}"
                break
        else:
            abort(404, 'Media not found.')

    res = requests.get(url, stream = True)
    return Response(
        stream_with_context(res.iter_content(None)),
        content_type = res.headers['content-type'],
        headers = [('content-disposition', f'inline; filename = {filename}')]
    )


