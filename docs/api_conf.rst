Configuration Options
======================

The following options of the Flask configuration can be used to control
Flask-Ipernity's behavior:


.. data:: IPERNITY_APP_KEY
    
    The Ipernity Application key.

    Default: ``None``

.. data:: IPERNITY_APP_SECRET
    
    The Ipernity Application secret.

    Default: ``None``

.. data:: IPERNITY_CACHE_REQUESTS

    Boolean indicating if API requests are cached in the session. As this can
    require lots of session memory, you should use an enhanced session handler
    like `Flask-Session`_ if setting this to ``True``.

    Default: ``False``

.. data:: IPERNITY_CACHE_MAX_AGE
    
    Maximum age for cached results to be used.

    Default: 300

.. data:: IPERNITY_CALLBACK

    Tells Flask-Ipernity if it should supply a view for the application's
    callback URL.

    Default: ``True``

.. data:: IPERNITY_CALLBACK_URL_PREFIX

    URL prefix for the callback blueprint.

    Default: ``"/ipernity"``

.. data:: IPERNITY_LOGIN

    Tells Flask-Ipernity if it should act as an identity provider for
    `Flask-Login`_.

    Default: ``False``

.. data:: IPERNITY_LOGIN_URL_PREFIX

    URL prefix for the login blueprint.

    Default: ``"/ipernity"``

.. data:: IPERNITY_PERMISSIONS

    Default permissions that are requested by :meth:`~Ipernity.authorize` if
    no permissions are specified. Should be a ``dict`` with the keys:

    .. code-block:: python

        IPERNITY_PERMISSIONS = {
            'doc'       'read',
            'blog':     'write',
            'post':     'delete',
            'network':  'write',
            'profile':  'read',
        }
    
    Missing keys indicate that no permissions are requested for this data.
    An empty ``dict`` means to login, but not request additional permissions.

    Default: ``{}``

    .. seealso::
        * `Ipernity permissions <http://www.ipernity.com/help/api/permissions.html>`_

.. data:: IPERNITY_SESSION_PREFIX

    Prefix for the Flask-Ipernity session variables.

    Default: ``"ipernity_"``

.. include:: links.inc

