import copy
import logging
import pprint
from functools import wraps

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.http import HttpResponseServerError

log = logging.getLogger(__name__)


def shib_decorator(func):
    """
    Decorator for views that require Shibboleth authentication.
    Flow:
    - If user is already authenticated, the view is called as normal.
    - If user is not authenticated, attempts to provision a new user based on Shibboleth metadata.
    - If user creation fails, redirects to login page.
    - If user is successfully provisioned, logs user in and calls view.
    Called by views.abc()
    """

    @wraps(func)  # all this does is preserves function metadata
    def wrapper(request, *args, **kwargs):
        log.debug('starting shib_decorator wrapper()')
        log.debug(f'type(func), ``{type(func)}``')
        if request.user.is_authenticated:
            log.debug('user already authenticated.')
            return func(request, *args, **kwargs)

        shib_metadata: dict = prep_shib_meta(request.META, request.get_host())
        user = provision_user(shib_metadata)
        if not user:
            log.error('User creation failed; raising Exception.')
            return HttpResponseServerError('Sorry, problem with authentication; ask developers to check the logs.')

        auth.login(request, user)
        log.info(f'user {user.username} logged in.')
        return func(request, *args, **kwargs)

    return wrapper


def prep_shib_meta(shib_metadata: dict, host: str) -> dict:
    """
    Extracts Shib metadata from WSGI environ.
    Returns extracted metadata as a dictionary.
    Called by shib_login().
    """
    log.debug('starting prep_shib_meta()')
    log.debug(f'request.META: ``{pprint.pformat(shib_metadata)}``')

    if host in ['127.0.0.1', '127.0.0.1:8000', 'testserver']:
        new_dct = settings.TEST_SHIB_META_DCT
    else:
        new_dct: dict = copy.copy(shib_metadata)
        for key, val in shib_metadata.items():  # get rid of some dictionary items not serializable
            if 'passenger' in key:
                new_dct.pop(key)
            elif 'wsgi.' in key:
                new_dct.pop(key)

    log.debug(f'returning new_dct, ``{pprint.pformat(new_dct)}``')
    return new_dct


def provision_user(shib_metadata: dict) -> User | None:
    """
    Creates or updates User object based on Shibboleth metadata.
    Returns User object or None
    Called by shib_login().
    """
    log.debug('starting provision_user()')
    log.debug(f'initial shib_metadata, ``{pprint.pformat(shib_metadata)}``')

    username = shib_metadata.get('Shibboleth-eppn')
    if not username:
        return None
    defaults = {
        'email': shib_metadata.get('Shibboleth-mail', f'{username}@example.com'),
        'first_name': shib_metadata.get('Shibboleth-givenName', ''),
        'last_name': shib_metadata.get('Shibboleth-sn', ''),
    }
    user, created = User.objects.update_or_create(username=username, defaults=defaults)
    user.save()
    return user
