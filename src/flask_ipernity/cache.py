"""
This module provides cache functionality.
"""

from __future__ import annotations

from logging import getLogger
from time import time
from typing import Any, Dict, Mapping, TYPE_CHECKING

from ipernity import IpernityAPI

from .ext import ipernity

# if TYPE_CHECKING:


log = getLogger(__name__)


class CachedIpernityAPI(IpernityAPI):
    """
    Wrapper for :class:`~ipernity.IpernityAPI` that caches requests
    in the Flask :class:`~flask.session`.
    
    Args:
        timeout:    Time in seconds that cached results are considered valid.
        args:       Passed to :class:`~ipernity.api.IpernityAPI`.
        kwargs:     Passed to :class:`~ipernity.api.IpernityAPI`.
    """
    
    def __init__(
        self,
        timeout: int = 300,
        *args: Any,
        **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.timeout = timeout
    
    
    @property
    def cache(self) -> Dict:
        """
        Dict for storing the cache.
        
        This gives you direct access to the :class:`~flask.session` variable
        containing the cached data. When modifying the dict, make sure to set
        :attr:`~flask.session.modified` so that the changes will be saved.
        """
        cache = ipernity.session_get('cache', None)
        if cache is None:
            log.debug('Initializing cache')
            ipernity.session_set('cache', {})
            cache = ipernity.session_get('cache', None)
        return cache
    
    
    def call(self, method_name: str, **kwargs: Any) -> Dict:
        """
        Makes an API call and caches the result.
        
        The results are stored in the :attr:`cache` property.
        """
        key = method_name + repr(self.token) + repr(kwargs)
        if key in self.cache:
            res, expire = self.cache[key]
            if time() < expire:
                log.debug(
                    '%s(%s): returning result from cache',
                    method_name,
                    kwargs
                )
                ipernity.session_set(
                    'returns_from_cache',
                    ipernity.session_get('returns_from_cache', 0) + 1
                )
                return res
        
        res = super().call(method_name, **kwargs)
        
        # This will also set session.modified
        ipernity.session_set(
            'api_calls',
            ipernity.session_get('api_calls', 0) + 1
        )
        
        self.cache[key] = (res, time() + self.timeout)
        return res


