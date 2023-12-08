"""
"""

from __future__ import annotations

from logging import getLogger
from time import time
from typing import Any, Dict, Mapping, TYPE_CHECKING

from flask import current_app, session
from ipernity import IpernityAPI

if TYPE_CHECKING:
    from .ext import Ipernity


log = getLogger(__name__)


class CachedIpernityAPI(IpernityAPI):
    
    def __init__(
        self,
        timeout: int = 300,
        *args: Any,
        **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
    
    
    @property
    def cache(self) -> Dict:
        key = current_app.config['IPERNITY_SESSION_PREFIX'] + 'cache'
        if key not in session:
            session[key] = {}
        return session[key]
    
    
    def call(self, method_name: str, **kwargs: Any) -> Mapping:
        key = method_name + repr(self.token) + repr(kwargs)
        if key in self.cache:
            res, expire = self.cache[key]
            if time() < expire:
                log.debug(
                    '%s(%s): returning result from cache',
                    method_name,
                    kwargs
                )
                return res
        
        res = super().call(method_name, **kwargs)
        
        self.cache[key] = (res, time() + 300)
        return res


