Getting Started
================


Installation
-------------

.. code-block:: console

    $ pip install Flask-Ipernity


Ipernity Application Key
-------------------------

To use Flask-Ipernity, you need to create an
`Ipernity API key <http://www.ipernity.com/apps/key>`_.

*   Under "Authentication method", choose "Web"
*   Enter a callback URL. If you use Flask-Ipernity's built-in callback, the
    URL is `http[s]://your.server.name/ipernity/cb`. Don't worry,
    you can change this value later if needed.
*   Save the application key and secret to the Flask configuration in the
    :data:`IPERNITY_APP_KEY` and :data:`IPERNITY_APP_SECRET` keys.


Ipernity Authentication/Authorization
--------------------------------------

Many Ipernity API calls require authentication/authorization. This can be done
in two steps:

1.  The :meth:`~Ipernity.authorize` method returns a redirect to Ipernity's
    authentication page.

2.  After authorization, the Browser is redirected to the application's
    callback URL (see above). By default, Flask-Ipernity adds a
    :class:`~flask.Blueprint` with a callback view that gets an access token
    and stores it in the application's :class:`~flask.session`.
    If you set :data:`IPERNITY_CALLBACK` = ``False``, you can define your own
    callback.

Flask-Ipernity provides a :class:`LocalProxy` variable
:data:`~flask_ipernity.ipernity` that contains the current application's
:class:`~flask_ipernity.Ipernity` object. API methods can be accessed with
the :attr:`~flask_ipernity.Ipernity.api` property.

Example:

.. code-block:: python

    from flask import Flask
    from flask_ipernity import Ipernity, ipernity, ipernity_auth_required

    app = Flask(__name__)
    app.config.update(
        IPERNITY_APP_KEY = 'XXX',
        IPERNITY_APP_SECRET = 'YYY'
        IPERNITY_PERMISSIONS = {'doc': 'read'}
    )
    Ipernity(app)
    
    @app.route('/get_doc')
    @ipernity_auth_required()   # You can also specify permissions here
    def get_doc():
        data = ipernity.api.docs.getList()
        ...


.. seealso::
    * :class:`~flask_ipernity.Ipernity` class
    * :data:`~flask_ipernity.ipernity` variable
    * :func:`~flask_ipernity.ipernity_auth_required` decorator


Proxying Ipernity documents
-----------------------------

Flask-Ipernity can proxy requests to Ipernity documents if
:data:`IPERNITY_PROXY_DOCS` is ``True`` (which is the default). This enables
a blueprint that can be accessed with with something like

.. code-block:: html

    <img src="{{url_for('ip_proxy.doc', doc_id=4711, label='1600')}}">

``label`` is the one of the sizes Ipernity provides, or ``'original'`` for the
original file.


.. _flask-login-integration:

Using Flask-Ipernity with Flask-Login
--------------------------------------

With Flask-Ipernity, you can use Ipernity as an identity provider for
`Flask-Login`_. Flaks-Ipernity then provides a blueprint with views for login
and logout and handles login via Ipernity authentication. To activate this
behavior, set the :data:`IPERNITY_LOGIN` configuration to ``True``.

.. note::
    When using ``IPERNITY_LOGIN=True``, be sure to call
    :meth:`flask_login.LoginManager.init_app` before
    :meth:`flask_ipernity.Ipernity.init_app`!

Views marked with :func:`~flask_login.login_required` will then trigger
Ipernity authentication. Additionally using
:func:`~flask_ipernity.ipernity_auth_required` is not necessary and may
lead to strange behavior.

.. code-block:: python

    from flask import Flask
    from flask_ipernity import Ipernity, ipernity
    from flask_login import LoginManager, login_required

    app = Flask(__name__)
    app.config.update(
        IPERNITY_APP_KEY = 'XXX',
        IPERNITY_APP_SECRET = 'YYY'
        IPERNITY_LOGIN = True,
        IPERNITY_PERMISSIONS = {'doc': 'read'}
    )
    LoginManager(app)
    Ipernity(app)
    
    @app.route('/get_doc')
    @login_required
    def get_doc():
        data = ipernity.api.docs.getList()
        ...


Caching Ipernity Requests
----------------------------

To avoid repeated requests in a short time, the results can be cached in the
Flask :class:`~flask.session`. To enable caching, set the configuration option
:data:`IPERNITY_CACHE_REQUESTS` to ``True``. To control the cache lifetime,
set :data:`IPERNITY_CACHE_MAX_AGE` to the number of seconds you want to keep
the results. The default is 300s.

.. note::
    Flask's default session handler only has a limited amount of memory which
    can easyly get exhausted when using caching. To avoid overflows, you can
    use an advanced session handler like `Flask-Session`_.


.. include:: links.inc

