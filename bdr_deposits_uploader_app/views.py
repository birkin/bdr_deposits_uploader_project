import datetime
import json
import logging

import trio
from django.conf import settings as project_settings
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from bdr_deposits_uploader_app.lib import config_new_helper, version_helper
from bdr_deposits_uploader_app.lib.shib_handler import shib_decorator
from bdr_deposits_uploader_app.lib.version_helper import GatherCommitAndBranchData

log = logging.getLogger(__name__)


# -------------------------------------------------------------------
# main urls
# -------------------------------------------------------------------


def info(request):
    """
    The "about" view.
    Can get here from 'info' url, and the root-url redirects here.
    """
    log.debug('starting info()')
    ## prep data ----------------------------------------------------
    # context = { 'message': 'Hello, world.' }
    context = {
        'quote': 'The best life is the one in which the creative impulses play the largest part and the possessive impulses the smallest.',
        'author': 'Bertrand Russell',
    }
    ## prep response ------------------------------------------------
    if request.GET.get('format', '') == 'json':
        log.debug('building json response')
        resp = HttpResponse(
            json.dumps(context, sort_keys=True, indent=2),
            content_type='application/json; charset=utf-8',
        )
    else:
        log.debug('building template response')
        resp = render(request, 'info.html', context)
    return resp


@shib_decorator
def config_new(request):
    """
    Enables coniguration of new app.
    """
    log.debug('starting config_new()')

    if not request.user.userprofile.can_create_app:
        return HttpResponse('You do not have permissions to create an app.')
    dummy_data: list = config_new_helper.get_recent_configs()
    context = {'recent_apps': dummy_data}
    return render(request, 'config_new.html', context)


@shib_decorator
def config_slug(request, slug):
    """
    Enables coniguration of existing app.
    """
    log.debug('starting config_slug()')
    log.debug(f'slug, ``{slug}``')

    if slug not in request.user.userprofile.can_configure_these_apps:
        return HttpResponse('You do not have permissions to configure this app.')

    # context = { 'slug': slug }
    return HttpResponse(f'config_slug view for slug: {slug}')
    # return render(request, 'config_slug.html', context)


@shib_decorator
def upload_slug(request, slug):
    """
    Displays the upload app.
    """
    log.debug('starting upload_slug()')
    log.debug(f'slug, ``{slug}``')

    if slug not in request.user.userprofile.can_view_these_apps:
        return HttpResponse('You do not have permissions to view this app.')

    # context = { 'slug': slug }
    return HttpResponse(f'upload_slug view for slug: {slug}')
    # return render(request, 'config_slug.html', context)


# -------------------------------------------------------------------
# support urls
# -------------------------------------------------------------------


def error_check(request):
    """
    Offers an easy way to check that admins receive error-emails (in development).
    To view error-emails in runserver-development:
    - run, in another terminal window: `python -m smtpd -n -c DebuggingServer localhost:1026`,
    - (or substitue your own settings for localhost:1026)
    """
    log.debug('starting error_check()')
    log.debug(f'project_settings.DEBUG, ``{project_settings.DEBUG}``')
    if project_settings.DEBUG is True:  # localdev and dev-server; never production
        log.debug('triggering exception')
        raise Exception('Raising intentional exception to check email-admins-on-error functionality.')
    else:
        log.debug('returning 404')
        return HttpResponseNotFound('<div>404 / Not Found</div>')


def version(request):
    """
    Returns basic branch and commit data.
    """
    log.debug('starting version()')
    rq_now = datetime.datetime.now()
    gatherer = GatherCommitAndBranchData()
    trio.run(gatherer.manage_git_calls)
    info_txt = f'{gatherer.branch} {gatherer.commit}'
    context = version_helper.make_context(request, rq_now, info_txt)
    output = json.dumps(context, sort_keys=True, indent=2)
    log.debug(f'output, ``{output}``')
    return HttpResponse(output, content_type='application/json; charset=utf-8')


def root(request):
    return HttpResponseRedirect(reverse('info_url'))
