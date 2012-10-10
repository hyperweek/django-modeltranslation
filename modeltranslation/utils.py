# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import get_language as _get_language
from django.utils.functional import lazy


def get_language():
    """
    Return an active language code that is guaranteed to be in
    settings.LANGUAGES (Django does not seem to guarantee this for us).
    """
    lang = _get_language()
    LANGUAGE_CODES = [l[0] for l in settings.LANGUAGES]
    if lang not in LANGUAGE_CODES and '-' in lang:
        lang = lang.split('-')[0]
    if lang in LANGUAGE_CODES:
        return lang
    return settings.LANGUAGE_CODE


def get_translation_fields(field):
    """Returns a list of localized fieldnames for a given field."""
    return [build_localized_fieldname(field, l[0]) for l in settings.LANGUAGES]


def build_localized_fieldname(field_name, lang):
    return str('%s_%s' % (field_name, lang.replace('-', '_')))


def _build_localized_verbose_name(verbose_name, lang):
    return u'%s [%s]' % (verbose_name, lang)
build_localized_verbose_name = lazy(_build_localized_verbose_name, unicode)
