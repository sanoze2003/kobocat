# coding: utf-8
from functools import wraps
from urllib.parse import urlparse

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.decorators import available_attrs
from django.conf import settings
from django.http import HttpResponseRedirect

from onadata.apps.logger.models import XForm


def check_obj(f):
    @wraps(f)
    def with_check_obj(*args, **kwargs):
        if args[0]:
            return f(*args, **kwargs)

    return with_check_obj


def is_owner(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
        # assume username is first arg
        if request.user.is_authenticated:
            if request.user.username == kwargs['username']:
                return view_func(request, *args, **kwargs)
            protocol = "https" if request.is_secure() else "http"
            return HttpResponseRedirect(f'{protocol}://{request.get_host()}')
        path = request.build_absolute_uri()
        login_url = request.build_absolute_uri(settings.LOGIN_URL)
        # If the login url is the same scheme and net location then just
        # use the path as the "next" url.
        login_scheme, login_netloc = urlparse(login_url)[:2]
        current_scheme, current_netloc = urlparse(path)[:2]
        if ((not login_scheme or login_scheme == current_scheme) and
                (not login_netloc or login_netloc == current_netloc)):
            path = request.get_full_path()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path, None, REDIRECT_FIELD_NAME)
    return _wrapped_view


def apply_form_field_names(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        def _get_decoded_record(record):
            if isinstance(record, dict):
                # Avoid RuntimeError: dictionary keys changed during iteration
                record_iter = dict(record)
                for field in record_iter:
                    if isinstance(record[field], list):
                        tmp_items = []
                        items = record[field]
                        for item in items:
                            tmp_items.append(_get_decoded_record(item))
                        record[field] = tmp_items
                    if field not in field_names.values() and \
                            field in field_names.keys():
                        record[field_names[field]] = record.pop(field)
            return record

        cursor = func(*args, **kwargs)
        # Compare by class name instead of type because tests use MockMongo
        if cursor.__class__.__name__ == 'Cursor' and 'id_string' in kwargs and \
                'username' in kwargs:
            username = kwargs.get('username')
            id_string = kwargs.get('id_string')
            dd = XForm.objects.get(
                id_string=id_string, user__username=username)
            records = []
            field_names = dd.data_dictionary().get_mongo_field_names_dict()
            for record in cursor:
                records.append(_get_decoded_record(record))
            return records
        return cursor
    return wrapper
